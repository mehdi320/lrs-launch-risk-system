"""Onglet Streamlit du module Creative Studio.

Cette fonction est appelée depuis app.py — c'est la seule couche du module
couplée à Streamlit. Elle n'importe jamais app.py (pour éviter un import
circulaire, app.py important ce module) : les fonctionnalités LRS
existantes qu'on veut réutiliser (audit LRS, corrélation ads) sont reçues
en callbacks optionnels, injectés par app.py au moment de l'appel.
"""

from __future__ import annotations

from typing import Callable, Optional

import streamlit as st

from datetime import datetime, timedelta, timezone

from creative_studio.core.budget_guard import DEFAULT_KILL_EXPOSURE_THRESHOLD
from creative_studio.core.copy_generation import (
    KIND_LABELS,
    GenerationRefused,
    generate_variants,
    generate_variants_from_reference,
)
from creative_studio.core.email_sequences import generate_email_sequence
from creative_studio.core.funnel_builder import FUNNEL_OBJECTIVE_LABELS, FUNNEL_STEP_TEMPLATES, generate_funnel
from creative_studio.core.funnel_elements import (
    ELEMENT_TYPE_LABELS,
    ElementType,
    render_element_text,
)
from creative_studio.core.pdf_export import build_funnel_pdf_filename, build_pdf_filename, generate_funnel_pdf, generate_variant_pdf
from creative_studio.core.prioritization import rank_variants_for_budget
from creative_studio.core.reference_extraction import (
    VARY_DIMENSION_LABELS,
    analyze_existing_copy,
    analyze_existing_copy_pdf_bytes,
)
from creative_studio.core.stats import VariantStats
from creative_studio.core.test_evaluation import compute_and_save_results
from creative_studio.core.variants import (
    ABTest,
    ConclusionReason,
    Framework,
    FunnelObjective,
    FunnelStep,
    FunnelStepElement,
    FunnelStepMedia,
    GenerationMode,
    MediaPlacement,
    MediaSourceType,
    MediaType,
    Product,
    VariantKind,
    VariantStatus,
    VaryDimension,
)
from creative_studio.storage.db import init_db
from creative_studio.storage.media import save_uploaded_media
from creative_studio.storage.repository import (
    ABTestRepository,
    EmailSequenceRepository,
    EventRepository,
    FunnelRepository,
    FunnelStepElementRepository,
    FunnelStepMediaRepository,
    ProductRepository,
    TestResultRepository,
    VariantRepository,
)

_SERVING_BASE_URL_DEFAULT = "http://localhost:8000"

_products = ProductRepository()
_variants = VariantRepository()
_test_results = TestResultRepository()
_tests = ABTestRepository()
_events = EventRepository()
_sequences = EmailSequenceRepository()
_funnels = FunnelRepository()
_funnel_media = FunnelStepMediaRepository()
_funnel_elements = FunnelStepElementRepository()


def render_creative_studio(
    run_lrs_audit_fn: Optional[Callable[[str], int]] = None,
) -> None:
    """Rend l'onglet Creative Studio.

    `run_lrs_audit_fn` (optionnel) : callback fourni par app.py qui prend le
    texte de la page de vente d'une variante et retourne un score LRS /20
    (typiquement un wrapper autour de run_audit_stream en mode Funnel Only).
    Si absent, le bouton "Auditer avec LRS" n'est pas proposé.
    """
    init_db()
    st.markdown("### 🎨 Creative Studio")
    st.caption(
        "Génération de créatifs, test A/B automatisé et séquences email — mode local. "
        "Le service de diffusion des pages tourne séparément "
        "(`uvicorn creative_studio.serving.app:app`)."
    )

    sub_products, sub_variants, sub_tests, sub_emails = st.tabs(
        ["📦 Produits", "✍️ Variantes", "🧪 Tests A/B", "✉️ Séquences email"]
    )

    with sub_products:
        _render_products_tab()

    with sub_variants:
        _render_variants_tab(run_lrs_audit_fn=run_lrs_audit_fn)

    with sub_tests:
        _render_tests_tab()

    with sub_emails:
        _render_emails_tab()


