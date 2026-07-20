"""사용자 행동/참여(engagement) 로그 모델.

기획안 §11의 SearchHistory / ClickLog / Feedback / Waitlist. KPI(외부 행동률,
대기자 등록률 등) 측정을 위한 런타임 로그이며 git 정본이 아닌 DB 직접 쓰기다.
"""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class SearchHistory(Base):
    """사용자가 입력한 자연어 질문 기록."""

    __tablename__ = "search_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ClickLog(Base):
    """외부 행동 클릭 추적 (전화/홈페이지/길찾기/상세보기)."""

    __tablename__ = "click_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    academy_id: Mapped[int | None] = mapped_column(
        ForeignKey("academies.id"), index=True
    )
    event: Mapped[str] = mapped_column(String(50), nullable=False)  # phone/website/directions/detail
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Feedback(Base):
    """완료 화면의 만족도 피드백 (😀/😐/☹️)."""

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rating: Mapped[str] = mapped_column(String(20), nullable=False)  # 만족도 라벨
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Waitlist(Base):
    """정식 출시 알림 신청 (이메일 또는 카카오)."""

    __tablename__ = "waitlist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str | None] = mapped_column(String(255))
    kakao: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
