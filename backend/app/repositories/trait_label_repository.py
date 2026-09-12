"""academy_trait_labels 데이터 접근."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.academy_trait_label import AcademyTraitLabel


def existing_dedup_keys(
    db: Session, academy_ids: list[int] | None = None
) -> set[tuple[int, str, str]]:
    """(academy_id, label, source_url) 집합 — 재실행 시 사전 조회로 중복 스킵."""
    stmt = select(
        AcademyTraitLabel.academy_id,
        AcademyTraitLabel.label,
        AcademyTraitLabel.source_url,
    )
    if academy_ids is not None:
        if not academy_ids:
            return set()
        stmt = stmt.where(AcademyTraitLabel.academy_id.in_(academy_ids))
    rows = db.execute(stmt).all()
    return {(aid, label, url) for aid, label, url in rows}


def add_labels(db: Session, rows: list[AcademyTraitLabel]) -> None:
    for row in rows:
        db.add(row)


def count_all(db: Session) -> int:
    return int(db.scalar(select(func.count()).select_from(AcademyTraitLabel)) or 0)


def count_by_status(db: Session, status: str) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(AcademyTraitLabel)
            .where(AcademyTraitLabel.status == status)
        )
        or 0
    )
