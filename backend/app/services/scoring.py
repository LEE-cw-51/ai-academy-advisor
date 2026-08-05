"""순수 적합도 랭킹 모듈.

SQLAlchemy / app.models 를 import 하지 않는다 (계층 규칙, docs/architecture.md).
입력은 Pydantic AcademySummary 와 원시 dict/스칼라뿐이다.
과목 추출도 여기에 둔다 — RecommendationRequest 에 필드를 추가하면
POST /recommendations 하드 엔드포인트에 유령 파라미터가 생긴다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Mapping, Sequence

from app.core.constants import ClassType, CurriculumType, SchoolLevel
from app.schemas.academy import AcademySummary, RecommendationRequest

# --- 가중치 (모듈 상수) ---
WEIGHT_SUBJECT = 3.0
WEIGHT_CONDITION_TRUE = 1.0
WEIGHT_CONDITION_FALSE = -2.0
WEIGHT_BUDGET_WITHIN = 1.5
WEIGHT_BUDGET_OVER = -2.0
WEIGHT_REGION = 1.0
WEIGHT_EVIDENCE_PER = 0.5
EVIDENCE_CAP = 4
WEIGHT_FRESHNESS = 0.2
FRESHNESS_DAYS = 180

# 질문·이름에서 매칭할 과목 어휘 (긴 키워드 우선 불필요 — 단순 부분일치).
_SUBJECT_VOCAB: tuple[str, ...] = (
    "수학",
    "영어",
    "국어",
    "과학",
    "물리",
    "화학",
    "생물",
    "지구과학",
    "논술",
    "코딩",
    "중국어",
    "일본어",
)

_LEVEL_ATTR = {
    SchoolLevel.ELEMENTARY: "level_elementary",
    SchoolLevel.MIDDLE: "level_middle",
    SchoolLevel.HIGH: "level_high",
}

_CLASS_ATTR = {
    ClassType.SMALL_GROUP: "class_small_group",
    ClassType.GROUP: "class_group",
    ClassType.ONE_ON_ONE: "class_one_on_one",
}

_CURRICULUM_ATTR = {
    CurriculumType.SEONHAENG: "curriculum_seonhaeng",
    CurriculumType.NAESIN: "curriculum_naesin",
    CurriculumType.SUNEUNG: "curriculum_suneung",
}


@dataclass(frozen=True)
class ScoredAcademy:
    academy_id: int
    score: float
    matched: list[str]
    unknown: list[str]
    conflicts: list[str]


def extract_subjects(query: str) -> list[str]:
    """질문에서 과목 키워드를 추출한다. 등장 순서·어휘 순으로 중복 없이."""
    found: list[str] = []
    for subject in _SUBJECT_VOCAB:
        if subject in query and subject not in found:
            found.append(subject)
    return found


def name_patterns(subjects: Sequence[str]) -> tuple[str, ...]:
    """list_candidates 정렬 힌트용 ilike 패턴. 과목 어휘는 scoring 에만 둔다."""
    return tuple(f"%{s}%" for s in subjects)


def _tri_state(
    value: bool | None,
    key: str,
    matched: list[str],
    unknown: list[str],
    conflicts: list[str],
) -> float:
    if value is True:
        matched.append(key)
        return WEIGHT_CONDITION_TRUE
    if value is False:
        conflicts.append(key)
        return WEIGHT_CONDITION_FALSE
    unknown.append(key)
    return 0.0


def _subject_signal(
    academy: AcademySummary,
    subjects: Sequence[str],
    matched: list[str],
    unknown: list[str],
    conflicts: list[str],
) -> float:
    if not subjects:
        return 0.0

    name_hit = any(s in academy.name for s in subjects)
    listed = academy.subjects
    list_hit = bool(listed) and any(s in listed for s in subjects)

    if name_hit or list_hit:
        matched.append("subject")
        return WEIGHT_SUBJECT

    if listed is None:
        unknown.append("subject")
        return 0.0

    conflicts.append("subject")
    return WEIGHT_CONDITION_FALSE


def score_one(
    academy: AcademySummary,
    request: RecommendationRequest,
    subjects: Sequence[str] = (),
    evidence_count: int = 0,
    similarity: float | None = None,
    today: date | None = None,
) -> ScoredAcademy:
    """학원 1건의 적합도 점수와 투명성 리스트를 계산한다."""
    matched: list[str] = []
    unknown: list[str] = []
    conflicts: list[str] = []
    total = 0.0

    total += _subject_signal(academy, subjects, matched, unknown, conflicts)

    if request.level is not None:
        attr = _LEVEL_ATTR[request.level]
        total += _tri_state(
            getattr(academy, attr), attr, matched, unknown, conflicts
        )

    if request.class_type is not None:
        attr = _CLASS_ATTR[request.class_type]
        total += _tri_state(
            getattr(academy, attr), attr, matched, unknown, conflicts
        )

    if request.curriculum is not None:
        attr = _CURRICULUM_ATTR[request.curriculum]
        total += _tri_state(
            getattr(academy, attr), attr, matched, unknown, conflicts
        )

    if request.shuttle is not None:
        val = academy.shuttle_available
        if val is None:
            unknown.append("shuttle_available")
        elif val == request.shuttle:
            matched.append("shuttle_available")
            total += WEIGHT_CONDITION_TRUE
        else:
            conflicts.append("shuttle_available")
            total += WEIGHT_CONDITION_FALSE

    if request.budget_max is not None:
        fee = academy.tuition_monthly_fee
        if fee is None:
            unknown.append("budget_max")
        elif fee <= request.budget_max:
            matched.append("budget_max")
            total += WEIGHT_BUDGET_WITHIN
        else:
            conflicts.append("budget_max")
            total += WEIGHT_BUDGET_OVER

    if request.region is not None:
        address = academy.address or ""
        if request.region in address:
            matched.append("region")
            total += WEIGHT_REGION
        else:
            # 확인된 불일치이지만 감점하지 않는다 (완화 후에만 도달). docs/api.md.
            conflicts.append("region")

    total += WEIGHT_EVIDENCE_PER * min(max(evidence_count, 0), EVIDENCE_CAP)

    if similarity is not None:
        total += max(0.0, similarity)

    ref = today if today is not None else date.today()
    verified = academy.last_verified_at
    if verified is not None and verified >= ref - timedelta(days=FRESHNESS_DAYS):
        total += WEIGHT_FRESHNESS

    return ScoredAcademy(
        academy_id=academy.id,
        score=round(total, 3),
        matched=matched,
        unknown=unknown,
        conflicts=conflicts,
    )


def rank(
    candidates: Sequence[AcademySummary],
    request: RecommendationRequest,
    subjects: Sequence[str] = (),
    evidence_counts: Mapping[int, int] | None = None,
    similarity: Mapping[int, float] | None = None,
    today: date | None = None,
) -> list[ScoredAcademy]:
    """후보를 채점하고 (-score, name, id) 로 안정 정렬한다."""
    counts = evidence_counts or {}
    sims = similarity or {}
    by_id = {a.id: a for a in candidates}
    scored = [
        score_one(
            academy,
            request,
            subjects=subjects,
            evidence_count=counts.get(academy.id, 0),
            similarity=sims.get(academy.id),
            today=today,
        )
        for academy in candidates
    ]
    scored.sort(
        key=lambda s: (-s.score, by_id[s.academy_id].name, s.academy_id)
    )
    return scored
