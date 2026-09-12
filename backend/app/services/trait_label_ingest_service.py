"""리뷰 → academy_trait_labels 배치 적재 (idempotent).

``academies.curriculum_*`` 등 사실 컬럼은 절대 쓰지 않는다.
기본 status=candidate. UI·상담 연결은 Stage 3 이후.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.academy_trait_label import AcademyTraitLabel
from app.models.review import Review
from app.repositories import trait_label_repository
from app.services.trait_label_matcher import (
    match_labels,
    snippet_around,
    source_type_from_review_source,
)


@dataclass
class TraitLabelIngestReport:
    reviews_scanned: int = 0
    inserted: int = 0
    skipped_duplicate: int = 0
    skipped_no_match: int = 0
    by_label: dict[str, int] = field(default_factory=dict)
    academies_touched: set[int] = field(default_factory=set)

    def summary_line(self) -> str:
        labels = " ".join(f"{k}={v}" for k, v in sorted(self.by_label.items()))
        return (
            f"scanned={self.reviews_scanned} inserted={self.inserted} "
            f"dup={self.skipped_duplicate} no_match={self.skipped_no_match} "
            f"academies={len(self.academies_touched)}"
            + (f" | {labels}" if labels else "")
        )


def _dedup_source_url(review: Review) -> str:
    if review.source_url:
        return review.source_url
    return f"review:{review.id}"


def ingest_trait_labels_from_reviews(
    db: Session,
    *,
    academy_id: int | None = None,
    limit: int | None = None,
    dry_run: bool = False,
    status: str = "candidate",
) -> TraitLabelIngestReport:
    """Scan reviews, extract closed labels, upsert (skip existing keys).

    Pre-query dedup like review ingest — avoids IntegrityError aborting a batch.
    """
    report = TraitLabelIngestReport()

    stmt = select(Review).order_by(Review.id)
    if academy_id is not None:
        stmt = stmt.where(Review.academy_id == academy_id)
    if limit is not None:
        stmt = stmt.limit(limit)

    reviews = list(db.scalars(stmt).all())
    academy_ids = sorted({r.academy_id for r in reviews})
    existing = trait_label_repository.existing_dedup_keys(db, academy_ids)

    pending: list[AcademyTraitLabel] = []

    for review in reviews:
        report.reviews_scanned += 1
        content = review.content or ""
        hits = match_labels(content)
        if not hits:
            report.skipped_no_match += 1
            continue

        source_url = _dedup_source_url(review)
        source_type = source_type_from_review_source(review.source)
        observed = review.published_at

        any_new = False
        for label, kw in hits:
            key = (review.academy_id, label, source_url)
            if key in existing:
                report.skipped_duplicate += 1
                continue
            existing.add(key)
            any_new = True
            report.inserted += 1
            report.by_label[label] = report.by_label.get(label, 0) + 1
            report.academies_touched.add(review.academy_id)
            if dry_run:
                continue
            pending.append(
                AcademyTraitLabel(
                    academy_id=review.academy_id,
                    label=label,
                    source_type=source_type,
                    source_url=source_url,
                    snippet=snippet_around(content, kw),
                    observed_at=observed,
                    status=status,
                )
            )

        if not any_new and hits:
            # all hits were duplicates — already counted above
            pass

    if not dry_run and pending:
        trait_label_repository.add_labels(db, pending)
        db.commit()

    return report
