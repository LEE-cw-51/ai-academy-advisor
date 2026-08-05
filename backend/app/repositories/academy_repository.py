from collections.abc import Sequence

from sqlalchemy import Select, case, func, or_, select
from sqlalchemy.orm import Session

from app.core.constants import ClassType, CurriculumType, SchoolLevel
from app.models.academy import Academy
from app.schemas.academy import AcademyListParams, RecommendationRequest

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


def _apply_recommendation_filters(
    stmt: Select, params: RecommendationRequest
) -> Select:
    stmt = _apply_filters(stmt, params)
    if params.region is not None:
        stmt = stmt.where(Academy.address.ilike(f"%{params.region}%"))
    if params.budget_max is not None:
        stmt = stmt.where(
            Academy.tuition_monthly_fee.is_not(None),
            Academy.tuition_monthly_fee <= params.budget_max,
        )
    return stmt


def list_recommendations(
    db: Session, params: RecommendationRequest
) -> tuple[list[Academy], int]:
    total = (
        db.scalar(_apply_recommendation_filters(select(func.count(Academy.id)), params))
        or 0
    )
    stmt = (
        _apply_recommendation_filters(select(Academy), params)
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


def list_candidates(
    db: Session,
    params: RecommendationRequest,
    pool_limit: int = 200,
    name_like: Sequence[str] = (),
) -> list[Academy]:
    """AI 소프트 필터용 후보 풀.

    `_apply_filters` / `_apply_recommendation_filters` 를 **의도적으로 재사용하지 않는다.**
    그쪽은 POST /recommendations 의 동결된 하드 필터 계약이고, 이쪽은 리콜 확보용이다.
    SQL 하드 필터는 region(address.ilike)과 q 뿐이며, 3상태 bool·budget 은
    scoring.py 에서 랭킹한다. 두 계약을 다시 결합하는 DRY 리팩터를 하지 말 것.

    `name_like` 는 필터가 아니라 정렬 힌트다. region 매치가 많아 LIMIT 으로
    잘릴 때 과목 토큰이 이름에 든 행을 풀 앞쪽으로 올려 채점 기회를 준다.
    """
    stmt = select(Academy)
    if params.region is not None:
        stmt = stmt.where(Academy.address.ilike(f"%{params.region}%"))
    if params.q is not None:
        pattern = f"%{params.q}%"
        stmt = stmt.where(
            or_(Academy.name.ilike(pattern), Academy.address.ilike(pattern))
        )

    order_clauses: list = []
    if name_like:
        match_any = or_(*(Academy.name.ilike(pattern) for pattern in name_like))
        order_clauses.append(case((match_any, 0), else_=1))
    order_clauses.extend([Academy.name, Academy.id])

    stmt = stmt.order_by(*order_clauses).limit(pool_limit)
    return list(db.scalars(stmt))
