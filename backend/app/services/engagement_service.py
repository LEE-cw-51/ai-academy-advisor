"""engagement 쓰기 비즈니스 로직 (repository 얇은 래핑)."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.engagement import ClickLog, Feedback, Waitlist
from app.repositories import academy_repository, engagement_repository
from app.schemas.engagement import (
    ClickEventCreate,
    FeedbackCreate,
    WaitlistCreate,
)


class WaitlistConflictError(Exception):
    """동일 요청에서 email/kakao가 서로 다른 대기자 행을 가리킬 때 충돌."""


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

    email_existing = (
        engagement_repository.find_waitlist_by_email(db, email) if email else None
    )
    kakao_existing = (
        engagement_repository.find_waitlist_by_kakao(db, kakao) if kakao else None
    )

    if (
        email_existing is not None
        and kakao_existing is not None
        and email_existing.id != kakao_existing.id
    ):
        raise WaitlistConflictError("Email and kakao belong to different waitlist rows")

    existing = email_existing or kakao_existing
    if existing is not None:
        changed = False
        if email and not existing.email:
            existing.email = email
            changed = True
        if kakao and not existing.kakao:
            existing.kakao = kakao
            changed = True
        if changed:
            try:
                return engagement_repository.save_waitlist(db, existing)
            except IntegrityError:
                db.rollback()
                email_existing = (
                    engagement_repository.find_waitlist_by_email(db, email)
                    if email
                    else None
                )
                kakao_existing = (
                    engagement_repository.find_waitlist_by_kakao(db, kakao)
                    if kakao
                    else None
                )
                if (
                    email_existing is not None
                    and kakao_existing is not None
                    and email_existing.id != kakao_existing.id
                ):
                    raise WaitlistConflictError(
                        "Email and kakao belong to different waitlist rows"
                    ) from None
                resolved = email_existing or kakao_existing
                if resolved is not None:
                    return resolved
                raise WaitlistConflictError("Waitlist conflict detected") from None
        return existing

    try:
        return engagement_repository.create_waitlist(db, email=email, kakao=kakao)
    except IntegrityError:
        db.rollback()
        email_existing = (
            engagement_repository.find_waitlist_by_email(db, email) if email else None
        )
        kakao_existing = (
            engagement_repository.find_waitlist_by_kakao(db, kakao) if kakao else None
        )
        if (
            email_existing is not None
            and kakao_existing is not None
            and email_existing.id != kakao_existing.id
        ):
            raise WaitlistConflictError(
                "Email and kakao belong to different waitlist rows"
            ) from None
        resolved = email_existing or kakao_existing
        if resolved is not None:
            return resolved
        raise WaitlistConflictError("Waitlist conflict detected") from None
