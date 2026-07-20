"""engagement 로그 + 리뷰 조회 데이터 접근 계층."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.engagement import ClickLog, Feedback, SearchHistory, Waitlist
from app.models.review import Review


def create_search_history(db: Session, query: str) -> SearchHistory:
    row = SearchHistory(query=query)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def create_click_log(
    db: Session, event: str, academy_id: int | None
) -> ClickLog:
    row = ClickLog(event=event, academy_id=academy_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def create_feedback(db: Session, rating: str, comment: str | None) -> Feedback:
    row = Feedback(rating=rating, comment=comment)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def create_waitlist(
    db: Session, email: str | None, kakao: str | None
) -> Waitlist:
    row = Waitlist(email=email, kakao=kakao)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_reviews_by_ids(db: Session, review_ids: list[int]) -> list[Review]:
    """RAG 근거용: id 목록으로 리뷰를 로드한다 (입력 순서 보존)."""
    if not review_ids:
        return []
    rows = db.scalars(select(Review).where(Review.id.in_(review_ids))).all()
    by_id = {row.id: row for row in rows}
    return [by_id[rid] for rid in review_ids if rid in by_id]
