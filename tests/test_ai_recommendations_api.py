"""POST /recommendations/ai — 자연어 추천 파이프라인(stub provider) 테스트."""

import pytest

from app.models.academy import Academy
from app.models.review import Review
from app.models.engagement import SearchHistory


def seed_academies(db) -> list[Academy]:
    rows = [
        Academy(
            name="가온수학(예시)",
            address="경기도 하남시 미사강변대로 1",
            level_high=True,
            curriculum_naesin=True,
        ),
        Academy(
            name="나래수학(예시)",
            address="경기도 하남시 미사대로 2",
            level_high=True,
            curriculum_naesin=True,
        ),
        Academy(
            name="강남수학(예시)",
            address="서울시 강남구 1",
            level_high=True,
        ),
    ]
    db.add_all(rows)
    db.commit()
    return rows


def test_ai_recommend_returns_items_with_reason_and_score(client, db_session):
    seed_academies(db_session)
    response = client.post(
        "/recommendations/ai", json={"query": "고1 내신 미사 수학학원"}
    )
    assert response.status_code == 200
    body = response.json()

    assert body["query"] == "고1 내신 미사 수학학원"
    # 미사 + high + 내신 → 미사 학원 2곳만 (강남 제외)
    names = [item["academy"]["name"] for item in body["items"]]
    assert names == ["가온수학(예시)", "나래수학(예시)"]

    for item in body["items"]:
        assert isinstance(item["reason"], str) and item["reason"]
        assert isinstance(item["score"], (int, float))
        assert item["evidence_reviews"] == []  # 리뷰 ingest 전이라 근거 없음


def test_ai_recommend_exposes_parsed_intent(client, db_session):
    seed_academies(db_session)
    response = client.post(
        "/recommendations/ai", json={"query": "고2 내신 미사"}
    )
    parsed = response.json()["parsed_intent"]
    assert parsed["level"] == "high"
    assert parsed["curriculum"] == "naesin"
    assert parsed["region"] == "미사"


def test_ai_recommend_records_search_history(client, db_session):
    seed_academies(db_session)
    client.post("/recommendations/ai", json={"query": "숙제 적은 수학학원"})
    rows = db_session.query(SearchHistory).all()
    assert len(rows) == 1
    assert rows[0].query == "숙제 적은 수학학원"


def test_ai_recommend_respects_limit(client, db_session):
    seed_academies(db_session)
    response = client.post(
        "/recommendations/ai", json={"query": "고등 수학학원", "limit": 1}
    )
    assert len(response.json()["items"]) == 1


def test_ai_recommend_evidence_loaded_when_reviews_indexed(client, db_session):
    """벡터 스토어에 리뷰가 색인되면 근거 리뷰가 응답에 실린다 (포트 경로 검증)."""
    academies = seed_academies(db_session)
    review = Review(
        academy_id=academies[0].id,
        content="고1 내신 대비가 정말 좋았습니다",
        source="맘카페",
        rating=5,
    )
    db_session.add(review)
    db_session.commit()
    db_session.refresh(review)

    # stub VectorStore는 in-memory라 색인해 둔다 (실제 배포는 pgvector ingest가 담당).
    from app.providers.factory import get_embedding_provider, get_vector_store

    embedder = get_embedding_provider()
    store = get_vector_store()
    query = "고1 내신 미사 수학학원"
    store.add([(str(review.id), embedder.embed([review.content])[0])])

    try:
        response = client.post("/recommendations/ai", json={"query": query})
        assert response.status_code == 200
        items = {i["academy"]["name"]: i for i in response.json()["items"]}
        evidence = items["가온수학(예시)"]["evidence_reviews"]
        assert len(evidence) == 1
        assert evidence[0]["content"] == "고1 내신 대비가 정말 좋았습니다"
        assert evidence[0]["source"] == "맘카페"
        assert evidence[0]["rating"] == 5
    finally:
        store._items.clear()  # lru_cache 싱글턴이라 다른 테스트에 누수 방지


def test_ai_recommend_includes_coordinates_for_map(client, db_session):
    """지도 마커용 좌표가 /recommendations/ai 응답의 academy에도 포함되어야 한다."""
    rows = seed_academies(db_session)
    rows[0].latitude = 37.5601526466
    rows[0].longitude = 127.1866028387
    db_session.commit()

    response = client.post(
        "/recommendations/ai", json={"query": "고1 내신 미사 수학학원"}
    )
    assert response.status_code == 200
    items = {i["academy"]["name"]: i["academy"] for i in response.json()["items"]}

    assert items["가온수학(예시)"]["latitude"] == pytest.approx(37.5601526466)
    assert items["가온수학(예시)"]["longitude"] == pytest.approx(127.1866028387)
    assert items["나래수학(예시)"]["latitude"] is None
    assert items["나래수학(예시)"]["longitude"] is None


