"""academy_repository.list_candidates — AI 소프트 필터 후보 풀."""

from app.core.constants import ClassType, CurriculumType, SchoolLevel
from app.models.academy import Academy
from app.repositories import academy_repository
from app.schemas.academy import RecommendationRequest


def _seed(db, rows: list[Academy]) -> list[Academy]:
    db.add_all(rows)
    db.commit()
    for row in rows:
        db.refresh(row)
    return rows


def test_null_facts_still_returned_with_soft_conditions(db_session):
    """3상태·예산이 전부 NULL 이어도 level/class/curriculum/shuttle/budget 요청에 반환된다."""
    _seed(
        db_session,
        [
            Academy(
                name="미확인학원",
                address="경기도 하남시 미사대로 1",
            )
        ],
    )
    params = RecommendationRequest(
        level=SchoolLevel.HIGH,
        class_type=ClassType.SMALL_GROUP,
        curriculum=CurriculumType.NAESIN,
        shuttle=True,
        budget_max=300_000,
        region="미사",
        limit=20,
    )
    rows = academy_repository.list_candidates(db_session, params)
    assert len(rows) == 1
    assert rows[0].name == "미확인학원"


def test_region_is_hard_filter(db_session):
    _seed(
        db_session,
        [
            Academy(name="미사학원", address="경기도 하남시 미사대로 1"),
            Academy(name="강남학원", address="서울시 강남구 1"),
        ],
    )
    params = RecommendationRequest(region="미사", limit=20)
    names = [r.name for r in academy_repository.list_candidates(db_session, params)]
    assert names == ["미사학원"]


def test_q_is_hard_filter(db_session):
    _seed(
        db_session,
        [
            Academy(name="가온수학", address="미사"),
            Academy(name="나래영어", address="미사"),
        ],
    )
    params = RecommendationRequest(q="수학", limit=20)
    names = [r.name for r in academy_repository.list_candidates(db_session, params)]
    assert names == ["가온수학"]


def test_pool_limit_respected(db_session):
    _seed(
        db_session,
        [Academy(name=f"학원{i:03d}", address="미사") for i in range(5)],
    )
    params = RecommendationRequest(limit=20)
    rows = academy_repository.list_candidates(db_session, params, pool_limit=3)
    assert len(rows) == 3


def test_name_like_saves_matching_rows_from_truncation(db_session):
    """가나다순 앞쪽만 남으면 '하늘수학'이 잘리므로 name_like 로 앞으로 올린다."""
    _seed(
        db_session,
        [
            Academy(name="가온피아노", address="미사"),
            Academy(name="나래피아노", address="미사"),
            Academy(name="다온피아노", address="미사"),
            Academy(name="하늘수학", address="미사"),
        ],
    )
    params = RecommendationRequest(region="미사", limit=20)
    without = academy_repository.list_candidates(db_session, params, pool_limit=2)
    assert [r.name for r in without] == ["가온피아노", "나래피아노"]

    with_hint = academy_repository.list_candidates(
        db_session, params, pool_limit=2, name_like=["%수학%"]
    )
    assert [r.name for r in with_hint] == ["하늘수학", "가온피아노"]


def test_default_sort_by_name_id(db_session):
    _seed(
        db_session,
        [
            Academy(name="나래", address="미사"),
            Academy(name="가온", address="미사"),
        ],
    )
    params = RecommendationRequest(limit=20)
    names = [r.name for r in academy_repository.list_candidates(db_session, params)]
    assert names == ["가온", "나래"]
