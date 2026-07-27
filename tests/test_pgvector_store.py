"""`PgVectorStore` 통합 테스트.

`Review.embedding`의 pgvector `Vector` variant와 `cosine_distance()` 비교자는
PostgreSQL(+ pgvector extension)에서만 동작한다 (SQLite 테스트는 JSON variant를
쓰므로 대상이 아니다). 실제 Postgres가 필요하므로 기본 CI(SQLite 기반)에서는
`PGVECTOR_TEST_DATABASE_URL`이 없으면 스킵한다.

로컬에서 실행하려면:
    docker compose up -d db
    PGVECTOR_TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/ai_academy_advisor \
        uv run pytest tests/test_pgvector_store.py
"""

import os

import pytest
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker

pytestmark = pytest.mark.skipif(
    not os.getenv("PGVECTOR_TEST_DATABASE_URL"),
    reason="PGVECTOR_TEST_DATABASE_URL이 설정된 실제 Postgres(+pgvector)가 필요합니다",
)


@pytest.fixture()
def pg_session_factory():
    from app.db.session import Base
    from app.models.academy import Academy  # noqa: F401 (FK 대상, 메타데이터 등록용)
    from app.models.review import Review

    engine = create_engine(os.environ["PGVECTOR_TEST_DATABASE_URL"], future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, future=True)
    yield factory
    with factory() as db:
        db.execute(delete(Review))
        db.commit()
    engine.dispose()


def _make_academy(db) -> int:
    from app.models.academy import Academy

    academy = Academy(name="테스트 학원", address="서울시 강남구")
    db.add(academy)
    db.commit()
    db.refresh(academy)
    return academy.id


def test_pgvector_store_add_and_search_returns_nearest_first(pg_session_factory):
    from app.models.review import Review

    with pg_session_factory() as db:
        academy_id = _make_academy(db)
        reviews = [Review(academy_id=academy_id, content=f"리뷰 {i}") for i in range(3)]
        db.add_all(reviews)
        db.commit()
        review_ids = [r.id for r in reviews]

    from app.providers.pgvector_store import PgVectorStore

    store = PgVectorStore(session_factory=pg_session_factory)
    vectors = {
        review_ids[0]: [1.0, 0.0],
        review_ids[1]: [0.0, 1.0],
        review_ids[2]: [-1.0, 0.0],
    }
    store.add([(str(rid), vec) for rid, vec in vectors.items()])

    hits = store.search([1.0, 0.0], top_k=2)

    assert len(hits) == 2
    assert hits[0].id == str(review_ids[0])
    assert hits[0].score >= hits[1].score
