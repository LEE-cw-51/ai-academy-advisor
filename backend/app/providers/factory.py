"""config 기반 provider 선택 팩토리.

`core.config.get_settings`의 `@lru_cache` 팩토리 관례를 따른다. provider 이름과
구현을 여기서만 매핑하므로, 새 어댑터 추가/교체는 이 파일과 config만 건드리면 된다.
"""

from functools import lru_cache

from app.core.config import get_settings
from app.providers.base import EmbeddingProvider, LLMProvider, VectorStore
from app.providers.groq import GroqLLMProvider
from app.providers.stub import (
    StubEmbeddingProvider,
    StubLLMProvider,
    StubVectorStore,
)


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    name = settings.embedding_provider
    if name == "stub":
        return StubEmbeddingProvider(dim=settings.embedding_dim)
    # 다음 단계에서 추가: "openai"(text-embedding-3-*), "bge-m3"(local HF).
    raise ValueError(
        f"지원하지 않는 embedding_provider: {name!r} (현재 'stub'만 구현됨)"
    )


@lru_cache
def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    name = settings.llm_provider
    if name == "stub":
        return StubLLMProvider()
    if name == "groq":
        return GroqLLMProvider(
            api_key=settings.groq_api_key,
            model=settings.llm_model,
            base_url=settings.groq_base_url,
        )
    # 다음 단계에서 추가: "openai"(gpt-4o-mini 등).
    raise ValueError(
        f"지원하지 않는 llm_provider: {name!r} (현재 'stub'/'groq'만 구현됨)"
    )


@lru_cache
def get_vector_store() -> VectorStore:
    settings = get_settings()
    name = settings.vector_store
    if name == "stub":
        return StubVectorStore()
    # 다음 단계에서 추가: "pgvector"(Review.embedding 기반 ANN 검색).
    raise ValueError(f"지원하지 않는 vector_store: {name!r} (현재 'stub'만 구현됨)")
