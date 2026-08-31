from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConsultationQuestion(BaseModel):
    topic: str = Field(min_length=1, max_length=40)
    prompt: str = Field(min_length=1, max_length=300)


class ConsultationRequest(BaseModel):
    """학부모 입력. 학원 추천이 아니라 상담에서 읽을 질문을 만들기 위한 맥락이다."""

    model_config = ConfigDict(extra="forbid")

    grade: str = Field(min_length=1, max_length=20)
    subject: str = Field(min_length=1, max_length=20)
    school: str = Field(default="", max_length=50)
    current_academy: str = Field(default="", max_length=100)
    style_tags: list[str] = Field(default_factory=list, max_length=8)
    concern: str = Field(min_length=1, max_length=500)
    intent: Literal["counsel_only", "find_new_academy"] = "counsel_only"

    @field_validator(
        "grade", "subject", "school", "current_academy", "concern", mode="before"
    )
    @classmethod
    def _strip_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("style_tags")
    @classmethod
    def _trim_tags(cls, value: list[str]) -> list[str]:
        # 다른 텍스트 필드처럼 max_length를 리스트 타입에 직접 걸 수 없어 (per-item
        # 제약이라) 여기서 잘라낸다 — 안 그러면 임의 길이 문자열이 그대로 LLM
        # 프롬프트에 들어간다.
        return [item.strip()[:20] for item in value if item.strip()]


class ConsultationResponse(BaseModel):
    questions: list[ConsultationQuestion] = Field(min_length=1, max_length=5)
    disclaimer: str
    model: str
    used_fallback: bool = False
