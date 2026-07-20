"""자연어 AI 추천(POST /recommendations/ai) 요청/응답 스키마."""

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.academy import AcademySummary


class AiRecommendationRequest(BaseModel):
    """자연어 질문 1건. 예: "고2 이과 내신 위주, 숙제 적은 미사 수학학원"."""

    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=3, ge=1, le=10)


class ReviewEvidence(BaseModel):
    """추천 근거로 제시되는 리뷰 발췌."""

    model_config = ConfigDict(from_attributes=True)

    content: str
    source: str | None
    rating: int | None


class AiRecommendationItem(BaseModel):
    """추천 학원 1건 + 추천 이유·점수·근거 리뷰."""

    academy: AcademySummary
    reason: str  # AI가 생성한 추천 이유
    score: float  # 추천 점수 (높을수록 적합)
    evidence_reviews: list[ReviewEvidence]  # 근거 리뷰 (없으면 빈 배열)


class AiRecommendationResponse(BaseModel):
    """추천 결과. `parsed_intent`로 질문 해석 결과를 투명하게 노출한다."""

    query: str
    parsed_intent: dict
    items: list[AiRecommendationItem]
