"""자연어 AI 추천 조립기.

DB→Pydantic 코어는 recommendation_pipeline 에 있고, 여기서는 limit truncate 후
LLM 추천 이유만 붙인다. `_build_reason` 호출 **전에** 자르는 것이 load-bearing —
학원 1건당 LLM 1회인데 풀이 최대 pool_limit(현재 500)건이므로, 순서를 뒤집으면
stub 이 아닌 LLM_PROVIDER 에서 동기 수백 회 순차 호출이 난다.
"""

from __future__ import annotations

import logging
import re
import time
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

logger = logging.getLogger(__name__)

# `backend/vercel.json`의 `maxDuration=30`(서버리스 함수 전체 예산) 대비 여유를 둔다.
# 요청 시작 시점부터 추적한다 — `build_context`(embed 최대 ~10s) 뒤에야 예산을
# 열면 embed+LLM 창이 겹쳐 하드캡을 넘을 수 있다. 남은 시간이 Groq httpx
# timeout(8.0)보다 짧으면 LLM을 시작하지 않고 `_fallback_reason`으로 넘어간다.
_REQUEST_DEADLINE_SECONDS = 28.0
_MIN_REASON_CALL_SECONDS = 8.0

# 프론트 CONDITION_LABELS 와 같은 학부모용 이름. 영문 키를 프롬프트에 넣지 않는다.
_CONDITION_LABELS = {
    "subject": "과목",
    "level_elementary": "초등",
    "level_middle": "중등",
    "level_high": "고등",
    "class_small_group": "소수정예",
    "class_group": "그룹수업",
    "class_one_on_one": "1:1",
    "curriculum_seonhaeng": "선행",
    "curriculum_naesin": "내신",
    "curriculum_suneung": "수능",
    "shuttle_available": "셔틀",
    "budget_max": "수강료",
    "region": "지역",
}

_REASON_SYSTEM_PROMPT = (
    "학부모에게 이 학원을 확인해 볼 후보로 정리한 이유를 2–3문장으로 쓴다. "
    "확인된 사실만 근거로 삼고 미확인 항목은 단정하지 마라. "
    "근거 리뷰는 검색 결과 스니펫(발췌)이지 리뷰 전문이 아니다 — "
    "잘린 문장에서 단정적인 결론을 끌어내지 말고, 리뷰 원문을 붙여넣지 마라. "
    "지역 조건이 완화됐다면 그 지역에 있다고 쓰지 마라. "
    "전화번호나 URL을 지어내지 마라. 연락처는 화면에 표시된 등록 학원 사실만 "
    "쓰며, 이유 문장에 전화·웹사이트를 넣지 마라. "
    "영문 키, 대괄호 리스트([]), '적합도:', 필드명, 주소 전문을 쓰지 마라. "
    "점수나 별점처럼 말하지 마라."
)

_DUMP_MARKERS = ("matched=", "unknown=", "[stub-llm]", "적합도:")
_PYTHON_LIST_RE = re.compile(
    r"\[\s*(?:'[^']*'|\"[^\"]*\"|\w+)(?:\s*,\s*(?:'[^']*'|\"[^\"]*\"|\w+))*\s*\]"
)


def _fallback_reason(scored: ScoredAcademy, relaxed: Sequence[str]) -> str:
    """LLM 실패 시 규칙 기반 이유. 채점 결과만 서술하고 품질을 단정하지 않는다.

    벤더 장애·모델 폐기(2026-09-04 Groq llama-3.3 폐기로 전 요청 500)가
    나도 탐색 응답 자체는 살아 있어야 한다.
    """
    if scored.matched:
        head = (
            f"입력하신 조건 중 {len(scored.matched)}개 항목이 "
            "등록 정보와 맞아 확인해 볼 후보로 정리했습니다."
        )
    else:
        head = (
            "입력하신 조건과 직접 겹치는 등록 정보는 확인되지 않았지만, "
            "조건과 관련해 확인해 볼 후보로 정리했습니다."
        )
    parts = [head]
    if scored.unknown:
        # 개수를 세지 않는다 — 카드는 unknown_conditions 를 나열하지 않으므로
        # "N개"라고 하면 사용자가 볼 수 없는 목록을 가리키게 된다
        # (2026-09-08 카드는 사실 우선). 응답 필드 자체는 그대로 둔다.
        parts.append("등록 정보에서 확인되지 않은 항목은 상담에서 직접 확인해 주세요.")
    if "region" in relaxed:
        parts.append("지역 조건이 완화되어 다른 지역의 후보가 포함될 수 있습니다.")
    return " ".join(parts)