def _selected_product(key_suffix: str) -> Product | None:
    """`key_suffix` doit être unique par onglet appelant : Streamlit rend le
    corps de tous les onglets à chaque exécution du script (pas seulement
    celui affiché), donc réutiliser la même clé de widget dans plusieurs
    onglets lève une StreamlitDuplicateElementKey.
    """
    products = _products.list()
    if not products:
        st.info("Crée d'abord un produit dans l'onglet 📦 Produits.")
        return None
    labels = {f"{p.name} ({p.price_cents / 100:.2f} {p.currency})": p for p in products}
    label = st.selectbox("Produit", list(labels.keys()), key=f"cs_selected_product_{key_suffix}")
    return labels[label]


def _render_products_tab() -> None:
    with st.form("cs_new_product"):
        st.markdown("#### Nouveau produit")
        name = st.text_input("Nom du produit")
        description = st.text_area("Description courte", height=80)
        col1, col2 = st.columns(2)
        with col1:
            price = st.number_input("Prix", min_value=0.0, step=1.0, format="%.2f")
        with col2:
            currency = st.selectbox("Devise", ["EUR", "USD", "GBP"])
        payment_link = st.text_input("Lien de paiement Stripe", placeholder="https://buy.stripe.com/...")
        audience = st.text_input("Cible / audience", placeholder="Ex: freelances 28-45 ans")
        submitted = st.form_submit_button("Créer le produit", type="primary")

    if submitted:
        if not (name and description and payment_link and audience):
            st.error("Tous les champs sont requis.")
        else:
            product = _products.create(
                Product(
                    name=name, description=description, price_cents=int(round(price * 100)),
                    currency=currency, stripe_payment_link=payment_link, audience=audience,
                )
            )
            st.success(f"Produit créé : {product.name}")
            st.rerun()

    st.markdown("#### Produits existants")
    for p in _products.list():
        with st.expander(f"{p.name} — {p.price_cents / 100:.2f} {p.currency}"):
            st.write(p.description)
            st.caption(f"Audience : {p.audience}")
            st.caption(f"Lien de paiement : {p.stripe_payment_link}")


def _render_variants_tab(run_lrs_audit_fn: Optional[Callable[[str], int]]) -> None:
    product = _selected_product("variants")
    if product is None:
        return

    mode_label = st.radio(
        "Mode de génération",
        ["🆕 Créer depuis zéro", "🔧 Optimiser un existant", "🧭 Funnel Builder"],
        horizontal=True,
        key="cs_generation_mode",
        help=(
            "Créer depuis zéro : input minimal (produit, description, prix, audience), "
            "aucun advertorial ou funnel existant requis. "
            "Optimiser un existant : pars d'une publicité ou page de vente déjà en ligne, "
            "et ne fais varier qu'un seul paramètre à la fois entre les variantes générées. "
            "Funnel Builder : génère la structure complète d'un funnel (capture/advertorial "
            "→ vente → confirmation/upsell) cohérente de bout en bout, plutôt qu'une page isolée."
        ),
    )
    st.divider()

    if mode_label == "🆕 Créer depuis zéro":
        _render_from_scratch_generation(product)
    elif mode_label == "🔧 Optimiser un existant":
        _render_optimize_existing_generation(product)
    else:
        _render_funnel_builder_generation(product)

    st.markdown("#### Variantes existantes")
    existing = _variants.list_by_product(product.id)
    if not existing:
        st.caption("Aucune variante pour ce produit pour l'instant.")
        return

    for v in existing:
        if v.source_mode == GenerationMode.OPTIMIZE_EXISTING:
            dim_label = VARY_DIMENSION_LABELS.get(v.varied_dimension.value) if v.varied_dimension else None
            mode_badge = f" · 🔧 optimisée ({dim_label})" if dim_label else " · 🔧 optimisée"
        elif v.source_mode == GenerationMode.FUNNEL_BUILDER:
            mode_badge = " · 🧭 funnel builder"
        else:
            mode_badge = " · 🆕 depuis zéro"
        with st.expander(f"[{v.framework.value}] {v.copy.headline} — statut: {v.status.value}{mode_badge}"):
            st.markdown(f"**Hook** : {v.copy.hook}")
            for section in v.copy.body_sections:
                st.write(section)
            st.markdown(f"**CTA** : {v.copy.cta}")
            score_col1, score_col2 = st.columns([1, 2])
            with score_col1:
                st.metric("Score LRS", v.lrs_score if v.lrs_score is not None else "—")
            with score_col2:
                if run_lrs_audit_fn is not None and st.button("Auditer avec LRS", key=f"audit_{v.id}"):
                    page_text = "\n\n".join([v.copy.headline, v.copy.hook, *v.copy.body_sections, v.copy.cta])
                    with st.spinner("Audit LRS en cours..."):
                        score = run_lrs_audit_fn(page_text)
                    _variants.update_lrs_score(v.id, score)
                    st.success(f"Score LRS : {score}/20")
                    st.rerun()


