"""리뷰 임베딩 백필: 길이 불일치·진행 없음 시 실패(쿼터 소진 루프 방지)."""

from sqlalchemy.orm import sessionmaker

from app.models.academy import Academy
from app.models.review import Review
from app.providers.pgvector_store import PgVectorStore
from app.services import review_embedding_service


class _PartialEmbedder:
    """행보다 하나 적은 벡터를 돌려 partial failure를 흉내낸다."""

    dimension = 4

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * self.dimension for _ in texts[:-1]]


class _FullEmbedder:
    dimension = 4

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[float(i + 1)] * self.dimension for i, _ in enumerate(texts)]


def _seed_reviews(db_session, n: int = 3) -> Academy:
    academy = Academy(name="가온수학", address="경기도 하남시 미사")
    db_session.add(academy)
    db_session.flush()
    for i in range(n):
        db_session.add(
            Review(
                academy_id=academy.id,
                content=f"후기 {i}",
                source="test",
                source_url=f"https://example.com/{i}",
                embedding=None,
            )
        )
    db_session.commit()
    return academy


def test_backfill_raises_on_vector_count_mismatch(db_session, db_engine, monkeypatch):
    _seed_reviews(db_session, n=3)
    factory = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    store = PgVectorStore(session_factory=factory)

    monkeypatch.setattr(
        review_embedding_service, "get_embedding_provider", lambda: _PartialEmbedder()
    )
    monkeypatch.setattr(review_embedding_service, "get_vector_store", lambda: store)

    missing_before = review_embedding_service.count_missing_embeddings(db_session)
    assert missing_before == 3

    try:
        review_embedding_service.backfill_missing_embeddings(db_session, batch_size=10)
        raised = False
    except ValueError as exc:
        raised = True
        assert "불일치" in str(exc)

    assert raised
    db_session.expire_all()
    assert review_embedding_service.count_missing_embeddings(db_session) == 3


def test_backfill_processes_all_when_lengths_match(db_session, db_engine, monkeypatch):
    _seed_reviews(db_session, n=3)
    factory = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    store = PgVectorStore(session_factory=factory)

    monkeypatch.setattr(
        review_embedding_service, "get_embedding_provider", lambda: _FullEmbedder()
    )
    monkeypatch.setattr(review_embedding_service, "get_vector_store", lambda: store)

    report = review_embedding_service.backfill_missing_embeddings(
        db_session, batch_size=10
    )

    assert report.processed == 3
    db_session.expire_all()
    assert review_embedding_service.count_missing_embeddings(db_session) == 0


def test_backfill_limit_stops_early_and_resumes(db_session, db_engine, monkeypatch):
    """비용을 먼저 확인하려 나눠 돌린다 — limit 에서 멈추고 재실행이 이어받는다.

    HuggingFace 는 토큰이 아니라 CPU 시간으로 과금해서 전체 비용을 사전에 계산할 수
    없다. 소량을 돌려 실제 소모액을 본 뒤 나머지를 잇는 경로가 필요하다.
    """
    _seed_reviews(db_session, n=5)
    factory = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    store = PgVectorStore(session_factory=factory)

    monkeypatch.setattr(
        review_embedding_service, "get_embedding_provider", lambda: _FullEmbedder()
    )
    monkeypatch.setattr(review_embedding_service, "get_vector_store", lambda: store)

    first = review_embedding_service.backfill_missing_embeddings(
        db_session, batch_size=2, limit=3
    )
    assert first.processed == 3
    db_session.expire_all()
    assert review_embedding_service.count_missing_embeddings(db_session) == 2

    second = review_embedding_service.backfill_missing_embeddings(
        db_session, batch_size=2
    )
    assert second.processed == 2
    db_session.expire_all()
    assert review_embedding_service.count_missing_embeddings(db_session) == 0


def test_backfill_raises_when_store_makes_no_progress(db_session, db_engine, monkeypatch):
    _seed_reviews(db_session, n=2)
    factory = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)

    class _NoopStore(PgVectorStore):
        def add(self, items: list[tuple[str, list[float]]]) -> None:
            return  # UPDATE 없이 반환 → missing 유지

    store = _NoopStore(session_factory=factory)
    monkeypatch.setattr(
        review_embedding_service, "get_embedding_provider", lambda: _FullEmbedder()
    )
    monkeypatch.setattr(review_embedding_service, "get_vector_store", lambda: store)

    try:
        review_embedding_service.backfill_missing_embeddings(db_session, batch_size=10)
        raised = False
    except ValueError as exc:
        raised = True
        assert "진행 없음" in str(exc)

    assert raised
    assert review_embedding_service.count_missing_embeddings(db_session) == 2
