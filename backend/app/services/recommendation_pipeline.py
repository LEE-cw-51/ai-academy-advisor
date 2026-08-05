"""AI 추천·채팅이 공유하는 DB→Pydantic 파이프라인 코어.

DB 작업은 전부 여기서 끝나고, 밖으로는 Pydantic/평범한 객체만 나간다.
P2(POST /chat SSE)는 세션이 닫힌 뒤 스트리밍하므로 이 전제가 필수다.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.review import Review
from app.providers.factory import get_embedding_provider, get_vector_store
from app.repositories import academy_repository, engagement_repository
from app.schemas.academy import AcademySummary, RecommendationRequest
from app.schemas.ai_recommendation import ReviewEvidence
from app.services import intent, scoring
from app.services.scoring import ScoredAcademy

_EVIDENCE_TOP_K = 5


@dataclass(frozen=True)
class PipelineContext:
    query: str
    request: RecommendationRequest  # 완화 전 원본 의도 (채점 기준)
    subjects: list[str]
    parsed_intent: dict
    relaxed: list[str]
    scored: list[ScoredAcademy]  # 정렬 완료, 풀 전체 (truncate 안 함)
    academies_by_id: dict[int, AcademySummary]
    evidence_by_academy: dict[int, list[ReviewEvidence]]


def _merge_prev_filters(
    prev_filters: dict | None, parsed: RecommendationRequest
) -> RecommendationRequest:
    """직전 턴 필터와 새 질문 해석을 병합한다. 새 질문의 non-None 값이 이긴다.

    모르는 키는 Pydantic v2 기본(extra='ignore')으로 조용히 버린다.
    extra='forbid' 로 바꾸면 클라이언트 오타가 서비스 내부 500이 된다.
    """
    base: dict = dict(prev_filters or {})
    for key, value in parsed.model_dump().items():
        if value is not None:
            base[key] = value
    base["limit"] = parsed.limit
    base["offset"] = parsed.offset
    return RecommendationRequest.model_validate(base)


def _to_summaries(rows) -> list[AcademySummary]:
    return [AcademySummary.model_validate(row) for row in rows]


def _candidate_pool(
    db: Session,
    req: RecommendationRequest,
    subjects: list[str],
    pool_limit: int,
) -> tuple[list[AcademySummary], list[str]]:
    """완화 사다리: 원본 → q 제거 → region 제거. 풀이 비지 않는 첫 단계에서 멈춘다.

    실제로 설정돼 있던 필터만 relaxed 에 기록한다.
    q 를 먼저 푸는 이유: 자유 텍스트라 가장 취약하고, 직전 턴에서 넘어온 과잉
    조건일 가능성이 높다. region 은 사용자의 가장 명시적인 의도라 마지막에 푼다.
    parse_intent 는 q 를 세팅하지 않으므로 q 단계는 prev_filters(P2 멀티턴)로만
    도달한다 — 죽은 코드가 아니다.
    """
    name_like = scoring.name_patterns(subjects)
    rows = academy_repository.list_candidates(db, req, pool_limit, name_like)
    if rows:
        return _to_summaries(rows), []

    relaxed: list[str] = []
    working = req

    if working.q is not None:
        relaxed.append("q")
        working = working.model_copy(update={"q": None})
        rows = academy_repository.list_candidates(
            db, working, pool_limit, name_like
        )
        if rows:
            return _to_summaries(rows), list(relaxed)

    if working.region is not None:
        relaxed.append("region")
        working = working.model_copy(update={"region": None})
        rows = academy_repository.list_candidates(
            db, working, pool_limit, name_like
        )
        if rows:
            return _to_summaries(rows), list(relaxed)

    return [], list(relaxed)


def _evidence_for(
    db: Session, query_embedding: list[float]
) -> list[tuple[Review, float]]:
    """질문 임베딩으로 벡터 스토어를 검색해 (리뷰, 유사도) 쌍을 반환한다.

    Hit.score 는 id 로 lookup 한다. get_reviews_by_ids 가 없는 id 를 조용히
    버리므로 위치 zip 은 어긋날 수 있다.
    """
    hits = get_vector_store().search(query_embedding, top_k=_EVIDENCE_TOP_K)
    similarity_by_id = {int(h.id): h.score for h in hits if h.id.isdigit()}
    reviews = engagement_repository.get_reviews_by_ids(
        db, list(similarity_by_id)
    )
    return [(r, similarity_by_id[r.id]) for r in reviews]


def build_context(
    db: Session,
    query: str,
    prev_filters: dict | None = None,
    limit: int = 3,
    pool_limit: int = 200,
) -> PipelineContext:
    """순서 계약: history → merge → subjects → pool → evidence → rank."""
    # 1. 질문 기록 — 완화 루프 밖에서 정확히 1회
    engagement_repository.create_search_history(db, query)

    # 2. 의도 + 직전 필터 병합
    req = _merge_prev_filters(prev_filters, intent.parse_intent(query, limit))

    # 3. 과목 (런타임 휴리스틱 — SQL WHERE 로 새어나가지 않음)
    subjects = scoring.extract_subjects(query)

    # 4. 후보 풀 (ORM→Pydantic 은 세션 살아있을 때)
    candidates, relaxed = _candidate_pool(db, req, subjects, pool_limit)
    academies_by_id = {a.id: a for a in candidates}

    # 5. RAG 근거 + 학원별 최고 유사도
    query_embedding = get_embedding_provider().embed([query])[0]
    evidence_by_academy: dict[int, list[ReviewEvidence]] = {}
    similarity_by_academy: dict[int, float] = {}
    evidence_counts: dict[int, int] = {}
    for review, sim in _evidence_for(db, query_embedding):
        evidence_by_academy.setdefault(review.academy_id, []).append(
            ReviewEvidence.model_validate(review)
        )
        evidence_counts[review.academy_id] = evidence_counts.get(
            review.academy_id, 0
        ) + 1
        prev = similarity_by_academy.get(review.academy_id)
        if prev is None or sim > prev:
            similarity_by_academy[review.academy_id] = sim

    # 6. 원본 req 로 채점 (완화해도 conflicts 에 region 등이 남는다)
    scored = scoring.rank(
        candidates,
        req,
        subjects=subjects,
        evidence_counts=evidence_counts,
        similarity=similarity_by_academy,
    )

    # 7. parsed_intent 조립
    parsed_intent = req.model_dump(
        exclude={"limit", "offset"}, exclude_none=True
    )
    if subjects:
        parsed_intent["subjects"] = subjects

    return PipelineContext(
        query=query,
        request=req,
        subjects=subjects,
        parsed_intent=parsed_intent,
        relaxed=relaxed,
        scored=scored,
        academies_by_id=academies_by_id,
        evidence_by_academy=evidence_by_academy,
    )