def _render_from_scratch_generation(product: Product) -> None:
    """Mode "Créer depuis zéro" — comportement historique du Creative Studio,
    inchangé : input minimal produit, aucune référence requise."""
    st.caption(
        "Génère des variantes uniquement à partir de la fiche produit ci-dessus "
        "(nom, description, prix, audience) — pas d'advertorial ni de funnel existant requis."
    )
    col1, col2 = st.columns(2)
    with col1:
        kind = st.selectbox(
            "Type de créatif",
            [VariantKind.SALES_PAGE, VariantKind.ADVERTORIAL],
            format_func=lambda k: "Page de vente" if k == VariantKind.SALES_PAGE else "Advertorial",
            key="cs_scratch_kind",
        )
    with col2:
        frameworks = st.multiselect(
            "Frameworks",
            [Framework.AIDA, Framework.PAS, Framework.HORMOZI],
            default=[Framework.AIDA, Framework.PAS, Framework.HORMOZI],
            format_func=lambda f: f.value,
            key="cs_scratch_frameworks",
        )

    if st.button("🪄 Générer les variantes avec Claude", type="primary", disabled=not frameworks, key="cs_scratch_generate"):
        try:
            with st.spinner(f"Génération de {len(frameworks)} variante(s)..."):
                new_variants = generate_variants(product, kind, frameworks)
                for v in new_variants:
                    _variants.create(v)
            st.success(f"{len(new_variants)} variante(s) générée(s).")
            st.rerun()
        except GenerationRefused as exc:
            st.error(str(exc))
        except RuntimeError as exc:
            st.error(f"Impossible de générer : {exc}")


def _render_optimize_existing_generation(product: Product) -> None:
    """Mode "Optimiser un existant" — analyse un advertorial/page de vente
    déjà en ligne puis génère des variantes à un seul paramètre variable,
    en réutilisant le même moteur de génération (copy_generation.py) et le
    même pipeline de test A/B que le mode "Créer depuis zéro"."""
    st.caption(
        "Colle le texte d'une publicité ou d'une page de vente déjà existante (ou son URL). "
        "Claude en extrait l'angle et le framework, puis génère une variante par paramètre "
        "coché ci-dessous — en gardant tout le reste identique, pour isoler ce qui améliore "
        "la conversion."
    )
    reference_input = st.text_area(
        "Advertorial / page de vente existante (texte collé ou URL)",
        height=140,
        placeholder="Colle ici le texte de la pub, ou https://...",
        key="cs_reference_input",
    )
    col1, col2 = st.columns(2)
    with col1:
        kind = st.selectbox(
            "Type de créatif",
            [VariantKind.SALES_PAGE, VariantKind.ADVERTORIAL],
            format_func=lambda k: "Page de vente" if k == VariantKind.SALES_PAGE else "Advertorial",
            key="cs_optimize_kind",
        )
    with col2:
        dimensions = st.multiselect(
            "Paramètres à faire varier (une variante par paramètre)",
            [VaryDimension.HOOK, VaryDimension.SOCIAL_PROOF, VaryDimension.URGENCY, VaryDimension.CTA],
            default=[VaryDimension.HOOK, VaryDimension.SOCIAL_PROOF, VaryDimension.URGENCY, VaryDimension.CTA],
            format_func=lambda d: VARY_DIMENSION_LABELS[d.value],
            key="cs_optimize_dimensions",
        )

    if st.button(
        "🔍 Analyser puis générer les variantes",
        type="primary",
        disabled=not (reference_input.strip() and dimensions),
        key="cs_optimize_generate",
    ):
        try:
            with st.spinner("Analyse de la publicité existante..."):
                analysis = analyze_existing_copy(reference_input)
            st.info(
                f"**Framework détecté** : {analysis.detected_framework.value}"
                + (f" (hybride — {analysis.hybrid_notes})" if analysis.is_hybrid else "")
                + f"  \n**Angle** : {analysis.angle}"
            )
            with st.spinner(f"Génération de {len(dimensions)} variante(s)..."):
                new_variants = generate_variants_from_reference(product, kind, analysis, dimensions)
                for v in new_variants:
                    _variants.create(v)
            st.success(f"{len(new_variants)} variante(s) générée(s) à partir de l'existant.")
            st.rerun()
        except GenerationRefused as exc:
            st.error(str(exc))
        except (RuntimeError, ValueError) as exc:
            st.error(f"Impossible de générer : {exc}")


