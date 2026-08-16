"""Couche repository : CRUD SQLite <-> dataclasses de creative_studio.core.

Chaque repository est volontairement une classe fine autour de requêtes
SQL explicites (pas d'ORM) — c'est la seule couche qui connaît le
schéma SQLite. Une migration vers Postgres en V2 se fait en réécrivant
cette couche seule, sans toucher à core/.
"""

from __future__ import annotations

import json
from dataclasses import asdict

from creative_studio.core.variants import (
    ABTest,
    ConclusionReason,
    CopyBlock,
    EmailSequence,
    Event,
    FormField,
    FormFieldType,
    FormSubmission,
    FormSubmissionSource,
    Framework,
    Funnel,
    FunnelObjective,
    FunnelStep,
    FunnelStepElement,
    FunnelStepForm,
    FunnelStepMedia,
    FunnelStepPopup,
    GenerationMode,
    MediaPlacement,
    MediaSourceType,
    MediaType,
    PopupMode,
    Product,
    TestResult,
    TestStatus,
    Variant,
    VariantKind,
    VariantStatus,
    VaryDimension,
)
from creative_studio.storage.db import db_session


class ProductRepository:
    def create(self, product: Product) -> Product:
        with db_session() as conn:
            conn.execute(
                """INSERT INTO products
                   (id, tenant_id, name, description, price_cents, currency,
                    stripe_payment_link, audience, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    product.id, product.tenant_id, product.name, product.description,
                    product.price_cents, product.currency, product.stripe_payment_link,
                    product.audience, product.created_at,
                ),
            )
        return product

    def get(self, product_id: str) -> Product | None:
        with db_session() as conn:
            row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        return self._from_row(row) if row else None

    def list(self, tenant_id: str = "local") -> list[Product]:
        with db_session() as conn:
            rows = conn.execute(
                "SELECT * FROM products WHERE tenant_id = ? ORDER BY created_at DESC", (tenant_id,)
            ).fetchall()
        return [self._from_row(r) for r in rows]

    @staticmethod
    def _from_row(row) -> Product:
        return Product(
            id=row["id"], tenant_id=row["tenant_id"], name=row["name"],
            description=row["description"], price_cents=row["price_cents"],
            currency=row["currency"], stripe_payment_link=row["stripe_payment_link"],
            audience=row["audience"], created_at=row["created_at"],
        )


class VariantRepository:
    def create(self, variant: Variant) -> Variant:
        with db_session() as conn:
            conn.execute(
                """INSERT INTO variants
                   (id, tenant_id, product_id, kind, framework, copy_json,
                    lrs_score, status, source_mode, varied_dimension, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    variant.id, variant.tenant_id, variant.product_id, variant.kind.value,
                    variant.framework.value, json.dumps(asdict(variant.copy), ensure_ascii=False),
                    variant.lrs_score, variant.status.value, variant.source_mode.value,
                    variant.varied_dimension.value if variant.varied_dimension else None,
                    variant.created_at,
                ),
            )
        return variant

    def get(self, variant_id: str) -> Variant | None:
        with db_session() as conn:
            row = conn.execute("SELECT * FROM variants WHERE id = ?", (variant_id,)).fetchone()
        return self._from_row(row) if row else None

    def list_by_product(self, product_id: str) -> list[Variant]:
        with db_session() as conn:
            rows = conn.execute(
                "SELECT * FROM variants WHERE product_id = ? ORDER BY created_at DESC", (product_id,)
            ).fetchall()
        return [self._from_row(r) for r in rows]

    def update_status(self, variant_id: str, status: VariantStatus) -> None:
        with db_session() as conn:
            conn.execute("UPDATE variants SET status = ? WHERE id = ?", (status.value, variant_id))

    def update_lrs_score(self, variant_id: str, score: int) -> None:
        with db_session() as conn:
            conn.execute("UPDATE variants SET lrs_score = ? WHERE id = ?", (score, variant_id))

    @staticmethod
    def _from_row(row) -> Variant:
        copy_data = json.loads(row["copy_json"])
        row_keys = row.keys()
        source_mode = row["source_mode"] if "source_mode" in row_keys else GenerationMode.FROM_SCRATCH.value
        varied_dimension = row["varied_dimension"] if "varied_dimension" in row_keys else None
        return Variant(
            id=row["id"], tenant_id=row["tenant_id"], product_id=row["product_id"],
            kind=VariantKind(row["kind"]), framework=Framework(row["framework"]),
            copy=CopyBlock(**copy_data), lrs_score=row["lrs_score"],
            status=VariantStatus(row["status"]),
            source_mode=GenerationMode(source_mode),
            varied_dimension=VaryDimension(varied_dimension) if varied_dimension else None,
            created_at=row["created_at"],
        )


