"""PgVectorStore 테스트.

`add()`는 dialect-agnostic한 plain UPDATE라 SQLite 픽스처로 실제 실행해 검증한다.
`search()`의 `<=>` 코사인 거리는 Postgres 전용 연산자라 SQLite에서 실행할 수 없으므로,
쿼리 형태(컴파일 결과)와 score 변환 로직만 DB 연결 없이 단위 검증하고, 실제 검색
결과 검증은 opt-in 통합 테스트(PGVECTOR_TEST_DATABASE_URL 설정 시에만)로 분리한다.
"""

import os

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import sessionmaker

from app.models.academy import Academy
from app.models.review import Review
from app.providers.pgvector_store import PgVectorStore


def test_pgvector_store_add_updates_embedding_column(db_engine, db_session):
    academy = Academy(name="가온수학(예시)", address="경기도 하남시 미사대로 1")
    db_session.add(academy)
    db_session.commit()
    review = Review(academy_id=academy.id, content="내신 대비가 좋았습니다", source="맘카페")
    db_session.add(review)
    db_session.commit()
    db_session.refresh(review)

    factory = sessionmaker(bind=db_engine, autoflush=False, autocommit=False, future=True)
    store = PgVectorStore(session_factory=factory)
    store.add([(str(review.id), [0.1, 0.2, 0.3, 0.4])])

    db_session.refresh(review)
    assert review.embedding == [0.1, 0.2, 0.3, 0.4]


def test_pgvector_store_add_empty_items_is_noop(db_engine):
    factory = sessionmaker(bind=db_engine, autoflush=False, autocommit=False, future=True)
    store = PgVectorStore(session_factory=factory)
    store.add([])  # 세션을 열지도 않고 조용히 반환 — 에러 없음


def test_pgvector_store_search_statement_uses_cosine_distance_and_limit():
    stmt = PgVectorStore._build_search_statement([0.1, 0.2, 0.3], top_k=5)
    compiled = str(stmt.compile(dialect=postgresql.dialect()))
    assert "<=>" in compiled
    assert "IS NOT NULL" in compiled
    assert "ORDER BY" in compiled
    assert "LIMIT" in compiled


def test_pgvector_store_to_hit_converts_distance_to_similarity_score():
    hit = PgVectorStore._to_hit(review_id=7, distance=0.2)
    assert hit.id == "7"
    assert hit.score == pytest.approx(0.8)


@pytest.mark.skipif(
    not os.getenv("PGVECTOR_TEST_DATABASE_URL"),
    reason="실제 Postgres+pgvector 인스턴스가 필요한 opt-in 통합 테스트",
)
def test_pgvector_store_search_against_real_postgres():
    from sqlalchemy import create_engine

    from app.db.session import Base

    engine = create_engine(os.environ["PGVECTOR_TEST_DATABASE_URL"], future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = factory()
    try:
        academy = Academy(name="가온수학(예시)", address="경기도 하남시 미사대로 1")
        session.add(academy)
        session.commit()

        near = Review(academy_id=academy.id, content="근접 리뷰")
        far = Review(academy_id=academy.id, content="먼 리뷰")
        session.add_all([near, far])
        session.commit()
        session.refresh(near)
        session.refresh(far)

        store = PgVectorStore(session_factory=factory)
        store.add(
            [
                (str(near.id), [1.0, 0.0, 0.0, 0.0]),
                (str(far.id), [0.0, 1.0, 0.0, 0.0]),
            ]
        )

        hits = store.search([1.0, 0.0, 0.0, 0.0], top_k=2)

        assert [hit.id for hit in hits] == [str(near.id), str(far.id)]
        assert hits[0].score > hits[1].score
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