_MEDIA_PLACEMENT_LABELS = {
    MediaPlacement.HERO: "Héros (haut de page)",
    MediaPlacement.DEMO: "Démonstration produit",
    MediaPlacement.PROOF: "Preuve sociale",
}

_ELEMENT_TYPES_ORDERED = [ElementType.COUNTDOWN_TIMER, ElementType.LIMITED_DISCOUNT, ElementType.STOCK_COUNTER]


def _render_funnel_builder_generation(product: Product) -> None:
    """Mode "Funnel Builder" — génère la structure complète d'un funnel
    (capture/advertorial -> vente -> confirmation/upsell selon l'objectif)
    cohérente de bout en bout, en réutilisant le même moteur de génération
    (_call_claude_for_copy) et le même pipeline de test A/B que les deux
    autres modes : chaque page du funnel est un Variant standard, testable
    individuellement, seule leur appartenance au funnel est nouvelle."""
    st.caption(
        "Génère la structure complète d'un funnel plutôt qu'une page isolée : un brief "
        "d'angle/ton/promesse est généré en premier, puis chaque page est rédigée en "
        "cohérence avec ce brief. Chaque page individuelle reste testable en A/B "
        "séparément via le pipeline existant."
    )
    col1, col2 = st.columns(2)
    with col1:
        objective = st.selectbox(
            "Objectif de conversion",
            [FunnelObjective.DIRECT_SALE, FunnelObjective.EMAIL_CAPTURE, FunnelObjective.BOOKING],
            format_func=lambda o: FUNNEL_OBJECTIVE_LABELS[o],
            key="cs_funnel_objective",
        )
    with col2:
        framework = st.selectbox(
            "Framework",
            [Framework.AIDA, Framework.PAS, Framework.HORMOZI],
            format_func=lambda f: f.value,
            key="cs_funnel_framework",
            help="Ignoré si une base de référence est fournie ci-dessous : le framework "
                 "détecté dans la référence prime alors.",
        )

    steps_preview = " → ".join(KIND_LABELS[k] for k in FUNNEL_STEP_TEMPLATES[objective])
    st.caption(f"Structure générée pour cet objectif : {steps_preview}")

    st.markdown("##### Base de référence (optionnel)")
    st.caption(
        "Construis le funnel autour d'un advert/page déjà gagnant (ex : le PDF exporté "
        "depuis l'onglet 🧪 Tests A/B) plutôt que d'un angle inventé."
    )
    reference_mode = st.radio(
        "Référence",
        ["Aucune", "🔗 Lien (PDF, URL ou texte collé)", "📤 Uploader un PDF"],
        horizontal=True,
        key="cs_funnel_reference_mode",
    )
    reference_link = ""
    uploaded_pdf = None
    if reference_mode == "🔗 Lien (PDF, URL ou texte collé)":
        reference_link = st.text_input(
            "Lien PDF gagnant, URL de la page, ou texte collé",
            placeholder="https://... (lien PDF ou page web) ou texte collé",
            key="cs_funnel_reference_link",
        )
    elif reference_mode == "📤 Uploader un PDF":
        uploaded_pdf = st.file_uploader("PDF gagnant", type=["pdf"], key="cs_funnel_reference_upload")

    if st.button("🧭 Générer le funnel avec Claude", type="primary", key="cs_funnel_generate"):
        try:
            reference = None
            reference_label = None
            with st.spinner("Génération du funnel..."):
                if reference_mode == "🔗 Lien (PDF, URL ou texte collé)" and reference_link.strip():
                    reference = analyze_existing_copy(reference_link)
                    reference_label = reference_link.strip()
                elif reference_mode == "📤 Uploader un PDF" and uploaded_pdf is not None:
                    reference = analyze_existing_copy_pdf_bytes(uploaded_pdf.getvalue())
                    reference_label = f"Upload : {uploaded_pdf.name}"

                funnel, funnel_variants = generate_funnel(
                    product, objective, framework, reference=reference, reference_label=reference_label,
                )
                for v in funnel_variants:
                    _variants.create(v)
                steps = [
                    FunnelStep(funnel_id=funnel.id, variant_id=v.id, step_order=i)
                    for i, v in enumerate(funnel_variants, start=1)
                ]
                _funnels.create(funnel, steps)
            st.success(f"Funnel généré : {len(funnel_variants)} page(s), angle « {funnel.angle} ».")
            st.rerun()
        except GenerationRefused as exc:
            st.error(str(exc))
        except (RuntimeError, ValueError) as exc:
            st.error(f"Impossible de générer : {exc}")

    st.markdown("#### Funnels existants")
    funnels = _funnels.list_by_product(product.id)
    if not funnels:
        st.caption("Aucun funnel généré pour ce produit pour l'instant.")
        return

    for funnel in funnels:
        steps = _funnels.list_steps(funnel.id)
        step_variant_by_id = {s.id: _variants.get(s.variant_id) for s in steps}
        ref_badge = f" · 📎 base : {funnel.source_reference[:40]}" if funnel.source_reference else ""
        with st.expander(f"🧭 {FUNNEL_OBJECTIVE_LABELS[funnel.objective]} — {funnel.angle[:60]}{ref_badge}"):
            st.caption(f"Ton : {funnel.tone}  \nPromesse : {funnel.promise}")

            media_by_variant_id: dict[str, list[FunnelStepMedia]] = {}
            elements_by_variant_id: dict[str, list[FunnelStepElement]] = {}
            all_variants = []
            for i, step in enumerate(steps, start=1):
                variant = step_variant_by_id.get(step.id)
                if variant is None:
                    continue
                all_variants.append(variant)
                st.markdown(
                    f"**{i}. [{KIND_LABELS[variant.kind]}] {variant.copy.headline}** — statut : {variant.status.value}"
                )
                media_by_variant_id[variant.id] = _render_funnel_step_media(step)
                elements_by_variant_id[variant.id] = _render_funnel_step_elements(step)

            if all_variants:
                pdf_bytes = generate_funnel_pdf(
                    product, funnel, all_variants, media_by_variant_id, elements_by_variant_id
                )
                st.download_button(
                    "📄 Télécharger le funnel en PDF",
                    data=pdf_bytes,
                    file_name=build_funnel_pdf_filename(product, funnel),
                    mime="application/pdf",
                    key=f"funnel_pdf_{funnel.id}",
                )


