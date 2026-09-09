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
        # stub 기본 경로도 학부모용 문장 — 채점 덤프·에코를 카드에 올리지 않는다.
        assert "matched=" not in item["reason"]
        assert "[stub-llm]" not in item["reason"]
        assert "unknown=" not in item["reason"]
        assert "적합도:" not in item["reason"]
        assert "확인해 볼 후보" in item["reason"]


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


class _ExplodingEmbedder:
    """OpenAI 임베딩 장애 시뮬레이션 — embed가 항상 실패한다."""

    def embed(self, texts):
        raise RuntimeError("openai embeddings unavailable")


def test_ai_recommend_returns_facts_when_embedding_fails(
    client, db_session, monkeypatch
):
    """임베딩이 죽어도 학원 사실 후보는 200 + evidence_reviews 빈 배열."""
    seed_academies(db_session)
    monkeypatch.setattr(
        "app.services.recommendation_pipeline.get_embedding_provider",
        lambda: _ExplodingEmbedder(),
    )
    response = client.post(
        "/recommendations/ai", json={"query": "고1 내신 미사 수학학원"}
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    for item in items:
        assert item["evidence_reviews"] == []
        assert "used_fallback" not in item


class _ExplodingVectorStore:
    """pgvector 장애 시뮬레이션 — search가 항상 실패한다."""

    def search(self, query_embedding, top_k=5):
        raise RuntimeError("pgvector unavailable")


def test_ai_recommend_returns_facts_when_vector_search_fails(
    client, db_session, monkeypatch
):
    """벡터 검색이 죽어도 학원 사실 후보는 200 + evidence_reviews 빈 배열."""
    seed_academies(db_session)
    monkeypatch.setattr(
        "app.services.recommendation_pipeline.get_vector_store",
        lambda db=None: _ExplodingVectorStore(),
    )
    response = client.post(
        "/recommendations/ai", json={"query": "고1 내신 미사 수학학원"}
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    for item in items:
        assert item["evidence_reviews"] == []


class _ExplodingLLM:
    """벤더 장애·모델 폐기 시뮬레이션 — chat이 항상 실패한다."""

    def chat(self, messages):
        raise RuntimeError("model_not_found")


def test_ai_recommend_falls_back_when_llm_fails(client, db_session, monkeypatch):
    """LLM이 죽어도 200 + 규칙 기반 reason (2026-09-04 Groq 모델 폐기 회귀)."""
    seed_academies(db_session)
    monkeypatch.setattr(
        "app.services.ai_recommendation_service.get_llm_provider",
        lambda: _ExplodingLLM(),
    )
    response = client.post(
        "/recommendations/ai", json={"query": "고1 내신 미사 수학학원"}
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    for item in items:
        assert item["reason"]
        assert "확인해 볼 후보" in item["reason"]


def test_fallback_reason_does_not_count_items_the_card_never_lists(
    client, db_session, monkeypatch
):
    """폴백 문구는 미확인 항목을 '개수'로 세지 않는다.

    카드가 unknown_conditions 를 나열하지 않기로 한 뒤(2026-09-08 사실 우선),
    "미확인 항목 3개"는 사용자가 화면 어디서도 볼 수 없는 목록을 가리킨다.
    응답 필드 자체는 투명성 필드로 남는다 — 바꾼 건 사람이 읽는 문장뿐.
    """
    # 미확인(NULL) 사실이 있는 시드라야 unknown_conditions 가 채워진다.
    seed_null_fact_academies(db_session)
    monkeypatch.setattr(
        "app.services.ai_recommendation_service.get_llm_provider",
        lambda: _ExplodingLLM(),
    )
    response = client.post(
        "/recommendations/ai", json={"query": "고1 내신 미사 수학학원"}
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert items

    with_unknown = [i for i in items if i["unknown_conditions"]]
    assert with_unknown, "미확인 항목이 있는 후보가 없으면 이 회귀를 못 지킨다"
    for item in with_unknown:
        # matched 개수는 카드가 "확인된 조건"으로 실제 나열하므로 세도 된다.
        # 세면 안 되는 건 화면에 없는 unknown 쪽이다.
        assert "미확인 항목" not in item["reason"]
        assert "등록 정보에서 확인되지 않은 항목" in item["reason"]


def test_ai_recommend_falls_back_when_provider_init_fails(
    client, db_session, monkeypatch
):
    """get_llm_provider 자체가 죽어도(설정 오류 등) 항목별 fallback으로 200."""
    seed_academies(db_session)

    def _boom():
        raise ValueError("bad provider config")

    monkeypatch.setattr(
        "app.services.ai_recommendation_service.get_llm_provider", _boom
    )
    response = client.post("/recommendations/ai", json={"query": "수학"})
    assert response.status_code == 200
    assert all(item["reason"] for item in response.json()["items"])


class _TrackingLLM:
    """chat 호출 여부를 기록한다."""

    def __init__(self) -> None:
        self.calls = 0

    def chat(self, messages):
        self.calls += 1
        return "LLM reason that should not appear"


def test_ai_recommend_skips_llm_when_request_budget_exhausted(
    client, db_session, monkeypatch
):
    """요청 전역 deadline 잔여 < MIN_REASON(8s)이면 LLM을 시작하지 않고 fallback."""
    import app.services.ai_recommendation_service as svc

    seed_academies(db_session)
    llm = _TrackingLLM()
    monkeypatch.setattr(
        "app.services.ai_recommendation_service.get_llm_provider",
        lambda: llm,
    )
    # deadline = monotonic() + (-100) → _build_reason 시점에 잔여가 이미 MIN 미만
    monkeypatch.setattr(svc, "_REQUEST_DEADLINE_SECONDS", -100.0)

    order: list[str] = []
    real_build = svc.build_context

    def tracked_build(*args, **kwargs):
        order.append("build_context")
        return real_build(*args, **kwargs)

    real_monotonic = svc.time.monotonic

    def tracked_monotonic() -> float:
        # recommend()의 첫 monotonic은 deadline 개설 — build_context보다 앞서야 한다.
        if "deadline" not in order:
            order.append("deadline")
        return real_monotonic()

    monkeypatch.setattr(svc, "build_context", tracked_build)
    monkeypatch.setattr(svc.time, "monotonic", tracked_monotonic)

    response = client.post(
        "/recommendations/ai", json={"query": "고1 내신 미사 수학학원"}
    )
    assert response.status_code == 200
    assert order[:2] == ["deadline", "build_context"]
    items = response.json()["items"]
    assert items
    assert llm.calls == 0
    for item in items:
        assert "확인해 볼 후보" in item["reason"]
        assert "LLM reason that should not appear" not in item["reason"]


def test_reason_system_prompt_forbids_invented_contact():
    """연락처는 등록 사실·UI만 — 이유 문장에 전화/URL을 지어내지 않는다."""
    from app.services.ai_recommendation_service import _REASON_SYSTEM_PROMPT

    assert "전화번호" in _REASON_SYSTEM_PROMPT
    assert "URL" in _REASON_SYSTEM_PROMPT
    assert "지어내" in _REASON_SYSTEM_PROMPT
    assert "이유 문장" in _REASON_SYSTEM_PROMPT
    assert "전화" in _REASON_SYSTEM_PROMPT
    assert "웹사이트" in _REASON_SYSTEM_PROMPT
    assert "적합도:" in _REASON_SYSTEM_PROMPT
    assert "주소 전문" in _REASON_SYSTEM_PROMPT
    assert "영문 키" in _REASON_SYSTEM_PROMPT


class _DumpLLM:
    """모델이 프롬프트 덤프를 따라 쓴 경우."""

    def chat(self, messages):
        return (
            "[stub-llm] 입력을 받았습니다: 질문: 고1 내신 "
            "적합도: matched=['subject'], unknown=['level_high']"
        )


def test_ai_recommend_replaces_dump_like_llm_output(client, db_session, monkeypatch):
    """LLM이 matched= / [stub-llm] / 적합도: 덤프를 돌려줘도 폴백 문장으로 바꾼다."""
    seed_academies(db_session)
    monkeypatch.setattr(
        "app.services.ai_recommendation_service.get_llm_provider",
        lambda: _DumpLLM(),
    )
    response = client.post(
        "/recommendations/ai", json={"query": "고1 내신 미사 수학학원"}
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    for item in items:
        assert "matched=" not in item["reason"]
        assert "[stub-llm]" not in item["reason"]
        assert "unknown=" not in item["reason"]
        assert "적합도:" not in item["reason"]
        assert "확인해 볼 후보" in item["reason"]


class _CapturingGoodLLM:
    """프롬프트에 덤프가 실리는지 검사하고, 깨끗한 문장을 반환한다."""

    def __init__(self) -> None:
        self.user_content = ""

    def chat(self, messages):
        for message in messages:
            if message.get("role") == "user":
                self.user_content = str(message.get("content", ""))
        return "등록된 고등·내신 정보와 맞아 확인해 볼 후보로 정리했습니다."


def test_reason_prompt_sends_korean_labels_not_debug_dump(
    client, db_session, monkeypatch
):
    seed_academies(db_session)
    llm = _CapturingGoodLLM()
    monkeypatch.setattr(
        "app.services.ai_recommendation_service.get_llm_provider",
        lambda: llm,
    )
    response = client.post(
        "/recommendations/ai", json={"query": "고1 내신 미사 수학학원"}
    )
    assert response.status_code == 200
    assert "matched=" not in llm.user_content
    assert "unknown=" not in llm.user_content
    assert "적합도:" not in llm.user_content
    assert "conflicts=" not in llm.user_content
    assert "고등" in llm.user_content
    assert "내신" in llm.user_content
    assert "과목" in llm.user_content
    for item in response.json()["items"]:
        assert item["reason"] == (
            "등록된 고등·내신 정보와 맞아 확인해 볼 후보로 정리했습니다."
        )
