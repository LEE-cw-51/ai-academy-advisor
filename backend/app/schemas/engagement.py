"""engagement(클릭/피드백/대기자) 쓰기 API의 요청/응답 스키마.

학원 사실 데이터와 달리 이 엔드포인트들은 DB 직접 쓰기다 (docs/data-strategy.md).
"""

from datetime import datetime
import re

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.constants import ClickEvent

# 가벼운 형식 검사 (email-validator 의존성 없이). 저장 전 lowercase 정규화.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ClickEventCreate(BaseModel):
    """외부 행동 클릭 추적 기록."""

    academy_id: int | None = Field(default=None, ge=1)
    event: ClickEvent


class FeedbackCreate(BaseModel):
    """완료 화면 만족도 피드백."""

    rating: str = Field(min_length=1, max_length=20)
    comment: str | None = Field(default=None, max_length=1000)


class WaitlistCreate(BaseModel):
    """정식 출시 알림 신청 (이메일 또는 카카오 중 최소 하나)."""

    email: str | None = Field(default=None, max_length=255)
    kakao: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def _normalize_and_require_contact(self) -> "WaitlistCreate":
        email = (self.email or "").strip().lower() or None
        kakao = (self.kakao or "").strip() or None
        if not email and not kakao:
            raise ValueError("email 또는 kakao 중 하나는 필요합니다")
        if email is not None and not _EMAIL_RE.match(email):
            raise ValueError("올바른 이메일 형식이 아닙니다")
        self.email = email
        self.kakao = kakao
        return self


class CreatedResponse(BaseModel):
    """쓰기 성공 확인 (공통)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