def _render_funnel_step_media(step: FunnelStep) -> list[FunnelStepMedia]:
    """Gestion des médias (photos/vidéos) attachés à un maillon de funnel —
    le système ne les génère pas, il les intègre à l'emplacement choisi dans
    la page rendue/exportée. Retourne la liste à jour pour l'export PDF."""
    existing = _funnel_media.list_by_step(step.id)
    with st.container(border=True):
        st.caption("🖼️ Médias")
        if not existing:
            st.caption("Aucun média attaché.")
        for m in existing:
            icon = "🎥" if m.media_type == MediaType.VIDEO else "🖼️"
            col_a, col_b = st.columns([5, 1])
            col_a.caption(f"{icon} {_MEDIA_PLACEMENT_LABELS[m.placement]} — {m.location[:50]}")
            if col_b.button("🗑️", key=f"del_media_{m.id}"):
                _funnel_media.delete(m.id)
                st.rerun()

        with st.form(f"cs_add_media_{step.id}", clear_on_submit=True):
            media_kind = st.radio("Type", ["Image", "Vidéo"], horizontal=True, key=f"media_kind_{step.id}")
            placement = st.selectbox(
                "Emplacement",
                [MediaPlacement.HERO, MediaPlacement.DEMO, MediaPlacement.PROOF],
                format_func=lambda p: _MEDIA_PLACEMENT_LABELS[p],
                key=f"media_placement_{step.id}",
            )
            url_input = st.text_input("URL (laisser vide si upload)", key=f"media_url_{step.id}")
            upload_input = st.file_uploader(
                "Ou uploader un fichier",
                type=["jpg", "jpeg", "png", "gif", "webp", "mp4", "webm", "mov"],
                key=f"media_upload_{step.id}",
            )
            add_media_submitted = st.form_submit_button("Ajouter le média")

        if add_media_submitted:
            media_type = MediaType.VIDEO if media_kind == "Vidéo" else MediaType.IMAGE
            try:
                if upload_input is not None:
                    generated_name = save_uploaded_media(upload_input.name, upload_input.getvalue())
                    _funnel_media.create(
                        FunnelStepMedia(
                            step_id=step.id, media_type=media_type, source_type=MediaSourceType.UPLOAD,
                            location=generated_name, placement=placement,
                        )
                    )
                    st.rerun()
                elif url_input.strip():
                    _funnel_media.create(
                        FunnelStepMedia(
                            step_id=step.id, media_type=media_type, source_type=MediaSourceType.URL,
                            location=url_input.strip(), placement=placement,
                        )
                    )
                    st.rerun()
                else:
                    st.error("Fournis une URL ou un fichier à uploader.")
            except ValueError as exc:
                st.error(str(exc))

    return existing


