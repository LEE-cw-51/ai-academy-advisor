"""자연어 AI 추천 조립기.

DB→Pydantic 코어는 recommendation_pipeline 에 있고, 여기서는 limit truncate 후
LLM 추천 이유만 붙인다. `_build_reason` 호출 **전에** 자르는 것이 load-bearing —
학원 1건당 LLM 1회인데 풀이 200건이므로, 순서를 뒤집으면 stub 이 아닌
LLM_PROVIDER 에서 동기 200회 순차 호출이 난다.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.providers.factory import get_llm_provider
from app.schemas.academy import AcademySummary
from app.schemas.ai_recommendation import (
    AiRecommendationItem,
    AiRecommendationResponse,
    ReviewEvidence,
)
from app.services.recommendation_pipeline import build_context
from app.services.scoring import ScoredAcademy


def _build_reason(
    academy: AcademySummary,
    scored: ScoredAcademy,
    evidence: list[ReviewEvidence],
    query: str,
    relaxed: Sequence[str] = (),
) -> str:
    """후보 사실 + 채점 투명성 + 근거 리뷰로 LLM 추천 이유를 생성한다."""
    llm = get_llm_provider()
    facts = f"학원명: {academy.name}, 주소: {academy.address or '미상'}"
    evidence_snippets = [
        (e.content[:500] + "…") if len(e.content) > 500 else e.content
        for e in evidence
    ]
    evidence_text = " / ".join(evidence_snippets) or "(근거 리뷰 없음)"
    transparency = (
        f"matched={scored.matched}, unknown={scored.unknown}, "
        f"conflicts={scored.conflicts}, relaxed={list(relaxed)}"
    )
    messages = [
        {
            "role": "system",
            "content": (
                "학부모의 질문에 맞춰 학원을 추천하는 이유를 근거 리뷰에 기반해 설명한다. "
                "확인된 사실만 근거로 삼고 미확인 항목은 단정하지 마라. "
                "relaxed에 포함된 조건(특히 region)은 사용자가 원한 조건이 완화됐다는 "
                "뜻이므로, 그 지역에 있다고 쓰지 마라."
            ),
        },
        {
            "role": "user",
            "content": (
                f"질문: {query}\n{facts}\n적합도: {transparency}\n"
                f"근거 리뷰: {evidence_text}"
            ),
        },
    ]
    return llm.chat(messages)


def recommend(db: Session, query: str, limit: int) -> AiRecommendationResponse:
    ctx = build_context(db, query, limit=limit)

    # ⚠️ limit truncate 후에만 LLM 호출 — 풀 전체를 돌리면 호출이 폭주한다.
    top = ctx.scored[:limit]
    items = [
        AiRecommendationItem(
            academy=ctx.academies_by_id[s.academy_id],
            reason=_build_reason(
                ctx.academies_by_id[s.academy_id],
                s,
                ctx.evidence_by_academy.get(s.academy_id, []),
                query,
                relaxed=ctx.relaxed,
            ),
            score=s.score,
            evidence_reviews=ctx.evidence_by_academy.get(s.academy_id, []),
            matched_conditions=s.matched,
            unknown_conditions=s.unknown,
            conflicts=s.conflicts,
        )
        for s in top
    ]

    return AiRecommendationResponse(
        query=query,
        parsed_intent=ctx.parsed_intent,
        items=items,
        relaxed=ctx.relaxed,
    )
