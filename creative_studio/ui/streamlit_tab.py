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

from creative_studio.core.budget_guard import DEFAULT_KILL_EXPOSURE_THRESHOLD
from creative_studio.core.copy_generation import GenerationRefused, generate_variants
from creative_studio.core.email_sequences import generate_email_sequence
from creative_studio.core.prioritization import rank_variants_for_budget
from creative_studio.core.stats import VariantStats
from creative_studio.core.test_evaluation import compute_and_save_results
from creative_studio.core.variants import (
    ABTest,
    ConclusionReason,
    Framework,
    Product,
    VariantKind,
    VariantStatus,
)
from creative_studio.storage.db import init_db
from creative_studio.storage.repository import (
    ABTestRepository,
    EmailSequenceRepository,
    EventRepository,
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


def _selected_product() -> Product | None:
    products = _products.list()
    if not products:
        st.info("Crée d'abord un produit dans l'onglet 📦 Produits.")
        return None
    labels = {f"{p.name} ({p.price_cents / 100:.2f} {p.currency})": p for p in products}
    label = st.selectbox("Produit", list(labels.keys()), key="cs_selected_product")
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
    product = _selected_product()
    if product is None:
        return

    col1, col2 = st.columns(2)
    with col1:
        kind = st.selectbox(
            "Type de créatif",
            [VariantKind.SALES_PAGE, VariantKind.ADVERTORIAL],
            format_func=lambda k: "Page de vente" if k == VariantKind.SALES_PAGE else "Advertorial",
        )
    with col2:
        frameworks = st.multiselect(
            "Frameworks",
            [Framework.AIDA, Framework.PAS, Framework.HORMOZI],
            default=[Framework.AIDA, Framework.PAS, Framework.HORMOZI],
            format_func=lambda f: f.value,
        )

    if st.button("🪄 Générer les variantes avec Claude", type="primary", disabled=not frameworks):
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

    st.markdown("#### Variantes existantes")
    existing = _variants.list_by_product(product.id)
    if not existing:
        st.caption("Aucune variante pour ce produit pour l'instant.")
        return

    for v in existing:
        with st.expander(f"[{v.framework.value}] {v.copy.headline} — statut: {v.status.value}"):
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


def _render_tests_tab() -> None:
    product = _selected_product()
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
    product = _selected_product()
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