class ABTestRepository:
    def create(self, test: ABTest) -> ABTest:
        with db_session() as conn:
            conn.execute(
                """INSERT INTO ab_tests
                   (id, tenant_id, product_id, name, status, winner_variant_id,
                    conclusion_reason, created_at, concluded_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    test.id, test.tenant_id, test.product_id, test.name, test.status.value,
                    test.winner_variant_id,
                    test.conclusion_reason.value if test.conclusion_reason else None,
                    test.created_at, test.concluded_at,
                ),
            )
            conn.executemany(
                "INSERT INTO ab_test_variants (test_id, variant_id) VALUES (?, ?)",
                [(test.id, vid) for vid in test.variant_ids],
            )
        return test

    def get(self, test_id: str) -> ABTest | None:
        with db_session() as conn:
            row = conn.execute("SELECT * FROM ab_tests WHERE id = ?", (test_id,)).fetchone()
            if not row:
                return None
            variant_rows = conn.execute(
                "SELECT variant_id, weight FROM ab_test_variants WHERE test_id = ?", (test_id,)
            ).fetchall()
        return self._from_row(row, variant_rows)

    def list_by_product(self, product_id: str) -> list[ABTest]:
        with db_session() as conn:
            rows = conn.execute(
                "SELECT * FROM ab_tests WHERE product_id = ? ORDER BY created_at DESC", (product_id,)
            ).fetchall()
            tests = []
            for row in rows:
                variant_rows = conn.execute(
                    "SELECT variant_id, weight FROM ab_test_variants WHERE test_id = ?", (row["id"],)
                ).fetchall()
                tests.append(self._from_row(row, variant_rows))
        return tests

    def conclude(
        self,
        test_id: str,
        winner_variant_id: str,
        concluded_at: str,
        reason: ConclusionReason = ConclusionReason.STATISTICAL_SIGNIFICANCE,
    ) -> None:
        with db_session() as conn:
            conn.execute(
                """UPDATE ab_tests SET status = ?, winner_variant_id = ?,
                   conclusion_reason = ?, concluded_at = ? WHERE id = ?""",
                (TestStatus.CONCLUDED.value, winner_variant_id, reason.value, concluded_at, test_id),
            )

    def kill_variant(self, test_id: str, variant_id: str) -> None:
        """Coupe une variante du trafic (poids à 0) — garde-fou de budget."""
        with db_session() as conn:
            conn.execute(
                "UPDATE ab_test_variants SET weight = 0 WHERE test_id = ? AND variant_id = ?",
                (test_id, variant_id),
            )

    def find_by_variant(self, variant_id: str) -> ABTest | None:
        """Le test A/B le plus récent qui inclut cette variante — utilisé par
        le chaînage de funnel (quel test_id sert le trafic réel de l'étape
        suivante) et par l'analytics de drop-off (core.funnel_analytics),
        que ce soit la variante d'origine du maillon ou une variante
        alternative testée par la suite pour la même position."""
        with db_session() as conn:
            row = conn.execute(
                """SELECT t.* FROM ab_tests t
                   JOIN ab_test_variants v ON v.test_id = t.id
                   WHERE v.variant_id = ?
                   ORDER BY t.created_at DESC LIMIT 1""",
                (variant_id,),
            ).fetchone()
            if row is None:
                return None
            variant_rows = conn.execute(
                "SELECT variant_id, weight FROM ab_test_variants WHERE test_id = ?", (row["id"],)
            ).fetchall()
        return self._from_row(row, variant_rows)

    @staticmethod
    def _from_row(row, variant_rows) -> ABTest:
        variant_ids = [r["variant_id"] for r in variant_rows]
        killed_variant_ids = [r["variant_id"] for r in variant_rows if r["weight"] == 0]
        reason = row["conclusion_reason"] if "conclusion_reason" in row.keys() else None
        return ABTest(
            id=row["id"], tenant_id=row["tenant_id"], product_id=row["product_id"],
            name=row["name"], variant_ids=variant_ids, status=TestStatus(row["status"]),
            winner_variant_id=row["winner_variant_id"], killed_variant_ids=killed_variant_ids,
            conclusion_reason=ConclusionReason(reason) if reason else None,
            created_at=row["created_at"], concluded_at=row["concluded_at"],
        )


class AssignmentRepository:
    def get_or_assign(self, test_id: str, visitor_id: str, variant_id_if_new: str, assigned_at: str) -> str:
        """Retourne la variante déjà assignée à ce visiteur, ou l'assigne si absente.

        Utilise INSERT OR IGNORE plutôt qu'un SELECT-puis-INSERT : deux requêtes
        concurrentes pour le même (test_id, visitor_id) ne lèvent jamais
        d'IntegrityError, et le SELECT final fait toujours foi sur la variante
        réellement stockée (la première des deux à committer).
        """
        with db_session() as conn:
            conn.execute(
                """INSERT OR IGNORE INTO assignments (test_id, visitor_id, variant_id, assigned_at)
                   VALUES (?, ?, ?, ?)""",
                (test_id, visitor_id, variant_id_if_new, assigned_at),
            )
            row = conn.execute(
                "SELECT variant_id FROM assignments WHERE test_id = ? AND visitor_id = ?",
                (test_id, visitor_id),
            ).fetchone()
        return row["variant_id"]


class EventRepository:
    def record(self, event: Event) -> None:
        with db_session() as conn:
            conn.execute(
                """INSERT INTO events
                   (tenant_id, test_id, variant_id, visitor_id, event_type, amount_cents, ts)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    event.tenant_id, event.test_id, event.variant_id, event.visitor_id,
                    event.event_type.value, event.amount_cents, event.ts,
                ),
            )

    def counts_by_variant(self, test_id: str, event_type: str) -> dict[str, int]:
        with db_session() as conn:
            rows = conn.execute(
                """SELECT variant_id, COUNT(DISTINCT visitor_id) AS n
                   FROM events WHERE test_id = ? AND event_type = ?
                   GROUP BY variant_id""",
                (test_id, event_type),
            ).fetchall()
        return {r["variant_id"]: r["n"] for r in rows}


