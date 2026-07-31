"""recommendation_pipeline.build_context 단위 테스트."""

from app.models.academy import Academy
from app.models.engagement import SearchHistory
from app.schemas.academy import AcademySummary
from app.services.recommendation_pipeline import build_context


def _seed(db, rows: list[Academy]) -> list[Academy]:
    db.add_all(rows)
    db.commit()
    for row in rows:
        db.refresh(row)
    return rows


def test_academies_by_id_are_pydantic_and_survive_session_close(db_session):
    """P2 스트리밍 전제: 세션 close 후에도 AcademySummary 속성 접근이 된다."""
    _seed(
        db_session,
        [Academy(name="가온수학", address="경기도 하남시 미사대로 1")],
    )
    ctx = build_context(db_session, "미사 수학학원", limit=3)
    db_session.close()

    assert ctx.academies_by_id
    for academy in ctx.academies_by_id.values():
        assert isinstance(academy, AcademySummary)
        assert academy.name  # DetachedInstanceError 없이 접근


def test_search_history_recorded_once_even_with_relaxation(db_session):
    _seed(
        db_session,
        [Academy(name="가온수학", address="경기도 하남시 미사대로 1")],
    )
    # 분당은 데이터에 없어 region 완화 2단까지 간다
    build_context(db_session, "분당 수학학원", limit=3)
    rows = db_session.query(SearchHistory).all()
    assert len(rows) == 1
    assert rows[0].query == "분당 수학학원"


def test_q_relaxation_via_prev_filters(db_session):
    """parse_intent 는 q 를 안 넣으므로 prev_filters 로만 q 단계에 도달한다."""
    _seed(
        db_session,
        [Academy(name="가온수학", address="경기도 하남시 미사대로 1")],
    )
    ctx = build_context(
        db_session,
        "미사 수학학원",
        prev_filters={"q": "존재하지않는토큰XYZ"},
        limit=3,
    )
    assert ctx.relaxed == ["q"]
    assert ctx.scored  # q 제거 후 풀 확보


def test_scoring_uses_original_request_after_region_relax(db_session):
    """region 을 풀어도 채점은 원본 req 라 모든 항목 conflicts 에 region 이 남는다."""
    _seed(
        db_session,
        [Academy(name="가온수학", address="경기도 하남시 미사대로 1")],
    )
    ctx = build_context(db_session, "분당 수학학원", limit=3)
    assert ctx.relaxed == ["region"]
    assert ctx.request.region == "분당"
    assert all("region" in s.conflicts for s in ctx.scored)


def test_prev_filters_overridden_by_new_query(db_session):
    _seed(
        db_session,
        [
            Academy(name="가온수학", address="경기도 하남시 미사대로 1"),
            Academy(name="강남수학", address="서울시 강남구 1"),
        ],
    )
    ctx = build_context(
        db_session,
        "미사 수학학원",
        prev_filters={"region": "강남"},
        limit=3,
    )
    assert ctx.request.region == "미사"
    names = [
        ctx.academies_by_id[s.academy_id].name for s in ctx.scored
    ]
    assert names == ["가온수학"]
