"""학원 특징 라벨 (주관적 언급 메타). academies 사실 컬럼과 분리.

리뷰·공개 문구에서 뽑은 닫힌 어휘만 담는다. scoring / curriculum_* 에 쓰지 않는다.
git 정본이 아니라 DB 직접 쓰기 (reviews 와 같은 예외 경로).
"""

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
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

from app.core.trait_labels import CLOSED_LABELS, SOURCE_TYPES, STATUSES, sql_in_list
from app.db.session import Base

# 손으로 쓴 사본을 두지 않는다 — 어휘 정본은 `app.core.trait_labels` 하나다.
_LABEL_IN = sql_in_list(CLOSED_LABELS)
_SOURCE_TYPE_IN = sql_in_list(SOURCE_TYPES)
_STATUS_IN = sql_in_list(STATUSES)


class AcademyTraitLabel(Base):
    """닫힌 특징 라벨 한 건. 기본 status=candidate.

    Dedup: ``(academy_id, label, source_url)``. ``source_url`` 이 없는 리뷰는
    적재 시 ``review:{id}`` 키를 넣어 재실행 idempotent 을 유지한다.
    """

    __tablename__ = "academy_trait_labels"
    __table_args__ = (
        UniqueConstraint(
            "academy_id",
            "label",
            "source_url",
            name="uq_academy_trait_labels_academy_id_label_source_url",
        ),
        CheckConstraint(f"label IN ({_LABEL_IN})", name="label"),
        CheckConstraint(f"source_type IN ({_SOURCE_TYPE_IN})", name="source_type"),
        CheckConstraint(f"status IN ({_STATUS_IN})", name="status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 단독 인덱스를 두지 않는다 — 위 유니크 제약의 선두 컬럼이 같은 조회를 커버한다.
    academy_id: Mapped[int] = mapped_column(ForeignKey("academies.id"), nullable=False)
    label: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # Dedup 키. 실제 URL 또는 review:{id} 센티널.
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    snippet: Mapped[str | None] = mapped_column(Text)
    observed_at: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="candidate"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
