"""provider 추상화 골격 테스트 (기본 stub 구현)."""

from app.providers.base import EmbeddingProvider, Hit, LLMProvider, VectorStore
from app.providers.factory import (
    get_embedding_provider,
    get_llm_provider,
    get_vector_store,
)
from app.providers.stub import (
    StubEmbeddingProvider,
    StubLLMProvider,
    StubVectorStore,
)


def test_factory_returns_stub_by_default():
    # 기본 config는 전부 stub이며 Protocol을 만족한다.
    embedder = get_embedding_provider()
    llm = get_llm_provider()
    store = get_vector_store()

    assert isinstance(embedder, StubEmbeddingProvider)
    assert isinstance(llm, StubLLMProvider)
    assert isinstance(store, StubVectorStore)
    assert isinstance(embedder, EmbeddingProvider)
    assert isinstance(llm, LLMProvider)
    assert isinstance(store, VectorStore)


def test_stub_embedding_is_deterministic_and_correct_dim():
    embedder = StubEmbeddingProvider(dim=16)
    a1 = embedder.embed(["고1 내신 수학"])
    a2 = embedder.embed(["고1 내신 수학"])
    b = embedder.embed(["숙제 적은 학원"])

    assert len(a1) == 1
    assert len(a1[0]) == embedder.dimension == 16
    assert a1 == a2  # 같은 입력 → 같은 벡터
    assert a1[0] != b[0]  # 다른 입력 → 다른 벡터


def test_factory_embedding_dim_matches_settings():
    # 기본 embedding_dim(1024)이 팩토리 산출물에 반영된다.
    embedder = get_embedding_provider()
    assert embedder.dimension == 1024


def test_stub_llm_returns_str_echoing_last_user_message():
    llm = StubLLMProvider()
    out = llm.chat(
        [
            {"role": "system", "content": "너는 학원 추천 도우미"},
            {"role": "user", "content": "숙제 적은 수학학원"},
        ]
    )
    assert isinstance(out, str)
    assert "숙제 적은 수학학원" in out


def test_stub_vector_store_returns_nearest_first():
    embedder = StubEmbeddingProvider(dim=32)
    store = StubVectorStore()

    texts = ["내신 관리 학원", "숙제 많은 학원", "1:1 과외"]
    vectors = embedder.embed(texts)
    store.add([(str(i), vec) for i, vec in enumerate(vectors)])

    # 첫 텍스트와 동일한 질의 → 그 자신이 top-1(코사인 유사도 1.0에 근접)
    query = embedder.embed(["내신 관리 학원"])[0]
    hits = store.search(query, top_k=2)

    assert len(hits) == 2
    assert all(isinstance(h, Hit) for h in hits)
    assert hits[0].id == "0"
    assert hits[0].score >= hits[1].score
