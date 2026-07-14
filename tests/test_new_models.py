"""새 모델(Review + engagement)의 SQLite 호환 라운드트립 테스트.

embedding 컬럼이 이중화(JSON.with_variant(Vector))되어 SQLite에서도 create_all/
삽입/조회가 동작하는지 검증한다.
"""

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
