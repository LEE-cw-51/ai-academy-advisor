from datetime import date

from app.models.academy import Academy


def seed_academies(db) -> list[Academy]:
    """필터 매트릭스: True / False / NULL 3상태가 모두 등장하도록 구성."""
    rows = [
        Academy(
            name="가온수학(예시)",
            address="경기도 하남시 미사강변대로 1",
            phone="031-000-0101",
            subjects=["수학"],
            level_middle=False,
            level_high=True,
            class_small_group=True,
            curriculum_naesin=True,
            shuttle_available=True,
            tagline="고등 내신 전문(예시)",
            last_verified_at=date(2026, 7, 1),
        ),
        Academy(
            name="나래수학(예시)",
            address="경기도 하남시 미사대로 2",
            subjects=["수학"],
            level_middle=True,
            level_high=False,
            class_group=True,
            curriculum_naesin=True,
            curriculum_suneung=False,
            shuttle_available=False,
        ),
        Academy(
            name="다온수학(예시)",
            address="경기도 하남시 망월동 3",
            subjects=["수학"],
            level_middle=True,
            level_high=None,
            class_one_on_one=True,
            curriculum_suneung=True,
            shuttle_available=None,
        ),
    ]
    db.add_all(rows)
    db.commit()
    return rows


def names(response) -> list[str]:
    return [item["name"] for item in response.json()["items"]]


def test_list_empty(client):
    response = client.get("/academies")
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "limit": 20, "offset": 0}


def test_list_returns_all_sorted_by_name(client, db_session):
    seed_academies(db_session)
    response = client.get("/academies")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert names(response) == ["가온수학(예시)", "나래수학(예시)", "다온수학(예시)"]


def test_filter_level_high_excludes_false_and_null(client, db_session):
    seed_academies(db_session)
    response = client.get("/academies", params={"level": "high"})
    # 나래는 False(확인됨-없음), 다온은 NULL(미확인) — 둘 다 제외되어야 한다.
    assert names(response) == ["가온수학(예시)"]
    assert response.json()["total"] == 1


def test_filter_class_type(client, db_session):
    seed_academies(db_session)
    response = client.get("/academies", params={"class_type": "one_on_one"})
    assert names(response) == ["다온수학(예시)"]


def test_filter_curriculum(client, db_session):
    seed_academies(db_session)
    response = client.get("/academies", params={"curriculum": "naesin"})
    assert names(response) == ["가온수학(예시)", "나래수학(예시)"]


def test_filter_shuttle_false_means_confirmed_no(client, db_session):
    seed_academies(db_session)
    response = client.get("/academies", params={"shuttle": "false"})
    # NULL(다온)은 '미확인'이므로 '차량 없음 확인' 결과에 포함되면 안 된다.
    assert names(response) == ["나래수학(예시)"]


def test_filters_combine_with_and(client, db_session):
    seed_academies(db_session)
    response = client.get(
        "/academies", params={"level": "middle", "curriculum": "naesin"}
    )
    assert names(response) == ["나래수학(예시)"]


def test_q_matches_name_and_address(client, db_session):
    seed_academies(db_session)
    by_name = client.get("/academies", params={"q": "나래"})
    assert names(by_name) == ["나래수학(예시)"]
    by_address = client.get("/academies", params={"q": "망월"})
    assert names(by_address) == ["다온수학(예시)"]


def test_pagination_limit_offset_total(client, db_session):
    seed_academies(db_session)
    response = client.get("/academies", params={"limit": 2, "offset": 2})
    body = response.json()
    assert body["total"] == 3
    assert body["limit"] == 2
    assert body["offset"] == 2
    assert names(response) == ["다온수학(예시)"]


def test_invalid_level_returns_422(client):
    assert client.get("/academies", params={"level": "university"}).status_code == 422


def test_limit_above_100_returns_422(client):
    assert client.get("/academies", params={"limit": 101}).status_code == 422


def test_detail_returns_all_fields_including_nulls(client, db_session):
    rows = seed_academies(db_session)
    response = client.get(f"/academies/{rows[0].id}")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "가온수학(예시)"
    assert body["tagline"] == "고등 내신 전문(예시)"
    assert body["level_high"] is True
    assert body["level_middle"] is False
    assert body["level_elementary"] is None
    assert body["registration_number"] is None
    assert body["operating_hours"] is None
    assert body["last_verified_at"] == "2026-07-01"
    # 내부 관리용 타임스탬프는 노출하지 않는다.
    assert "created_at" not in body
    assert "updated_at" not in body


def test_detail_not_found_404(client):
    response = client.get("/academies/999999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Academy not found"}
