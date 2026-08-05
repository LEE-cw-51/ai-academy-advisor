"""Provider 포트(Protocol) 정의.

여기 정의된 인터페이스만이 서비스 계층과의 계약이다. 구현체(stub, 향후 OpenAI/
bge-m3/pgvector 등)는 이 시그니처를 만족하기만 하면 config 변경만으로 교체된다.
"""

from dataclasses import dataclass
from datetime import date
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class Hit:
    """벡터 검색 결과 1건. `id`는 저장 시 부여한 식별자, `score`는 유사도(클수록 유사)."""

    id: str
    score: float


@dataclass(frozen=True)
class ReviewItem:
    """리뷰 소스에서 가져온 공개 게시물 1건.

    `content`는 네이버 검색 API `description`의 스니펫(~200자)이지 **리뷰 전문이 아니다** —
    전문을 얻으려면 별도 크롤링이 필요하고 그 순간 공식 API를 쓴 법적 근거가 사라진다
    (docs/decision-log.md 2026-07-31). HTML 태그·엔티티는 제거된 상태로 들어온다.

    `published_at`은 `blog`만 제공한다. `cafearticle` 응답에는 날짜 필드가 없어
    `None`이 정상이며 결측이 아니다.
    """

    title: str
    content: str
    url: str
    source: str  # "naver_blog" | "naver_cafearticle" | "stub"
    published_at: date | None


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


@runtime_checkable
class ReviewSource(Protocol):
    """공개 게시물 검색소. 학원명 등의 질의로 리뷰 스니펫을 가져온다."""

    def search(self, query: str, limit: int = 10) -> list[ReviewItem]:
        """`query`와 관련된 공개 게시물을 최대 `limit`건 반환한다.

        검색어 매칭은 소스가 알아서 하며 정확도를 보장하지 않는다 — 학원 귀속 판정은
        호출부(`review_ingest_service`)의 이름 사후필터 책임이다.
        """
        ...
