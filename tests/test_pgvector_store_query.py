"""`PgVectorStore.search()`의 쿼리 빌드가 예외 없이 동작하는지 검증하는 회귀 테스트.

`Review.embedding.cosine_distance(...)`는 `with_variant()`로 이중화된 컬럼에서
`AttributeError`를 낸다 (postgres dialect에서도 마찬가지 — `comparator_factory`가
원본 JSON 타입에 고정되기 때문). 이 오류는 표현식을 만드는 시점에 나므로 실제 DB
연결 없이도 재현/검증할 수 있다. `tests/test_pgvector_store.py`는 실 Postgres가
있을 때만 도는 통합 테스트라 이 버그를 기본 `pytest`에서 잡지 못했다 — 여기서는
가짜 세션으로 `search()`를 호출해 표현식 빌드 단계까지 DB 없이 검증한다.
"""

from app.providers.pgvector_store import PgVectorStore


class _FakeResult:
    def all(self):
        return []


class _FakeSession:
    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def execute(self, stmt):
        return _FakeResult()


def test_pgvector_store_search_builds_distance_expression_without_error():
    store = PgVectorStore(session_factory=lambda: _FakeSession())
    hits = store.search([0.1, 0.2, 0.3], top_k=5)
    assert hits == []
