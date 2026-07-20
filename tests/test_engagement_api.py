"""engagement 쓰기 API (/events, /feedback, /waitlist) 테스트."""

from app.models.academy import Academy
from app.models.engagement import ClickLog, Feedback, Waitlist


def _seed_academy(db) -> Academy:
    academy = Academy(name="가온수학(예시)", address="경기도 하남시 미사강변대로 1")
    db.add(academy)
    db.commit()
    db.refresh(academy)
    return academy


def test_track_click_creates_log(client, db_session):
    academy = _seed_academy(db_session)
    response = client.post(
        "/events", json={"academy_id": academy.id, "event": "phone"}
    )
    assert response.status_code == 201
    body = response.json()
    assert "id" in body and "created_at" in body

    rows = db_session.query(ClickLog).all()
    assert len(rows) == 1
    assert rows[0].event == "phone"
    assert rows[0].academy_id == academy.id


def test_track_click_without_academy_id_allowed(client, db_session):
    response = client.post("/events", json={"event": "detail"})
    assert response.status_code == 201
    assert db_session.query(ClickLog).count() == 1


def test_track_click_invalid_event_returns_422(client):
    response = client.post("/events", json={"event": "share"})
    assert response.status_code == 422


def test_track_click_unknown_academy_returns_404(client, db_session):
    response = client.post("/events", json={"academy_id": 999, "event": "phone"})
    assert response.status_code == 404


def test_submit_feedback_creates_row(client, db_session):
    response = client.post("/feedback", json={"rating": "😀", "comment": "좋아요"})
    assert response.status_code == 201
    rows = db_session.query(Feedback).all()
    assert len(rows) == 1
    assert rows[0].rating == "😀"
    assert rows[0].comment == "좋아요"


def test_join_waitlist_with_email(client, db_session):
    response = client.post("/waitlist", json={"email": "parent@example.com"})
    assert response.status_code == 201
    rows = db_session.query(Waitlist).all()
    assert len(rows) == 1
    assert rows[0].email == "parent@example.com"
    assert rows[0].kakao is None


def test_join_waitlist_with_kakao(client, db_session):
    response = client.post("/waitlist", json={"kakao": "plus_friend"})
    assert response.status_code == 201
    assert db_session.query(Waitlist).count() == 1


def test_join_waitlist_requires_contact_returns_422(client):
    response = client.post("/waitlist", json={})
    assert response.status_code == 422


def test_join_waitlist_blank_contact_returns_422(client):
    response = client.post("/waitlist", json={"email": "  ", "kakao": ""})
    assert response.status_code == 422