def _render_funnel_step_elements(step: FunnelStep) -> list[FunnelStepElement]:
    """Gestion des éléments de conversion (timer, réduction limitée, stock)
    attachés à un maillon de funnel — ne passent jamais par la génération
    Claude, uniquement par la couche de rendu (core.funnel_elements).
    Retourne la liste à jour pour l'export PDF."""
    existing = _funnel_elements.list_by_step(step.id)
    with st.container(border=True):
        st.caption("⏱️ Éléments de conversion")
        if not existing:
            st.caption("Aucun élément attaché.")
        for el in existing:
            try:
                el_type = ElementType(el.element_type)
                label = ELEMENT_TYPE_LABELS[el_type]
            except ValueError:
                label = el.element_type
            text = render_element_text(el.element_type, el.config) or "(config invalide)"
            col_a, col_b, col_c = st.columns([4, 1, 1])
            col_a.caption(f"**{label}** — {text}")
            new_enabled = col_b.checkbox("Actif", value=el.enabled, key=f"toggle_elem_{el.id}")
            if new_enabled != el.enabled:
                _funnel_elements.set_enabled(el.id, new_enabled)
                st.rerun()
            if col_c.button("🗑️", key=f"del_elem_{el.id}"):
                _funnel_elements.delete(el.id)
                st.rerun()

        element_type = st.selectbox(
            "Type d'élément à ajouter",
            _ELEMENT_TYPES_ORDERED,
            format_func=lambda e: ELEMENT_TYPE_LABELS[e],
            key=f"new_elem_type_{step.id}",
        )
        with st.form(f"cs_add_element_{step.id}", clear_on_submit=True):
            config = _render_element_config_form(element_type, step.id)
            add_element_submitted = st.form_submit_button("Ajouter l'élément")

        if add_element_submitted:
            _funnel_elements.create(
                FunnelStepElement(step_id=step.id, element_type=element_type.value, config=config)
            )
            st.rerun()

    return existing


def _render_element_config_form(element_type: ElementType, step_id: str) -> dict:
    """Champs de config spécifiques à un type d'élément — utilisé pour
    initialiser le formulaire d'ajout. Étendre à un nouveau type = ajouter
    un cas ici + une config/renderer dans core.funnel_elements, jamais de
    migration de schéma (config stockée en JSON libre)."""
    default_deadline = datetime.now(timezone.utc) + timedelta(days=3)

    if element_type == ElementType.COUNTDOWN_TIMER:
        end_date = st.date_input("Date de fin", value=default_deadline.date(), key=f"cd_date_{step_id}")
        end_time = st.time_input("Heure de fin", value=default_deadline.time(), key=f"cd_time_{step_id}")
        label = st.text_input("Libellé", value="Offre expire dans", key=f"cd_label_{step_id}")
        return {"end_at": datetime.combine(end_date, end_time, tzinfo=timezone.utc).isoformat(), "label": label}

    if element_type == ElementType.LIMITED_DISCOUNT:
        col1, col2 = st.columns(2)
        with col1:
            original = st.number_input("Prix original", min_value=0.0, step=1.0, key=f"disc_orig_{step_id}")
        with col2:
            discounted = st.number_input("Prix réduit", min_value=0.0, step=1.0, key=f"disc_new_{step_id}")
        end_date = st.date_input("Expire le", value=default_deadline.date(), key=f"disc_date_{step_id}")
        end_time = st.time_input("À", value=default_deadline.time(), key=f"disc_time_{step_id}")
        return {
            "original_price_cents": int(round(original * 100)),
            "discounted_price_cents": int(round(discounted * 100)),
            "expires_at": datetime.combine(end_date, end_time, tzinfo=timezone.utc).isoformat(),
        }

    # STOCK_COUNTER — valeur toujours saisie manuellement, jamais générée/estimée.
    remaining = st.number_input("Places / stock restant", min_value=0, step=1, value=10, key=f"stock_rem_{step_id}")
    label = st.text_input("Libellé", value="places restantes", key=f"stock_label_{step_id}")
    return {"remaining": int(remaining), "label": label}