def _condition_labels(keys: Sequence[str]) -> str:
    """알려진 조건 키만 한국어 라벨로. 모르는 키는 영문 누수를 막기 위해 버린다."""
    return ", ".join(
        _CONDITION_LABELS[key] for key in keys if key in _CONDITION_LABELS
    )


def _looks_like_reason_dump(text: str) -> bool:
    """LLM이 디버그 덤프·프롬프트 에코를 그대로 돌려준 경우."""
    stripped = text.strip()
    if not stripped:
        return True
    if any(marker in stripped for marker in _DUMP_MARKERS):
        return True
    return _PYTHON_LIST_RE.search(stripped) is not None


def _reason_user_prompt(
    academy: AcademySummary,
    scored: ScoredAcademy,
    evidence: list[ReviewEvidence],
    query: str,
    relaxed: Sequence[str],
) -> str:
    evidence_snippets = [
        (e.content[:500] + "…") if len(e.content) > 500 else e.content
        for e in evidence
    ]
    evidence_text = " / ".join(evidence_snippets) or "(근거 리뷰 없음)"
    matched_labels = _condition_labels(scored.matched)
    lines = [
        f"질문: {query}",
        f"학원명: {academy.name}",
        f"확인된 조건: {matched_labels or '없음'}",
    ]
    if "region" in relaxed:
        lines.append("지역 조건이 완화되었습니다. 그 지역에 있다고 쓰지 마세요.")
    lines.append(f"근거 리뷰(발췌, 원문 붙여넣기 금지): {evidence_text}")
    return "\n".join(lines)


def _build_reason(
    academy: AcademySummary,
    scored: ScoredAcademy,
    evidence: list[ReviewEvidence],
    query: str,
    relaxed: Sequence[str] = (),
    deadline: float | None = None,
) -> str:
    """후보 이름 + 한국어 조건 라벨 + 근거 리뷰로 LLM 추천 이유를 생성한다.

    채점 덤프(`matched=` 등)는 프롬프트에 넣지 않는다. LLM 준비/호출 실패와
    덤프처럼 보이는 출력은 항목별로 삼키고 `_fallback_reason`으로 대체한다 —
    consultation_service의 used_fallback 패턴 준용 (응답 스키마는 그대로).

    `deadline`(`time.monotonic()` 기준)이 임박했으면 LLM을 아예 호출하지 않고
    바로 fallback으로 넘어간다 — `limit`(최대 10)개 항목이 순차 호출이라, 개별
    provider 타임아웃만으로는 전체 합이 `maxDuration`을 넘을 수 있다.
    """
    if deadline is not None and deadline - time.monotonic() < _MIN_REASON_CALL_SECONDS:
        logger.info("LLM 추천 이유 시간 예산 소진 — fallback으로 대체")
        return _fallback_reason(scored, relaxed)

    messages = [
        {
            "role": "system",
            "content": _REASON_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": _reason_user_prompt(
                academy, scored, evidence, query, relaxed
            ),
        },
    ]
    try:
        llm = get_llm_provider()
        text = llm.chat(messages)
    except Exception:
        logger.warning(
            "LLM 추천 이유 생성 실패 — 규칙 기반 fallback으로 대체", exc_info=True
        )
        return _fallback_reason(scored, relaxed)
    if _looks_like_reason_dump(text):
        logger.info("LLM 추천 이유가 덤프처럼 보여 fallback으로 대체")
        return _fallback_reason(scored, relaxed)
    return text.strip()


def recommend(db: Session, query: str, limit: int) -> AiRecommendationResponse:
    # embed/DB/랭킹보다 먼저 요청 전역 deadline을 연다 — build_context 이후에
    # 예산을 열면 embed(최대 ~10s)와 LLM 창이 겹쳐 maxDuration을 넘길 수 있다.
    deadline = time.monotonic() + _REQUEST_DEADLINE_SECONDS
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
                deadline=deadline,
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
