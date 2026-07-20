"""POST /recommendations/ai — 자연어 추천 파이프라인(stub provider) 테스트."""

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
