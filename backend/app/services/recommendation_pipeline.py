"""AI 추천·채팅이 공유하는 DB→Pydantic 파이프라인 코어.

DB 작업은 전부 여기서 끝나고, 밖으로는 Pydantic/평범한 객체만 나간다.
P2(POST /chat SSE)는 세션이 닫힌 뒤 스트리밍하므로 이 전제가 필수다.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.providers.factory import get_embedding_provider, get_vector_store
from app.repositories import academy_repository, engagement_repository
from app.schemas.academy import AcademySummary, RecommendationRequest
from app.schemas.ai_recommendation import ReviewEvidence
from app.services import intent, scoring
from app.services.scoring import ScoredAcademy

logger = logging.getLogger(__name__)

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


def _similar_review_ids(db: Session, query: str) -> dict[int, float] | None:
    """질문 임베딩으로 벡터 스토어를 검색해 {review_id: 유사도} 를 반환한다.

    **폴백 대상은 이 두 호출뿐이다.** 임베딩/벡터 장애가 학원 사실 후보를 500으로
    죽이지 않게 None 을 돌려주고 채점은 사실만으로 이어간다. 리뷰 본문 조회와
    스키마 검증은 이 밖에 둔다 — 그쪽 결함까지 삼키면 코드 버그가 '근거 없음'으로
    위장돼 WARNING 만 남기고 영구히 빈 evidence 를 내보내게 된다.
    """
    try:
        query_embedding = get_embedding_provider().embed([query])[0]
        hits = get_vector_store(db).search(
            query_embedding, top_k=_EVIDENCE_TOP_K
        )
    except Exception:
        logger.warning(
            "RAG 근거 검색 실패 — 학원 사실만으로 채점 계속", exc_info=True
        )
        return None
    return {int(h.id): h.score for h in hits if h.id.isdigit()}


def _load_review_evidence(
    db: Session, query: str
) -> tuple[
    dict[int, list[ReviewEvidence]],
    dict[int, float],
    dict[int, int],
]:
    """벡터 히트를 학원별 근거·유사도·건수로 모은다.

    Hit.score 는 id 로 lookup 한다. get_reviews_by_ids 가 없는 id 를 조용히
    버리므로 위치 zip 은 어긋날 수 있다. 후보 풀·SearchHistory 는 여기서 감싸지 않는다.
    """
    similarity_by_id = _similar_review_ids(db, query)
    if not similarity_by_id:
        return {}, {}, {}

    evidence_by_academy: dict[int, list[ReviewEvidence]] = {}
    similarity_by_academy: dict[int, float] = {}
    evidence_counts: dict[int, int] = {}
    reviews = engagement_repository.get_reviews_by_ids(
        db, list(similarity_by_id)
    )
    for review in reviews:
        sim = similarity_by_id[review.id]
        evidence_by_academy.setdefault(review.academy_id, []).append(
            ReviewEvidence.model_validate(review)
        )
        evidence_counts[review.academy_id] = evidence_counts.get(
            review.academy_id, 0
        ) + 1
        prev = similarity_by_academy.get(review.academy_id)
        if prev is None or sim > prev:
            similarity_by_academy[review.academy_id] = sim
    return evidence_by_academy, similarity_by_academy, evidence_counts


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

    # 5. RAG 근거 + 학원별 최고 유사도 (실패 시 빈 근거로 사실 채점만 이어감)
    evidence_by_academy, similarity_by_academy, evidence_counts = (
        _load_review_evidence(db, query)
    )

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
