"""리뷰(Review) 모델.

학원 사실(Fact) 테이블과 달리 git 정본이 아닌 **DB 직접 쓰기** 대상이다
(docs/data-strategy.md Phase 2 AI 요약 / Phase 3 사용자 데이터).

`embedding` 컬럼은 기존 `academy.SubjectsJSON` 이중화 관례를 따른다:
PostgreSQL(운영)에서는 pgvector `Vector`, SQLite(테스트)에서는 JSON으로 저장된다.
차원은 config의 `embedding_dim`을 따르며 Vector(dim)과 일치해야 한다.
"""

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import get_settings
from app.db.session import Base

EMBEDDING_DIM = get_settings().embedding_dim

# SQLite(테스트)에서는 JSON, PostgreSQL(운영)에서는 pgvector Vector로 저장된다.
EmbeddingVector = JSON().with_variant(Vector(EMBEDDING_DIM), "postgresql")


class Review(Base):
    """학원에 연결된 리뷰/요약 텍스트와 그 임베딩."""

    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    academy_id: Mapped[int] = mapped_column(
        ForeignKey("academies.id"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(100))  # 출처 (블로그/맘카페/AI요약 등)
    rating: Mapped[int | None] = mapped_column(Integer)  # 별점 (있을 경우)

    embedding: Mapped[list[float] | None] = mapped_column(EmbeddingVector)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
