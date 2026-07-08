from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base

# SQLite(테스트)에서는 JSON, PostgreSQL(운영)에서는 JSONB로 저장된다.
SubjectsJSON = JSON().with_variant(postgresql.JSONB(), "postgresql")


class Academy(Base):
    """학원 사실(Fact) 레코드.

    Boolean 컬럼은 3상태를 가진다:
    True = 확인됨-있음, False = 확인됨-없음, NULL = 미확인.
    """

    __tablename__ = "academies"
    __table_args__ = (
        UniqueConstraint("name", "address", name="uq_academies_name_address"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 자연키 #1: 공식 학원 등록번호 (나이스 학원민원서비스 등)
    registration_number: Mapped[str | None] = mapped_column(String(50), unique=True)

    name: Mapped[str] = mapped_column(String(100), index=True)
    address: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(20))
    website_url: Mapped[str | None] = mapped_column(String(300))
    blog_url: Mapped[str | None] = mapped_column(String(300))
    instagram_url: Mapped[str | None] = mapped_column(String(300))

    # 과목 리스트 (예: ["수학"]). 표시 전용 — cross-dialect 필터 불가, 필터가 필요해지면 junction table로 이관.
    subjects: Mapped[list[str] | None] = mapped_column(SubjectsJSON)

    level_elementary: Mapped[bool | None] = mapped_column(Boolean)  # 초등부
    level_middle: Mapped[bool | None] = mapped_column(Boolean)  # 중등부
    level_high: Mapped[bool | None] = mapped_column(Boolean)  # 고등부

    class_small_group: Mapped[bool | None] = mapped_column(Boolean)  # 소수정예
    class_group: Mapped[bool | None] = mapped_column(Boolean)  # 그룹수업
    class_one_on_one: Mapped[bool | None] = mapped_column(Boolean)  # 1:1

    curriculum_seonhaeng: Mapped[bool | None] = mapped_column(Boolean)  # 선행
    curriculum_naesin: Mapped[bool | None] = mapped_column(Boolean)  # 내신
    curriculum_suneung: Mapped[bool | None] = mapped_column(Boolean)  # 수능

    shuttle_available: Mapped[bool | None] = mapped_column(Boolean)  # 차량운행

    tuition_monthly_fee: Mapped[int | None] = mapped_column(Integer)  # 월 수강료 (원)

    operating_hours: Mapped[str | None] = mapped_column(Text)  # 운영시간 (자유 서술)
    established_year: Mapped[int | None] = mapped_column(Integer)  # 개원년도
    teacher_count: Mapped[int | None] = mapped_column(Integer)  # 강사수
    classroom_count: Mapped[int | None] = mapped_column(Integer)  # 강의실수
    tagline: Mapped[str | None] = mapped_column(String(200))  # 한 줄 소개 (수동 큐레이션)

    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    source_note: Mapped[str | None] = mapped_column(Text)  # 출처 메모
    last_verified_at: Mapped[date | None] = mapped_column(Date)  # 최종 확인일

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
