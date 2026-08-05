"""새 모델(Review + engagement)의 SQLite 호환 라운드트립 테스트.

embedding 컬럼이 이중화(JSON.with_variant(Vector))되어 SQLite에서도 create_all/
삽입/조회가 동작하는지 검증한다.
"""

from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.academy import Academy
from app.models.engagement import ClickLog, Feedback, SearchHistory, Waitlist
from app.models.review import Review


def _make_academy(db_session) -> Academy:
    academy = Academy(name="테스트수학학원", address="하남시 미사강변대로 1")
    db_session.add(academy)
    db_session.commit()
    db_session.refresh(academy)
    return academy


def test_review_roundtrip_with_embedding(db_session):
    academy = _make_academy(db_session)
    embedding = [0.1, 0.2, 0.3]
    review = Review(
        academy_id=academy.id,
        content="내신 대비가 좋았습니다",
        source="맘카페",
        rating=5,
        embedding=embedding,
    )
    db_session.add(review)
    db_session.commit()
    db_session.refresh(review)

    assert review.id is not None
    assert review.academy_id == academy.id
    assert review.embedding == embedding
    assert review.created_at is not None


def test_review_roundtrip_with_source_url_and_published_at(db_session):
    academy = _make_academy(db_session)
    review = Review(
        academy_id=academy.id,
        content="미사 수학학원 후기입니다",
        source="naver_blog",
        source_url="https://blog.example/1",
        published_at=date(2026, 7, 31),
    )
    db_session.add(review)
    db_session.commit()
    db_session.refresh(review)

    assert review.source_url == "https://blog.example/1"
    assert review.published_at == date(2026, 7, 31)


def test_same_url_rejected_for_same_academy(db_session):
    academy = _make_academy(db_session)
    for _ in range(2):
        db_session.add(
            Review(
                academy_id=academy.id,
                content="같은 글",
                source_url="https://blog.example/dup",
            )
        )

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_same_url_allowed_across_academies(db_session):
    """블로그 글 1건이 두 학원을 언급할 수 있고, 그건 학원별로 유효한 근거다."""
    first = _make_academy(db_session)
    second = Academy(name="다른수학학원", address="하남시 미사강변대로 2")
    db_session.add(second)
    db_session.commit()

    for academy_id in (first.id, second.id):
        db_session.add(
            Review(
                academy_id=academy_id,
                content="두 학원을 비교한 글",
                source_url="https://blog.example/compare",
            )
        )
    db_session.commit()

    assert db_session.query(Review).count() == 2


def test_null_source_url_bypasses_unique_constraint(db_session):
    """수동 입력·AI 요약 리뷰는 원문 링크가 없다 — NULL 다중 허용이 의도된 동작이다."""
    academy = _make_academy(db_session)
    for _ in range(2):
        db_session.add(Review(academy_id=academy.id, content="수동 입력 요약"))
    db_session.commit()

    assert db_session.query(Review).count() == 2


def test_engagement_models_roundtrip(db_session):
    academy = _make_academy(db_session)

    db_session.add(SearchHistory(query="고2 내신 수학 숙제 적은 곳"))
    db_session.add(ClickLog(academy_id=academy.id, event="phone"))
    db_session.add(ClickLog(academy_id=None, event="detail"))  # academy_id nullable
    db_session.add(Feedback(rating="😀", comment="도움이 됐어요"))
    db_session.add(Waitlist(email="parent@example.com"))
    db_session.add(Waitlist(kakao="plus_friend_id"))
    db_session.commit()

    assert db_session.query(SearchHistory).count() == 1
    assert db_session.query(ClickLog).count() == 2
    assert db_session.query(Feedback).count() == 1
    assert db_session.query(Waitlist).count() == 2
