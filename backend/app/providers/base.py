"""Provider 포트(Protocol) 정의.

여기 정의된 인터페이스만이 서비스 계층과의 계약이다. 구현체(stub, 향후 OpenAI/
bge-m3/pgvector 등)는 이 시그니처를 만족하기만 하면 config 변경만으로 교체된다.
"""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class Hit:
    """벡터 검색 결과 1건. `id`는 저장 시 부여한 식별자, `score`는 유사도(클수록 유사)."""

    id: str
    score: float


@runtime_checkable
class EmbeddingProvider(Protocol):
    """텍스트를 고정 차원 벡터로 임베딩한다."""

    @property
    def dimension(self) -> int:
        """임베딩 벡터의 차원 수. 벡터 컬럼(Vector(dim))과 일치해야 한다."""
        ...

    def embed(self, texts: list[str]) -> list[list[float]]:
        """여러 텍스트를 각각 `dimension` 길이의 벡터로 변환한다."""
        ...


@runtime_checkable
class LLMProvider(Protocol):
    """대화형 LLM. 메시지 목록을 받아 문자열 응답을 생성한다."""

    def chat(self, messages: list[dict]) -> str:
        """`messages`는 OpenAI 형식(`{"role", "content"}`)이지만 provider 무관하게 해석된다."""
        ...


@runtime_checkable
class VectorStore(Protocol):
    """임베딩 벡터의 저장/검색소."""

    def add(self, items: list[tuple[str, list[float]]]) -> None:
        """`(id, embedding)` 쌍들을 저장한다."""
        ...

    def search(self, embedding: list[float], top_k: int) -> list[Hit]:
        """질의 벡터와 가장 유사한 상위 `top_k`건을 유사도 내림차순으로 반환한다."""
        ...
