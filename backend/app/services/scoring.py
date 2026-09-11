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
from app.core.subjects import (
    SubjectHit,
    extract_subject_hits as _extract_subject_hits,
    extract_subjects_from_text,
)
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

# 질의 과목 추출은 app.core.subjects 와 같은 규칙을 쓴다. academy.subjects 는
# 4종(국어·영어·수학·기타)이고, 과학·피아노 등은 기타 버킷 + subject_detail 라벨로
# 들어간다. 그래서 "물리"→기타/과학 hit 을 만들어 subject_detail="과학" 학원과
# 라벨로 매칭한다 (버킷만 보면 피아노 학원까지 매칭되는 오류를 막는다).

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
    """질문에서 과목 버킷을 추출한다 (parsed_intent·relaxed 계약용, taxonomy 4종)."""
    return extract_subjects_from_text(query)


def extract_subject_hits(query: str) -> list[SubjectHit]:
    """질문에서 과목 신호를 버킷+세부 라벨로 추출한다 (채점·정렬 힌트용)."""
    return _extract_subject_hits(query)


def _hit_term(hit: str | SubjectHit) -> str | None:
    """정렬/매칭에 쓸 어휘. 기타 hit 은 라벨(없으면 스킵), 나머지는 버킷/문자열."""
    if isinstance(hit, SubjectHit):
        if hit.subject == "기타":
            return hit.label
        return hit.subject
    return hit


def name_patterns(subjects: Sequence[str | SubjectHit]) -> tuple[str, ...]:
    """list_candidates 정렬 힌트용 ilike 패턴. 과목 어휘는 scoring 에만 둔다."""
    terms = [_hit_term(hit) for hit in subjects]
    return tuple(f"%{term}%" for term in terms if term)


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
    subjects: Sequence[str | SubjectHit],
    matched: list[str],
    unknown: list[str],
    conflicts: list[str],
) -> float:
    # 문자열은 국/영/수 버킷 hit 으로 승격. 라벨 없는 맨 "기타" hit 은 신호가
    # 없으므로 버린다 (그것 하나로 모든 기타 학원이 매칭되면 안 된다).
    hits = [h if isinstance(h, SubjectHit) else SubjectHit(h, None) for h in subjects]
    hits = [h for h in hits if not (h.subject == "기타" and h.label is None)]
    if not hits:
        return 0.0

    listed = academy.subjects
    for hit in hits:
        term = hit.label if hit.subject == "기타" else hit.subject
        if term is None:
            continue
        name_hit = term in academy.name
        if hit.subject == "기타":
            list_hit = academy.subject_detail == term
        else:
            list_hit = bool(listed) and term in listed
        if name_hit or list_hit:
            matched.append("subject")
            return WEIGHT_SUBJECT

    if listed is None:
        unknown.append("subject")
        return 0.0

    # subjects 는 확인됐고 매치는 없다. 기타 hit 은 학원의 세부 라벨이 미확인이면
    # 감점하지 않고 unknown 으로 둔다 (확인된 다른 라벨일 때만 충돌).
    any_conflict = False
    any_unknown = False
    for hit in hits:
        if hit.subject == "기타":
            if "기타" in listed:
                if academy.subject_detail is None:
                    any_unknown = True
                else:
                    any_conflict = True
            else:
                any_conflict = True
        else:
            any_conflict = True

    if any_conflict:
        conflicts.append("subject")
        return WEIGHT_CONDITION_FALSE
    if any_unknown:
        unknown.append("subject")
    return 0.0


def score_one(
    academy: AcademySummary,
    request: RecommendationRequest,
    subjects: Sequence[str | SubjectHit] = (),
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
    subjects: Sequence[str | SubjectHit] = (),
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
