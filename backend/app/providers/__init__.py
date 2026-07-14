"""AI provider 추상화 계층 (포트 + 어댑터).

교체 가능성이 핵심이다. 서비스 계층은 구체 provider가 아니라 `base.py`의
Protocol에만 의존하고, 실제 구현은 config로 선택해 `factory.py`에서 주입받는다.
이번 단계의 기본 구현은 전부 stub이며, 실제 어댑터(OpenAI/bge-m3/pgvector)와
LlamaIndex 기반 RagEngine은 다음 단계에서 같은 포트 뒤에 추가한다.
"""

from app.providers.base import EmbeddingProvider, Hit, LLMProvider, VectorStore
from app.providers.factory import (
    get_embedding_provider,
    get_llm_provider,
    get_vector_store,
)

__all__ = [
    "EmbeddingProvider",
    "LLMProvider",
    "VectorStore",
    "Hit",
    "get_embedding_provider",
    "get_llm_provider",
    "get_vector_store",
]
