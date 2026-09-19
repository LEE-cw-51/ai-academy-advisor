"""engagement 로그 + 리뷰 조회 데이터 접근 계층."""

from datetime import datetime

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


def list_search_history(
    db: Session, since: datetime, until: datetime
) -> list[SearchHistory]:
    """[since, until) 구간의 질문 기록. 비식별 집계 리포트(app.cli.demand_report) 전용 읽기."""
    stmt = (
        select(SearchHistory)
        .where(SearchHistory.created_at >= since, SearchHistory.created_at < until)
        .order_by(SearchHistory.id)
    )
    return list(db.scalars(stmt).all())


def list_click_logs(db: Session, since: datetime, until: datetime) -> list[ClickLog]:
    """[since, until) 구간의 외부 행동 기록. 위와 같은 용도."""
    stmt = (
        select(ClickLog)
        .where(ClickLog.created_at >= since, ClickLog.created_at < until)
        .order_by(ClickLog.id)
    )
    return list(db.scalars(stmt).all())


def create_feedback(db: Session, rating: str, comment: str | None) -> Feedback:
    row = Feedback(rating=rating, comment=comment)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def find_waitlist_by_email(db: Session, email: str) -> Waitlist | None:
    return db.scalars(select(Waitlist).where(Waitlist.email == email)).first()


def find_waitlist_by_kakao(db: Session, kakao: str) -> Waitlist | None:
    return db.scalars(select(Waitlist).where(Waitlist.kakao == kakao)).first()


def create_waitlist(
    db: Session, email: str | None, kakao: str | None
) -> Waitlist:
    row = Waitlist(email=email, kakao=kakao)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def save_waitlist(db: Session, row: Waitlist) -> Waitlist:
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
