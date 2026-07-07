from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.schemas.academy import (
    AcademyDetail,
    AcademyListParams,
    AcademyListResponse,
    AcademySummary,
)
from app.services import academy_service

router = APIRouter(prefix="/academies", tags=["academies"])


@router.get("", response_model=AcademyListResponse)
def list_academies(
    params: Annotated[AcademyListParams, Query()],
    db: Annotated[Session, Depends(get_db)],
) -> AcademyListResponse:
    items, total = academy_service.list_academies(db, params)
    return AcademyListResponse(
        items=[AcademySummary.model_validate(item) for item in items],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@router.get("/{academy_id}", response_model=AcademyDetail)
def get_academy(
    academy_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> AcademyDetail:
    academy = academy_service.get_academy(db, academy_id)
    if academy is None:
        raise HTTPException(status_code=404, detail="Academy not found")
    return AcademyDetail.model_validate(academy)
