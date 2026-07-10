from app.models.academy import Academy


def seed_academies(db) -> list[Academy]:
    """지역·예산 필터 검증을 위한 매트릭스: 수강료 NULL(미확인) 포함."""
    rows = [
        Academy(
            name="가온수학(예시)",
            address="경기도 하남시 미사강변대로 1",
            level_middle=False,
            level_high=True,
            shuttle_available=True,
            tuition_monthly_fee=300000,
        ),
        Academy(
            name="나래수학(예시)",
            address="경기도 하남시 미사대로 2",
            level_middle=True,
            level_high=False,
            shuttle_available=False,
            tuition_monthly_fee=200000,
        ),
        Academy(
            name="다온수학(예시)",
            address="경기도 하남시 망월동 3",
            level_middle=True,
            level_high=None,
            shuttle_available=None,
            tuition_monthly_fee=None,
        ),
    ]
    db.add_all(rows)
    db.commit()
    return rows


def names(response) -> list[str]:
    return [item["name"] for item in response.json()["items"]]


def test_recommend_empty_body_returns_all(client, db_session):
    seed_academies(db_session)
    response = client.post("/recommendations", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert names(response) == ["가온수학(예시)", "나래수학(예시)", "다온수학(예시)"]


def test_recommend_reuses_existing_level_filter(client, db_session):
    seed_academies(db_session)
    response = client.post("/recommendations", json={"level": "high"})
    assert names(response) == ["가온수학(예시)"]


def test_recommend_region_matches_address_substring(client, db_session):
    seed_academies(db_session)
    response = client.post("/recommendations", json={"region": "미사"})
    assert names(response) == ["가온수학(예시)", "나래수학(예시)"]


def test_recommend_region_no_match_returns_empty(client, db_session):
    seed_academies(db_session)
    response = client.post("/recommendations", json={"region": "강남"})
    assert names(response) == []
    assert response.json()["total"] == 0


def test_recommend_budget_max_excludes_over_budget_and_unverified(client, db_session):
    seed_academies(db_session)
    response = client.post("/recommendations", json={"budget_max": 250000})
    # 다온(NULL=미확인)과 가온(300000, 예산 초과)은 모두 제외되어야 한다.
    assert names(response) == ["나래수학(예시)"]


def test_recommend_filters_combine_with_and(client, db_session):
    seed_academies(db_session)
    response = client.post(
        "/recommendations",
        json={"level": "middle", "region": "미사", "budget_max": 250000},
    )
    assert names(response) == ["나래수학(예시)"]


def test_recommend_pagination_limit_offset_total(client, db_session):
    seed_academies(db_session)
    response = client.post("/recommendations", json={"limit": 2, "offset": 2})
    body = response.json()
    assert body["total"] == 3
    assert body["limit"] == 2
    assert body["offset"] == 2
    assert names(response) == ["다온수학(예시)"]


def test_recommend_invalid_level_returns_422(client):
    response = client.post("/recommendations", json={"level": "university"})
    assert response.status_code == 422


def test_recommend_negative_budget_returns_422(client):
    response = client.post("/recommendations", json={"budget_max": -1})
    assert response.status_code == 422
