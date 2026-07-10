from sqlalchemy.orm import Session

from app.models.academy import Academy
from app.repositories import academy_repository
from app.schemas.academy import RecommendationRequest


def recommend(db: Session, params: RecommendationRequest) -> tuple[list[Academy], int]:
    return academy_repository.list_recommendations(db, params)