class TestResultRepository:
    def save(self, result: TestResult) -> None:
        with db_session() as conn:
            conn.execute(
                """INSERT INTO test_results
                   (test_id, variant_id, exposures, conversions, conversion_rate,
                    p_value, is_significant, is_winner, alpha_used, n_looks, computed_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    result.test_id, result.variant_id, result.exposures, result.conversions,
                    result.conversion_rate, result.p_value, int(result.is_significant),
                    int(result.is_winner), result.alpha_used, result.n_looks, result.computed_at,
                ),
            )

    def latest_for_test(self, test_id: str) -> list[TestResult]:
        with db_session() as conn:
            latest_ts = conn.execute(
                "SELECT MAX(computed_at) AS ts FROM test_results WHERE test_id = ?", (test_id,)
            ).fetchone()["ts"]
            if not latest_ts:
                return []
            rows = conn.execute(
                "SELECT * FROM test_results WHERE test_id = ? AND computed_at = ?",
                (test_id, latest_ts),
            ).fetchall()
        return [
            TestResult(
                test_id=r["test_id"], variant_id=r["variant_id"], exposures=r["exposures"],
                conversions=r["conversions"], conversion_rate=r["conversion_rate"],
                p_value=r["p_value"], is_significant=bool(r["is_significant"]),
                is_winner=bool(r["is_winner"]), alpha_used=r["alpha_used"], n_looks=r["n_looks"],
                computed_at=r["computed_at"],
            )
            for r in rows
        ]

    def count_prior_looks(self, test_id: str) -> int:
        """Nombre d'évaluations déjà effectuées sur ce test (peeks passés).

        Sert à la correction de Bonferroni dynamique dans core.stats —
        chaque consultation des résultats compte comme une comparaison
        supplémentaire et durcit le seuil de significativité exigé.
        """
        with db_session() as conn:
            row = conn.execute(
                "SELECT COUNT(DISTINCT computed_at) AS n FROM test_results WHERE test_id = ?",
                (test_id,),
            ).fetchone()
        return row["n"] or 0


class FunnelRepository:
    def create(self, funnel: Funnel, steps: list[FunnelStep]) -> Funnel:
        """Persiste le funnel et ses maillons en une seule transaction — les
        Variant référencés par chaque FunnelStep doivent déjà avoir été créés
        via VariantRepository.create() avant cet appel."""
        with db_session() as conn:
            conn.execute(
                """INSERT INTO funnels
                   (id, tenant_id, product_id, objective, angle, tone, promise, source_reference, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    funnel.id, funnel.tenant_id, funnel.product_id, funnel.objective.value,
                    funnel.angle, funnel.tone, funnel.promise, funnel.source_reference, funnel.created_at,
                ),
            )
            conn.executemany(
                """INSERT INTO funnel_steps
                   (id, tenant_id, funnel_id, variant_id, step_order, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                [
                    (s.id, s.tenant_id, s.funnel_id, s.variant_id, s.step_order, s.created_at)
                    for s in steps
                ],
            )
        return funnel

    def list_by_product(self, product_id: str) -> list[Funnel]:
        with db_session() as conn:
            rows = conn.execute(
                "SELECT * FROM funnels WHERE product_id = ? ORDER BY created_at DESC", (product_id,)
            ).fetchall()
        return [self._from_row(r) for r in rows]

    def list_steps(self, funnel_id: str) -> list[FunnelStep]:
        with db_session() as conn:
            rows = conn.execute(
                "SELECT * FROM funnel_steps WHERE funnel_id = ? ORDER BY step_order ASC", (funnel_id,)
            ).fetchall()
        return [self._step_from_row(r) for r in rows]

    def get_step_by_variant(self, variant_id: str) -> FunnelStep | None:
        """Résout le maillon de funnel (s'il existe) auquel appartient une
        variante — utilisé par le service de diffusion pour savoir si la
        page servie doit inclure des médias/éléments de conversion, sans
        que serving/app.py n'ait à connaître le pipeline de génération."""
        with db_session() as conn:
            row = conn.execute(
                "SELECT * FROM funnel_steps WHERE variant_id = ?", (variant_id,)
            ).fetchone()
        return self._step_from_row(row) if row else None

    def get_next_step(self, funnel_id: str, current_step_order: int) -> FunnelStep | None:
        """Le maillon suivant dans l'ordre du funnel — utilisé pour chaîner
        le CTA d'une étape vers la suivante plutôt que de renvoyer
        systématiquement vers Stripe, ce qui rend l'entonnoir de conversion
        (core.funnel_analytics) réellement significatif."""
        with db_session() as conn:
            row = conn.execute(
                """SELECT * FROM funnel_steps WHERE funnel_id = ? AND step_order > ?
                   ORDER BY step_order ASC LIMIT 1""",
                (funnel_id, current_step_order),
            ).fetchone()
        return self._step_from_row(row) if row else None

    @staticmethod
    def _step_from_row(row) -> FunnelStep:
        return FunnelStep(
            id=row["id"], tenant_id=row["tenant_id"], funnel_id=row["funnel_id"],
            variant_id=row["variant_id"], step_order=row["step_order"], created_at=row["created_at"],
        )

    @staticmethod
    def _from_row(row) -> Funnel:
        row_keys = row.keys()
        source_reference = row["source_reference"] if "source_reference" in row_keys else None
        return Funnel(
            id=row["id"], tenant_id=row["tenant_id"], product_id=row["product_id"],
            objective=FunnelObjective(row["objective"]), angle=row["angle"], tone=row["tone"],
            promise=row["promise"], source_reference=source_reference, created_at=row["created_at"],
        )


class FunnelStepMediaRepository:
    def create(self, media: FunnelStepMedia) -> FunnelStepMedia:
        with db_session() as conn:
            conn.execute(
                """INSERT INTO funnel_step_media
                   (id, tenant_id, step_id, media_type, source_type, location, placement, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    media.id, media.tenant_id, media.step_id, media.media_type.value,
                    media.source_type.value, media.location, media.placement.value, media.created_at,
                ),
            )
        return media

    def list_by_step(self, step_id: str) -> list[FunnelStepMedia]:
        with db_session() as conn:
            rows = conn.execute(
                "SELECT * FROM funnel_step_media WHERE step_id = ? ORDER BY created_at ASC", (step_id,)
            ).fetchall()
        return [
            FunnelStepMedia(
                id=r["id"], tenant_id=r["tenant_id"], step_id=r["step_id"],
                media_type=MediaType(r["media_type"]), source_type=MediaSourceType(r["source_type"]),
                location=r["location"], placement=MediaPlacement(r["placement"]), created_at=r["created_at"],
            )
            for r in rows
        ]

    def delete(self, media_id: str) -> None:
        with db_session() as conn:
            conn.execute("DELETE FROM funnel_step_media WHERE id = ?", (media_id,))


class FunnelStepElementRepository:
    def create(self, element: FunnelStepElement) -> FunnelStepElement:
        with db_session() as conn:
            conn.execute(
                """INSERT INTO funnel_step_elements
                   (id, tenant_id, step_id, element_type, config_json, enabled, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    element.id, element.tenant_id, element.step_id, element.element_type,
                    json.dumps(element.config, ensure_ascii=False), int(element.enabled), element.created_at,
                ),
            )
        return element

    def list_by_step(self, step_id: str) -> list[FunnelStepElement]:
        with db_session() as conn:
            rows = conn.execute(
                "SELECT * FROM funnel_step_elements WHERE step_id = ? ORDER BY created_at ASC", (step_id,)
            ).fetchall()
        return [
            FunnelStepElement(
                id=r["id"], tenant_id=r["tenant_id"], step_id=r["step_id"],
                element_type=r["element_type"], config=json.loads(r["config_json"]),
                enabled=bool(r["enabled"]), created_at=r["created_at"],
            )
            for r in rows
        ]

    def set_enabled(self, element_id: str, enabled: bool) -> None:
        with db_session() as conn:
            conn.execute(
                "UPDATE funnel_step_elements SET enabled = ? WHERE id = ?", (int(enabled), element_id)
            )

    def delete(self, element_id: str) -> None:
        with db_session() as conn:
            conn.execute("DELETE FROM funnel_step_elements WHERE id = ?", (element_id,))


def _screens_to_json(screens: list[list[FormField]]) -> str:
    return json.dumps([[asdict(f) for f in screen] for screen in screens], ensure_ascii=False)


def _screens_from_json(raw: str) -> list[list[FormField]]:
    return [
        [
            FormField(
                name=d["name"], label=d["label"],
                field_type=FormFieldType(d["field_type"]), required=d["required"],
            )
            for d in screen
        ]
        for screen in json.loads(raw)
    ]


class FunnelStepFormRepository:
    """Un seul formulaire par étape (UNIQUE sur step_id) — un upsert simple
    (delete + create) plutôt qu'un UPDATE champ par champ, la config entière
    étant remplacée à chaque modification depuis l'UI."""

    def upsert(self, form: FunnelStepForm) -> FunnelStepForm:
        with db_session() as conn:
            conn.execute("DELETE FROM funnel_step_forms WHERE step_id = ?", (form.step_id,))
            conn.execute(
                """INSERT INTO funnel_step_forms
                   (id, tenant_id, step_id, screens_json, enabled, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    form.id, form.tenant_id, form.step_id, _screens_to_json(form.screens),
                    int(form.enabled), form.created_at,
                ),
            )
        return form

    def get_by_step(self, step_id: str) -> FunnelStepForm | None:
        with db_session() as conn:
            row = conn.execute(
                "SELECT * FROM funnel_step_forms WHERE step_id = ?", (step_id,)
            ).fetchone()
        if row is None:
            return None
        return FunnelStepForm(
            id=row["id"], tenant_id=row["tenant_id"], step_id=row["step_id"],
            screens=_screens_from_json(row["screens_json"]), enabled=bool(row["enabled"]),
            created_at=row["created_at"],
        )

    def delete_by_step(self, step_id: str) -> None:
        with db_session() as conn:
            conn.execute("DELETE FROM funnel_step_forms WHERE step_id = ?", (step_id,))


class FunnelStepPopupRepository:
    """Un seul popup par étape (UNIQUE sur step_id), même logique d'upsert
    que FunnelStepFormRepository."""

    def upsert(self, popup: FunnelStepPopup) -> FunnelStepPopup:
        with db_session() as conn:
            conn.execute("DELETE FROM funnel_step_popups WHERE step_id = ?", (popup.step_id,))
            conn.execute(
                """INSERT INTO funnel_step_popups
                   (id, tenant_id, step_id, mode, copy_json, enabled, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    popup.id, popup.tenant_id, popup.step_id, popup.mode.value,
                    json.dumps(asdict(popup.copy), ensure_ascii=False), int(popup.enabled), popup.created_at,
                ),
            )
        return popup

    def get_by_step(self, step_id: str) -> FunnelStepPopup | None:
        with db_session() as conn:
            row = conn.execute(
                "SELECT * FROM funnel_step_popups WHERE step_id = ?", (step_id,)
            ).fetchone()
        if row is None:
            return None
        return FunnelStepPopup(
            id=row["id"], tenant_id=row["tenant_id"], step_id=row["step_id"],
            mode=PopupMode(row["mode"]), copy=CopyBlock(**json.loads(row["copy_json"])),
            enabled=bool(row["enabled"]), created_at=row["created_at"],
        )

    def delete_by_step(self, step_id: str) -> None:
        with db_session() as conn:
            conn.execute("DELETE FROM funnel_step_popups WHERE step_id = ?", (step_id,))


class FormSubmissionRepository:
    def create(self, submission: FormSubmission) -> FormSubmission:
        with db_session() as conn:
            conn.execute(
                """INSERT INTO form_submissions
                   (id, tenant_id, test_id, variant_id, visitor_id, source, values_json, submitted_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    submission.id, submission.tenant_id, submission.test_id, submission.variant_id,
                    submission.visitor_id, submission.source.value,
                    json.dumps(submission.values, ensure_ascii=False), submission.submitted_at,
                ),
            )
        return submission

    def count_by_variant(self, test_id: str) -> dict[str, int]:
        with db_session() as conn:
            rows = conn.execute(
                """SELECT variant_id, COUNT(*) AS n FROM form_submissions
                   WHERE test_id = ? GROUP BY variant_id""",
                (test_id,),
            ).fetchall()
        return {r["variant_id"]: r["n"] for r in rows}


class EmailSequenceRepository:
    def create(self, sequence: EmailSequence) -> EmailSequence:
        with db_session() as conn:
            conn.execute(
                """INSERT INTO email_sequences
                   (id, tenant_id, product_id, angle, length, emails_json, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    sequence.id, sequence.tenant_id, sequence.product_id, sequence.angle,
                    sequence.length, json.dumps(sequence.emails, ensure_ascii=False),
                    sequence.created_at,
                ),
            )
        return sequence

    def list_by_product(self, product_id: str) -> list[EmailSequence]:
        with db_session() as conn:
            rows = conn.execute(
                "SELECT * FROM email_sequences WHERE product_id = ? ORDER BY created_at DESC",
                (product_id,),
            ).fetchall()
        return [
            EmailSequence(
                id=r["id"], tenant_id=r["tenant_id"], product_id=r["product_id"],
                angle=r["angle"], length=r["length"], emails=json.loads(r["emails_json"]),
                created_at=r["created_at"],
            )
            for r in rows
        ]
