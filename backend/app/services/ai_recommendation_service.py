"""자연어 AI 추천 파이프라인.

기획안 §9 추천 과정을 provider 포트 경유로 구성한다:
질문 → (SearchHistory 기록) → 의도 분석 → 필터링 → RAG 근거 검색 → 추천 이유 생성.

provider는 전부 config로 선택되는 포트(기본 stub)이며, 실제 임베딩/LLM/pgvector와
LlamaIndex는 config만 바꿔 4b에서 교체한다. 리뷰 ingest 전이라 벡터 검색 결과(근거)는
비어 있을 수 있으나, 포트 호출 경로 자체는 완성되어 있다.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.academy import Academy
from app.models.review import Review
from app.providers.factory import (
    get_embedding_provider,
    get_llm_provider,
    get_vector_store,
)
from app.repositories import academy_repository, engagement_repository
from app.schemas.academy import AcademySummary, RecommendationRequest
from app.schemas.ai_recommendation import (
    AiRecommendationItem,
    AiRecommendationResponse,
    ReviewEvidence,
)
from app.services import intent

# 근거 리뷰 검색 시 조회할 상위 개수.
_EVIDENCE_TOP_K = 5


def _score(req: RecommendationRequest) -> float:
    """해석된 필터 조건 수를 기반으로 한 단순 적합도 점수 (임시 휴리스틱)."""
    conditions = [
        req.level,
        req.class_type,
        req.curriculum,
        req.region,
        req.budget_max,
    ]
    return float(sum(1 for c in conditions if c is not None))


def _build_reason(academy: Academy, evidence: list[Review], query: str) -> str:
    """후보 사실 + 근거 리뷰로 프롬프트를 구성해 LLM에게 추천 이유를 생성시킨다."""
    llm = get_llm_provider()
    facts = f"학원명: {academy.name}, 주소: {academy.address or '미상'}"
    evidence_text = " / ".join(r.content for r in evidence) or "(근거 리뷰 없음)"
    messages = [
        {
            "role": "system",
            "content": "학부모의 질문에 맞춰 학원을 추천하는 이유를 근거 리뷰에 기반해 설명한다.",
        },
        {
            "role": "user",
            "content": f"질문: {query}\n{facts}\n근거 리뷰: {evidence_text}",
        },
    ]
    return llm.chat(messages)


def _evidence_for(db: Session, query_embedding: list[float]) -> list[Review]:
    """질문 임베딩으로 벡터 스토어를 검색해 근거 리뷰를 로드한다."""
    store = get_vector_store()
    hits = store.search(query_embedding, top_k=_EVIDENCE_TOP_K)
    review_ids = [int(hit.id) for hit in hits if hit.id.isdigit()]
    return engagement_repository.get_reviews_by_ids(db, review_ids)


def recommend(db: Session, query: str, limit: int) -> AiRecommendationResponse:
    # 1. 질문 기록 (KPI: 질문 시작률)
    engagement_repository.create_search_history(db, query)

    # 2. 의도 분석 (규칙 기반 기본 구현; LLM 파서로 교체 가능)
    req = intent.parse_intent(query, limit)

    # 3. 조건 필터링 (기존 규칙 기반 추천 로직 재사용)
    candidates, _ = academy_repository.list_recommendations(db, req)

    # 4. RAG 근거 검색 (질문 임베딩 → 벡터 검색 → 리뷰 로드)
    embedder = get_embedding_provider()
    query_embedding = embedder.embed([query])[0]
    evidence = _evidence_for(db, query_embedding)
    evidence_by_academy: dict[int, list[Review]] = {}
    for review in evidence:
        evidence_by_academy.setdefault(review.academy_id, []).append(review)

    # 5. 추천 이유 생성 + 점수
    base_score = _score(req)
    items = [
        AiRecommendationItem(
            academy=AcademySummary.model_validate(academy),
            reason=_build_reason(
                academy, evidence_by_academy.get(academy.id, []), query
            ),
            score=base_score,
            evidence_reviews=[
                ReviewEvidence.model_validate(r)
                for r in evidence_by_academy.get(academy.id, [])
            ],
        )
        for academy in candidates
    ]

    return AiRecommendationResponse(
        query=query,
        parsed_intent=req.model_dump(exclude={"limit", "offset"}, exclude_none=True),
        items=items,
    )
