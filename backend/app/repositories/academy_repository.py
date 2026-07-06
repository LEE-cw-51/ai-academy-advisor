from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.core.constants import ClassType, CurriculumType, SchoolLevel
from app.models.academy import Academy
from app.schemas.academy import AcademyListParams

_LEVEL_COLUMNS = {
    SchoolLevel.ELEMENTARY: Academy.level_elementary,
    SchoolLevel.MIDDLE: Academy.level_middle,
    SchoolLevel.HIGH: Academy.level_high,
}

_CLASS_TYPE_COLUMNS = {
    ClassType.SMALL_GROUP: Academy.class_small_group,
    ClassType.GROUP: Academy.class_group,
    ClassType.ONE_ON_ONE: Academy.class_one_on_one,
}

_CURRICULUM_COLUMNS = {
    CurriculumType.SEONHAENG: Academy.curriculum_seonhaeng,
    CurriculumType.NAESIN: Academy.curriculum_naesin,
    CurriculumType.SUNEUNG: Academy.curriculum_suneung,
}


def _apply_filters(stmt: Select, params: AcademyListParams) -> Select:
    # Boolean 필터는 IS TRUE / IS FALSE 를 명시해 NULL(미확인)을 제외한다.
    if params.level is not None:
        stmt = stmt.where(_LEVEL_COLUMNS[params.level].is_(True))
    if params.class_type is not None:
        stmt = stmt.where(_CLASS_TYPE_COLUMNS[params.class_type].is_(True))
    if params.curriculum is not None:
        stmt = stmt.where(_CURRICULUM_COLUMNS[params.curriculum].is_(True))
    if params.shuttle is not None:
        stmt = stmt.where(Academy.shuttle_available.is_(params.shuttle))
    if params.q is not None:
        pattern = f"%{params.q}%"
        stmt = stmt.where(
            or_(Academy.name.ilike(pattern), Academy.address.ilike(pattern))
        )
    return stmt


def list_academies(db: Session, params: AcademyListParams) -> tuple[list[Academy], int]:
    total = db.scalar(_apply_filters(select(func.count(Academy.id)), params)) or 0
    stmt = (
        _apply_filters(select(Academy), params)
        .order_by(Academy.name, Academy.id)
        .limit(params.limit)
        .offset(params.offset)
    )
    return list(db.scalars(stmt)), total


def get_by_id(db: Session, academy_id: int) -> Academy | None:
    return db.get(Academy, academy_id)


def find_by_registration_number(
    db: Session, registration_number: str
) -> Academy | None:
    return db.scalar(
        select(Academy).where(Academy.registration_number == registration_number)
    )


def find_by_name_and_address(
    db: Session, name: str, address: str | None
) -> Academy | None:
    stmt = select(Academy).where(Academy.name == name)
    if address is None:
        stmt = stmt.where(Academy.address.is_(None))
    else:
        stmt = stmt.where(Academy.address == address)
    return db.scalar(stmt)


def list_all(db: Session) -> list[Academy]:
    return list(db.scalars(select(Academy).order_by(Academy.id)))