def seed_null_fact_academies(db) -> list[Academy]:
    """실데이터처럼 3상태·예산·과목이 전부 NULL 인 학원들."""
    rows = [
        Academy(name="하늘수학", address="경기도 하남시 미사대로 10"),
        Academy(name="가온피아노", address="경기도 하남시 미사대로 20"),
        Academy(name="나래영어", address="경기도 하남시 미사대로 30"),
    ]
    db.add_all(rows)
    db.commit()
    return rows


def test_ai_recommend_returns_items_when_all_facts_null(client, db_session):
    """헤드라인 버그: 하드 .is_(True) 라면 [] — 소프트 필터에선 결과가 나온다."""
    seed_null_fact_academies(db_session)
    response = client.post(
        "/recommendations/ai",
        json={"query": "고1 내신 미사 소수정예 30만원 수학학원"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["items"]  # main 에서는 []
    assert body["relaxed"] == []


def test_ai_recommend_subject_match_ranks_first_with_strictly_higher_score(
    client, db_session
):
    seed_null_fact_academies(db_session)
    response = client.post(
        "/recommendations/ai",
        json={"query": "고1 내신 미사 수학학원"},
    )
    items = response.json()["items"]
    assert items[0]["academy"]["name"] == "하늘수학"
    assert items[0]["score"] > items[1]["score"]


def test_ai_recommend_scores_differ_across_items(client, db_session):
    """삭제한 _score() 는 모든 항목에 동일 점수를 줬다 — 이제 달라야 한다."""
    seed_null_fact_academies(db_session)
    response = client.post(
        "/recommendations/ai",
        json={"query": "고1 내신 미사 수학학원"},
    )
    scores = [i["score"] for i in response.json()["items"]]
    assert len(set(scores)) > 1


def test_ai_recommend_exposes_transparency_lists(client, db_session):
    seed_null_fact_academies(db_session)
    response = client.post(
        "/recommendations/ai",
        json={"query": "고1 내신 미사 수학학원"},
    )
    item = response.json()["items"][0]
    assert "subject" in item["matched_conditions"]
    assert "region" in item["matched_conditions"]
    assert "level_high" in item["unknown_conditions"]
    assert "curriculum_naesin" in item["unknown_conditions"]
    assert isinstance(item["conflicts"], list)


def test_ai_recommend_relaxes_region_when_no_local_hit(client, db_session):
    seed_null_fact_academies(db_session)
    response = client.post(
        "/recommendations/ai",
        json={"query": "분당 수학학원"},
    )
    body = response.json()
    assert body["relaxed"] == ["region"]
    assert body["items"]
    for item in body["items"]:
        assert "region" in item["conflicts"]


def test_ai_recommend_relaxed_empty_on_direct_hit(client, db_session):
    seed_academies(db_session)
    response = client.post(
        "/recommendations/ai",
        json={"query": "고1 내신 미사 수학학원"},
    )
    assert response.json()["relaxed"] == []


def test_ai_recommend_evidence_similarity_raises_score(client, db_session):
    academies = seed_null_fact_academies(db_session)
    # 피아노 학원에만 리뷰를 달아 유사도·근거 보너스로 순위가 뒤집히게 한다.
    piano = next(a for a in academies if a.name == "가온피아노")
    review = Review(
        academy_id=piano.id,
        content="고1 내신 미사 수학학원 추천합니다",
        source="맘카페",
        rating=5,
    )
    db_session.add(review)
    db_session.commit()
    db_session.refresh(review)

    from app.providers.factory import get_embedding_provider, get_vector_store

    embedder = get_embedding_provider()
    store = get_vector_store()
    query = "고1 내신 미사 수학학원"
    store.add([(str(review.id), embedder.embed([review.content])[0])])

    try:
        response = client.post("/recommendations/ai", json={"query": query})
        assert response.status_code == 200
        items = {i["academy"]["name"]: i for i in response.json()["items"]}
        # 근거·유사도 보너스 없이는 하늘수학이 1위. 보너스로 피아노 점수가 올라간다.
        assert items["가온피아노"]["score"] > 0
        assert items["가온피아노"]["evidence_reviews"]
    finally:
        store._items.clear()


def test_ai_recommend_empty_db_returns_200_with_empty_items(client, db_session):
    response = client.post(
        "/recommendations/ai", json={"query": "고1 내신 미사 수학학원"}
    )
    assert response.status_code == 200
    assert response.json()["items"] == []
