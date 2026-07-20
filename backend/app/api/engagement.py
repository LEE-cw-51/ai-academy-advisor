"""engagement 쓰기 엔드포인트 (클릭 추적 / 피드백 / 대기자 등록).

학원 데이터의 정본은 git이지만(읽기 전용), 사용자 행동 데이터는 DB 직접 쓰기다
(docs/data-strategy.md). KPI(외부 행동률·대기자 등록률 등) 측정을 위한 엔드포인트.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.schemas.engagement import (
    ClickEventCreate,
    CreatedResponse,
    FeedbackCreate,
    WaitlistCreate,
)
from app.services import engagement_service

router = APIRouter(tags=["engagement"])


@router.post("/events", response_model=CreatedResponse, status_code=status.HTTP_201_CREATED)
def track_click(
    payload: ClickEventCreate,
    db: Annotated[Session, Depends(get_db)],
) -> CreatedResponse:
    if payload.academy_id is not None and not engagement_service.academy_exists(
        db, payload.academy_id
    ):
        raise HTTPException(status_code=404, detail="Academy not found")
    row = engagement_service.record_click(db, payload)
    return CreatedResponse.model_validate(row)


@router.post("/feedback", response_model=CreatedResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    payload: FeedbackCreate,
    db: Annotated[Session, Depends(get_db)],
) -> CreatedResponse:
    row = engagement_service.record_feedback(db, payload)
    return CreatedResponse.model_validate(row)


@router.post("/waitlist", response_model=CreatedResponse, status_code=status.HTTP_201_CREATED)
def join_waitlist(
    payload: WaitlistCreate,
    db: Annotated[Session, Depends(get_db)],
) -> CreatedResponse:
    row = engagement_service.register_waitlist(db, payload)
    return CreatedResponse.model_validate(row)
