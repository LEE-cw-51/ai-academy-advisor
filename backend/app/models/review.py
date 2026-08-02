"""리뷰(Review) 모델.

학원 사실(Fact) 테이블과 달리 git 정본이 아닌 **DB 직접 쓰기** 대상이다
(docs/data-strategy.md Phase 2 AI 요약 / Phase 3 사용자 데이터).

`embedding` 컬럼은 기존 `academy.SubjectsJSON` 이중화 관례를 따른다:
PostgreSQL(운영)에서는 pgvector `Vector`, SQLite(테스트)에서는 JSON으로 저장된다.
차원은 config의 `embedding_dim`을 따르며 Vector(dim)과 일치해야 한다.
"""

from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import get_settings
from app.db.session import Base

EMBEDDING_DIM = get_settings().embedding_dim

# SQLite(테스트)에서는 JSON, PostgreSQL(운영)에서는 pgvector Vector로 저장된다.
EmbeddingVector = JSON().with_variant(Vector(EMBEDDING_DIM), "postgresql")


class Review(Base):
    """학원에 연결된 리뷰/요약 텍스트와 그 임베딩.

    `(academy_id, source_url)` 복합 유니크로 재수집 시 중복을 막는다. `academy_id`가
    키에 포함돼야 하는 이유: 블로그 글 1건이 두 학원을 언급할 수 있고, 그건 학원별로
    각각 유효한 근거이기 때문이다. `source_url`이 NULL인 행(수동 입력·AI 요약)은
    NULL끼리 서로 다르게 취급되어 제약을 우회하는데, 이는 의도된 동작이다.
    """

    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint(
            "academy_id", "source_url", name="uq_reviews_academy_id_source_url"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    academy_id: Mapped[int] = mapped_column(
        ForeignKey("academies.id"), nullable=False, index=True
    )
    # 임베딩 입력. 수집 경로에서는 제목+스니펫을 합친 문자열이 들어간다 (제목의 정보
    # 밀도가 높아서인데, UI가 렌더하지 않을 title 컬럼을 따로 두지는 않는다).
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(100))  # naver_blog / naver_cafearticle 등
    rating: Mapped[int | None] = mapped_column(Integer)  # 별점 (있을 경우)

    source_url: Mapped[str | None] = mapped_column(String(500))  # 원문 링크 (dedup 키)
    published_at: Mapped[date | None] = mapped_column(Date)  # 원문 작성일 (blog만 제공)

    embedding: Mapped[list[float] | None] = mapped_column(EmbeddingVector)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
