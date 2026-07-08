from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.schemas.academy import (
    AcademySummary,
    RecommendationRequest,
    RecommendationResponse,
)
from app.services import recommendation_service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("", response_model=RecommendationResponse)
def recommend_academies(
    params: RecommendationRequest,
    db: Annotated[Session, Depends(get_db)],
) -> RecommendationResponse:
    items, total = recommendation_service.recommend(db, params)
    return RecommendationResponse(
        items=[AcademySummary.model_validate(item) for item in items],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )
