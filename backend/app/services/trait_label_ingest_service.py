"""리뷰 → academy_trait_labels 배치 적재 (idempotent).

``academies.curriculum_*`` 등 사실 컬럼은 절대 쓰지 않는다.
기본 status=candidate. UI·상담 연결은 Stage 3 이후.

`review_ingest_service.ingest_reviews` 와 같은 재개 가능 계약을 따른다 — 청크마다
커밋해서 중간에 끊겨도 앞선 적재가 남고, 재실행은 dedup 이 이미 넣은 건을 건너뛴다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.trait_labels import STATUSES
from app.models.academy_trait_label import AcademyTraitLabel
from app.models.review import Review
from app.repositories import trait_label_repository
from app.services.trait_label_matcher import (
    match_labels,
    snippet_around,
    source_type_from_review_source,
)

# 청크 크기. 작게 잡으면 커밋 왕복이 늘고, 크게 잡으면 끊겼을 때 잃는 양이 는다.
_COMMIT_CHUNK = 200


@dataclass
class TraitLabelIngestReport:
    reviews_scanned: int = 0
    inserted: int = 0
    skipped_duplicate: int = 0
    skipped_no_match: int = 0
    purged: int = 0  # --purge-candidates 로 지운 기존 candidate 행 수
    by_label: dict[str, int] = field(default_factory=dict)
    academies_touched: set[int] = field(default_factory=set)

    def summary_line(self) -> str:
        labels = " ".join(f"{k}={v}" for k, v in sorted(self.by_label.items()))
        return (
            f"scanned={self.reviews_scanned} inserted={self.inserted} "
            f"dup={self.skipped_duplicate} no_match={self.skipped_no_match} "
            f"purged={self.purged} academies={len(self.academies_touched)}"
            + (f" | {labels}" if labels else "")
        )


def _dedup_source_url(review_id: int, source_url: str | None) -> str:
    if source_url:
        return source_url
    return f"review:{review_id}"


def ingest_trait_labels_from_reviews(
    db: Session,
    *,
    academy_id: int | None = None,
    limit: int | None = None,
    dry_run: bool = False,
    status: str = "candidate",
    purge_candidates: bool = False,
) -> TraitLabelIngestReport:
    """Scan reviews, extract closed labels, upsert (skip existing keys).

    Pre-query dedup like review ingest — avoids IntegrityError aborting a batch.

    `purge_candidates` 는 매처 규칙이 바뀌어 candidate 를 다시 뽑을 때만 쓴다.
    `published` 행은 어떤 경우에도 지우지 않는다.
    """
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}, got {status!r}")

    report = TraitLabelIngestReport()

    if purge_candidates:
        if dry_run:
            report.purged = trait_label_repository.count_by_status(db, "candidate")
        else:
            report.purged = trait_label_repository.delete_by_status(db, "candidate")
            db.commit()

    # 컬럼을 지정해서 읽는다 — `select(Review)` 는 1024차원 `embedding` 까지 끌어와
    # 세션에 얹는다. 이 스캔이 쓰는 건 아래 6개뿐이다.
    stmt = select(
        Review.id,
        Review.academy_id,
        Review.content,
        Review.source,
        Review.source_url,
        Review.published_at,
    ).order_by(Review.id)
    if academy_id is not None:
        stmt = stmt.where(Review.academy_id == academy_id)
    if limit is not None:
        stmt = stmt.limit(limit)

    # `yield_per` 스트리밍과 중간 커밋은 같이 쓸 수 없다 (커서가 닫힌다). 임베딩을
    # 뺀 가벼운 행이므로 한 번에 읽고 청크로 커밋한다.
    rows = db.execute(stmt).all()
    academy_ids = sorted({row.academy_id for row in rows})
    existing = trait_label_repository.existing_dedup_keys(db, academy_ids)

    pending: list[AcademyTraitLabel] = []

    def flush() -> None:
        if not pending:
            return
        trait_label_repository.add_labels(db, pending)
        db.commit()
        pending.clear()

    for row in rows:
        report.reviews_scanned += 1
        content = row.content or ""
        hits = match_labels(content)
        if not hits:
            report.skipped_no_match += 1
            continue

        source_url = _dedup_source_url(row.id, row.source_url)
        source_type = source_type_from_review_source(row.source)
        observed: date | None = row.published_at

        for label, kw in hits:
            key = (row.academy_id, label, source_url)
            if key in existing:
                report.skipped_duplicate += 1
                continue
            existing.add(key)
            report.inserted += 1
            report.by_label[label] = report.by_label.get(label, 0) + 1
            report.academies_touched.add(row.academy_id)
            if dry_run:
                continue
            pending.append(
                AcademyTraitLabel(
                    academy_id=row.academy_id,
                    label=label,
                    source_type=source_type,
                    source_url=source_url,
                    snippet=snippet_around(content, kw),
                    observed_at=observed,
                    status=status,
                )
            )

        if len(pending) >= _COMMIT_CHUNK:
            flush()

    if not dry_run:
        flush()

    return report