def _render_tests_tab() -> None:
    product = _selected_product("tests")
    if product is None:
        return

    variants = _variants.list_by_product(product.id)
    if len(variants) < 2:
        st.info("Il faut au moins 2 variantes générées pour lancer un test A/B.")
        return

    with st.form("cs_new_test"):
        st.markdown("#### Nouveau test A/B")
        test_name = st.text_input("Nom du test", placeholder="Ex: Headline AIDA vs PAS — semaine 1")
        labels = {f"[{v.framework.value}] {v.copy.headline}": v.id for v in variants}
        selected_labels = st.multiselect("Variantes à tester", list(labels.keys()))
        submitted = st.form_submit_button("Lancer le test", type="primary")

    if submitted:
        if not test_name or len(selected_labels) < 2:
            st.error("Nom du test + au moins 2 variantes requis.")
        else:
            variant_ids = [labels[label] for label in selected_labels]
            test = _tests.create(ABTest(product_id=product.id, name=test_name, variant_ids=variant_ids))
            for vid in variant_ids:
                _variants.update_status(vid, VariantStatus.TESTING)
            st.success(f"Test créé : {test.name}")
            st.rerun()

    st.markdown("#### Tests en cours")
    base_url = st.text_input(
        "URL du service de diffusion", value=_SERVING_BASE_URL_DEFAULT, key="cs_serving_base_url"
    )
    kill_exposure_threshold = st.number_input(
        "Seuil de coupe budget (expositions par variante à la traîne)",
        min_value=100, value=DEFAULT_KILL_EXPOSURE_THRESHOLD, step=100,
        help="Au-delà de ce nombre d'expositions, une variante qui n'a toujours pas dépassé "
             "la variante en tête est coupée automatiquement pour ne plus gaspiller de budget.",
        key="cs_kill_threshold",
    )
    variant_by_id = {v.id: v for v in variants}

    for test in _tests.list_by_product(product.id):
        with st.expander(f"🧪 {test.name} — {test.status.value}"):
            st.code(f"{base_url}/v/{test.id}", language=None)

            # Ne recalcule (et ne réécrit un instantané en base) que sur clic
            # explicite ou lors du tout premier affichage — sinon Streamlit
            # relancerait ce calcul à chaque interaction ailleurs dans l'appli
            # et ferait grossir test_results indéfiniment sans raison.
            if st.button("🔄 Recalculer les résultats", key=f"recompute_{test.id}"):
                results = compute_and_save_results(test.id, kill_exposure_threshold=kill_exposure_threshold)
            else:
                results = _test_results.latest_for_test(test.id)
                if not results:
                    results = compute_and_save_results(test.id, kill_exposure_threshold=kill_exposure_threshold)

            # Le calcul peut avoir conclu le test ou coupé des variantes —
            # on relit l'état à jour plutôt que la valeur capturée avant l'appel.
            test = _tests.get(test.id)

            if test.conclusion_reason == ConclusionReason.BUDGET_STOP_LOSS:
                st.warning("⛔ Test conclu par garde-fou budget — les autres variantes ont été coupées.")
            elif test.conclusion_reason == ConclusionReason.STATISTICAL_SIGNIFICANCE:
                st.success("✅ Test conclu — gagnant statistiquement significatif.")

            if test.winner_variant_id:
                winner_variant = variant_by_id.get(test.winner_variant_id) or _variants.get(test.winner_variant_id)
                if winner_variant is not None:
                    st.download_button(
                        "📄 Télécharger le gagnant en PDF",
                        data=generate_variant_pdf(product, winner_variant),
                        file_name=build_pdf_filename(product),
                        mime="application/pdf",
                        key=f"winner_pdf_{test.id}",
                    )

            if not any(r.exposures for r in results):
                st.caption("Pas encore de trafic enregistré sur ce test.")
                continue

            for r in sorted(results, key=lambda r: r.conversion_rate, reverse=True):
                variant = variant_by_id.get(r.variant_id)
                label = f"[{variant.framework.value}] {variant.copy.headline}" if variant else r.variant_id
                if r.is_winner:
                    badge = " 🏆 GAGNANTE"
                elif r.variant_id in test.killed_variant_ids:
                    badge = " ⛔ COUPÉE (budget)"
                else:
                    badge = ""
                st.markdown(
                    f"**{label}**{badge}  \n"
                    f"Expositions : {r.exposures} · Conversions : {r.conversions} · "
                    f"Taux : {r.conversion_rate * 100:.2f}%"
                    + (
                        f" · p-value vs meilleure variante : {r.p_value:.4f} "
                        f"(seuil {r.alpha_used:.4f} après {r.n_looks} consultation(s))"
                        if r.p_value is not None else ""
                    )
                )

            lrs_scores = {v.id: v.lrs_score for v in variants if v.lrs_score is not None}
            if lrs_scores:
                # Les variantes déjà coupées ne reçoivent plus de trafic —
                # inutile de leur attribuer une priorité de budget.
                stats = [
                    VariantStats(variant_id=r.variant_id, exposures=r.exposures, conversions=r.conversions)
                    for r in results
                    if r.variant_id not in test.killed_variant_ids
                ]
                st.markdown("##### Priorité de budget (score LRS x traction observée)")
                for p in rank_variants_for_budget(stats, lrs_scores):
                    variant = variant_by_id.get(p.variant_id)
                    label = f"[{variant.framework.value}] {variant.copy.headline}" if variant else p.variant_id
                    st.caption(f"{label} — priorité {p.priority_score:.4f} (score LRS {p.lrs_score or '—'})")


