"""engagement 쓰기 API (/events, /feedback, /waitlist) 테스트."""

import pytest

from app.api.waitlist_rate_limit import reset_waitlist_rate_limit
from app.core.constants import ClickEvent
from app.models.academy import Academy
from app.models.engagement import ClickLog, Feedback, Waitlist


def _seed_academy(db) -> Academy:
    academy = Academy(name="가온수학(예시)", address="경기도 하남시 미사강변대로 1")
    db.add(academy)
    db.commit()
    db.refresh(academy)
    return academy


def test_track_click_creates_log(client, db_session):
    reset_waitlist_rate_limit()
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
    reset_waitlist_rate_limit()
    response = client.post("/events", json={"event": "detail"})
    assert response.status_code == 201
    assert db_session.query(ClickLog).count() == 1


def test_track_click_kakao_channel_event(client, db_session):
    reset_waitlist_rate_limit()
    response = client.post("/events", json={"event": "kakao_channel"})
    assert response.status_code == 201
    rows = db_session.query(ClickLog).all()
    assert len(rows) == 1
    assert rows[0].event == "kakao_channel"
    assert rows[0].academy_id is None


@pytest.mark.parametrize(
    "event",
    [
        # 2026-09-14 `/check`·`/checklists`·홈 상황 카드 퇴역으로 걷어낸 퍼널 이벤트.
        # 과거 click_logs 행은 남지만 새 요청은 받지 않는다.
        "mini_check_started",
        "mini_check_completed",
        "mini_check_result_viewed",
        "mini_check_home_clicked",
        "home_check_clicked",
        "checklist_kakao_clicked",
        "home_explore_selected",
        "explore_check_clicked",
        "check_explore_clicked",
    ],
)
def test_retired_landing_funnel_events_return_422(client, db_session, event):
    reset_waitlist_rate_limit()
    response = client.post("/events", json={"event": event})
    assert response.status_code == 422
    assert db_session.query(ClickLog).count() == 0


def test_track_click_invalid_event_returns_422(client):
    reset_waitlist_rate_limit()
    response = client.post("/events", json={"event": "share"})
    assert response.status_code == 422


def test_click_event_values_fit_string_50_column():
    for event in ClickEvent:
        assert len(event.value) <= 50


def test_track_click_unknown_academy_returns_404(client, db_session):
    reset_waitlist_rate_limit()
    response = client.post("/events", json={"academy_id": 999, "event": "phone"})
    assert response.status_code == 404


def test_submit_feedback_creates_row(client, db_session):
    reset_waitlist_rate_limit()
    response = client.post("/feedback", json={"rating": "😀", "comment": "좋아요"})
    assert response.status_code == 201
    rows = db_session.query(Feedback).all()
    assert len(rows) == 1
    assert rows[0].rating == "😀"
    assert rows[0].comment == "좋아요"


def test_join_waitlist_with_email(client, db_session):
    reset_waitlist_rate_limit()
    response = client.post("/waitlist", json={"email": "parent@example.com"})
    assert response.status_code == 201
    rows = db_session.query(Waitlist).all()
    assert len(rows) == 1
    assert rows[0].email == "parent@example.com"
    assert rows[0].kakao is None


def test_join_waitlist_with_kakao(client, db_session):
    reset_waitlist_rate_limit()
    response = client.post("/waitlist", json={"kakao": "plus_friend"})
    assert response.status_code == 201
    assert db_session.query(Waitlist).count() == 1


def test_join_waitlist_requires_contact_returns_422(client):
    reset_waitlist_rate_limit()
    response = client.post("/waitlist", json={})
    assert response.status_code == 422


def test_join_waitlist_blank_contact_returns_422(client):
    reset_waitlist_rate_limit()
    response = client.post("/waitlist", json={"email": "  ", "kakao": ""})
    assert response.status_code == 422


def test_join_waitlist_invalid_email_returns_422(client):
    reset_waitlist_rate_limit()
    response = client.post("/waitlist", json={"email": "not-an-email"})
    assert response.status_code == 422


def test_join_waitlist_duplicate_email_returns_same_row(client, db_session):
    reset_waitlist_rate_limit()
    first = client.post("/waitlist", json={"email": "Parent@Example.com"})
    second = client.post("/waitlist", json={"email": "parent@example.com"})
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert db_session.query(Waitlist).count() == 1
    assert db_session.query(Waitlist).one().email == "parent@example.com"


def test_join_waitlist_duplicate_merges_kakao(client, db_session):
    reset_waitlist_rate_limit()
    first = client.post("/waitlist", json={"email": "merge@example.com"})
    second = client.post(
        "/waitlist", json={"email": "merge@example.com", "kakao": "merge_kakao"}
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    row = db_session.query(Waitlist).one()
    assert row.email == "merge@example.com"
    assert row.kakao == "merge_kakao"


def test_join_waitlist_email_kakao_conflict_returns_409(client):
    reset_waitlist_rate_limit()
    first = client.post("/waitlist", json={"email": "conflict@example.com"})
    second = client.post("/waitlist", json={"kakao": "conflict_kakao"})
    conflict = client.post(
        "/waitlist",
        json={"email": "conflict@example.com", "kakao": "conflict_kakao"},
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert conflict.status_code == 409


def test_join_waitlist_rate_limited(client):
    reset_waitlist_rate_limit()
    for i in range(10):
        response = client.post("/waitlist", json={"email": f"rate{i}@example.com"})
        assert response.status_code == 201, response.text
    blocked = client.post("/waitlist", json={"email": "rate-overflow@example.com"})
    assert blocked.status_code == 429
    assert "너무 많습니다" in blocked.json()["detail"]


def test_events_rate_limited(client):
    reset_waitlist_rate_limit()
    for _ in range(10):
        response = client.post("/events", json={"event": "detail"})
        assert response.status_code == 201, response.text
    blocked = client.post("/events", json={"event": "detail"})
    assert blocked.status_code == 429


def test_feedback_rate_limited(client):
    reset_waitlist_rate_limit()
    for i in range(10):
        response = client.post(
            "/feedback", json={"rating": "😀", "comment": f"c{i}"}
        )
        assert response.status_code == 201, response.text
    blocked = client.post("/feedback", json={"rating": "😐", "comment": "overflow"})
    assert blocked.status_code == 429


def test_xff_rotation_does_not_bypass_rate_limit(client):
    """X-Forwarded-For 첫 hop은 클라이언트 조작 가능 — 신뢰하지 않는다."""
    reset_waitlist_rate_limit()
    for i in range(10):
        response = client.post(
            "/waitlist",
            json={"email": f"xff{i}@example.com"},
            headers={"X-Forwarded-For": f"203.0.113.{i}"},
        )
        assert response.status_code == 201, response.text
    blocked = client.post(
        "/waitlist",
        json={"email": "xff-overflow@example.com"},
        headers={"X-Forwarded-For": "198.51.100.1"},
    )
    assert blocked.status_code == 429
