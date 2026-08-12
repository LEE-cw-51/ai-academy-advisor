"""engagement 쓰기 비즈니스 로직 (repository 얇은 래핑)."""

from sqlalchemy.orm import Session

from app.models.engagement import ClickLog, Feedback, Waitlist
from app.repositories import academy_repository, engagement_repository
from app.schemas.engagement import (
    ClickEventCreate,
    FeedbackCreate,
    WaitlistCreate,
)


def academy_exists(db: Session, academy_id: int) -> bool:
    return academy_repository.get_by_id(db, academy_id) is not None


def record_click(db: Session, payload: ClickEventCreate) -> ClickLog:
    return engagement_repository.create_click_log(
        db, event=payload.event.value, academy_id=payload.academy_id
    )


def record_feedback(db: Session, payload: FeedbackCreate) -> Feedback:
    return engagement_repository.create_feedback(
        db, rating=payload.rating, comment=payload.comment
    )


def register_waitlist(db: Session, payload: WaitlistCreate) -> Waitlist:
    # 스키마에서 이미 strip/lowercase 정규화됨.
    email = payload.email
    kakao = payload.kakao

    existing: Waitlist | None = None
    if email:
        existing = engagement_repository.find_waitlist_by_email(db, email)
    if existing is None and kakao:
        existing = engagement_repository.find_waitlist_by_kakao(db, kakao)

    if existing is not None:
        changed = False
        if email and not existing.email:
            existing.email = email
            changed = True
        if kakao and not existing.kakao:
            existing.kakao = kakao
            changed = True
        if changed:
            return engagement_repository.save_waitlist(db, existing)
        return existing

    return engagement_repository.create_waitlist(db, email=email, kakao=kakao)