def _render_emails_tab() -> None:
    product = _selected_product("emails")
    if product is None:
        return

    variants = _variants.list_by_product(product.id)
    winning_variant = next((v for v in variants if v.status.value != "draft" and v.lrs_score), None)

    with st.form("cs_new_sequence"):
        st.markdown("#### Nouvelle séquence email")
        angle = st.text_area("Angle / idée produit", height=80)
        length = st.selectbox("Longueur de la séquence", [5, 7, 14], index=1)
        variant_labels = {"— Aucune —": None}
        variant_labels.update({f"[{v.framework.value}] {v.copy.headline}": v for v in variants})
        options = list(variant_labels.keys())
        default_label = (
            f"[{winning_variant.framework.value}] {winning_variant.copy.headline}"
            if winning_variant is not None
            else options[0]
        )
        selected_variant_label = st.selectbox(
            "Ancrer sur le copy gagnant (optionnel)", options, index=options.index(default_label)
        )
        submitted = st.form_submit_button("Générer la séquence", type="primary")

    if submitted:
        if not angle:
            st.error("L'angle produit est requis.")
        else:
            try:
                with st.spinner(f"Génération de {length} emails..."):
                    sequence = generate_email_sequence(
                        product, angle, length, winning_variant=variant_labels[selected_variant_label]
                    )
                    _sequences.create(sequence)
                st.success(f"Séquence de {length} emails générée.")
                st.rerun()
            except GenerationRefused as exc:
                st.error(str(exc))
            except RuntimeError as exc:
                st.error(f"Impossible de générer : {exc}")

    st.markdown("#### Séquences existantes")
    for seq in _sequences.list_by_product(product.id):
        with st.expander(f"✉️ {seq.angle[:60]} — {seq.length} emails"):
            for email in seq.emails:
                st.markdown(f"**J+{email['day_offset']} · {email['goal']}** — {email['subject']}")
                st.text(email["body"])
                st.divider()
