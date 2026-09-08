"""recommendation_pipeline.build_context 단위 테스트."""

import pytest

from app.models.academy import Academy
from app.models.engagement import SearchHistory
from app.providers.base import Hit
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


class _ExplodingVectorStore:
    """pgvector 장애 시뮬레이션 — search가 항상 실패한다."""

    def search(self, query_embedding, top_k=5):
        raise RuntimeError("pgvector unavailable")


class _StubVectorStore:
    """항상 review id 1 을 히트로 돌려주는 정상 벡터 스토어."""

    def search(self, query_embedding, top_k=5):
        return [Hit(id="1", score=0.9)]


def test_build_context_does_not_swallow_review_lookup_errors(
    db_session, monkeypatch
):
    """폴백 범위는 임베딩·벡터 검색뿐이다.

    리뷰 본문 조회(요청 세션 DB)나 스키마 검증이 깨지면 '근거 없음'으로 위장하지
    말고 터져야 한다 — 아니면 스키마 드리프트가 WARNING 한 줄만 남기고 전 사용자에게
    영구히 빈 evidence 를 내보낸다.
    """
    _seed(
        db_session,
        [Academy(name="가온수학", address="경기도 하남시 미사대로 1")],
    )
    monkeypatch.setattr(
        "app.services.recommendation_pipeline.get_vector_store",
        lambda db=None: _StubVectorStore(),
    )

    def _boom(db, ids):
        raise RuntimeError("connection reset by pooler")

    monkeypatch.setattr(
        "app.services.recommendation_pipeline"
        ".engagement_repository.get_reviews_by_ids",
        _boom,
    )
    with pytest.raises(RuntimeError, match="connection reset by pooler"):
        build_context(db_session, "미사 수학학원", limit=3)


def test_build_context_keeps_candidates_when_vector_search_fails(
    db_session, monkeypatch
):
    """벡터 검색이 죽어도 학원 사실 후보는 남고 근거만 비운다."""
    _seed(
        db_session,
        [Academy(name="가온수학", address="경기도 하남시 미사대로 1")],
    )
    monkeypatch.setattr(
        "app.services.recommendation_pipeline.get_vector_store",
        lambda db=None: _ExplodingVectorStore(),
    )
    ctx = build_context(db_session, "미사 수학학원", limit=3)
    assert ctx.scored
    assert ctx.academies_by_id
    assert ctx.evidence_by_academy == {}
    rows = db_session.query(SearchHistory).all()
    assert len(rows) == 1
    assert rows[0].query == "미사 수학학원"


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
