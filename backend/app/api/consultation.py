"""맞춤 상담 질문 API."""

from fastapi import APIRouter, status

from app.schemas.consultation import ConsultationRequest, ConsultationResponse
from app.services import consultation_service

router = APIRouter(tags=["consultation"])


@router.post(
    "/consultation/questions",
    response_model=ConsultationResponse,
    status_code=status.HTTP_200_OK,
)
def create_consultation_questions(payload: ConsultationRequest) -> ConsultationResponse:
    return consultation_service.generate_questions(payload)
