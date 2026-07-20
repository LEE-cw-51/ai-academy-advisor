"""자연어 질문에서 구조화된 추천 필터를 추출한다.

현재 구현은 규칙 기반 키워드 매칭이다. LLM 기반 의도 분석(더 유연한 파싱)이 필요해지면
이 `parse_intent` 함수만 교체하면 되도록 순수 함수로 격리했다 — 호출부
(`ai_recommendation_service`)는 이 시그니처에만 의존한다.
"""

from __future__ import annotations

import re

from app.core.constants import ClassType, CurriculumType, SchoolLevel
from app.schemas.academy import RecommendationRequest

# §4 타겟 지역. 질문에 등장하면 지역(address 부분일치) 조건으로 사용한다.
_REGION_KEYWORDS = ["미사", "하남", "강동", "위례", "분당"]

# 커리큘럼 키워드 → enum
_CURRICULUM_KEYWORDS = {
    "내신": CurriculumType.NAESIN,
    "수능": CurriculumType.SUNEUNG,
    "선행": CurriculumType.SEONHAENG,
}

# 수업형태 키워드 → enum (긴 키워드 우선 매칭)
_CLASS_TYPE_KEYWORDS = {
    "1:1": ClassType.ONE_ON_ONE,
    "일대일": ClassType.ONE_ON_ONE,
    "소수정예": ClassType.SMALL_GROUP,
    "소수": ClassType.SMALL_GROUP,
    "그룹": ClassType.GROUP,
}

# "300만"/"30만원" 형태의 예산 상한 (단위: 만원)
_BUDGET_PATTERN = re.compile(r"(\d+)\s*만")


def _parse_level(query: str) -> SchoolLevel | None:
    # 고1/고2/고3/고등 → high, 중/중등 → middle, 초/초등 → elementary
    if re.search(r"고\d|고등", query):
        return SchoolLevel.HIGH
    if re.search(r"중\d|중등|중학|중학생", query):
        return SchoolLevel.MIDDLE
    if re.search(r"초\d|초등|초등학교|초등학생", query):
        return SchoolLevel.ELEMENTARY
    return None


def _parse_region(query: str) -> str | None:
    for keyword in _REGION_KEYWORDS:
        if keyword in query:
            return keyword
    return None


def _parse_curriculum(query: str) -> CurriculumType | None:
    for keyword, value in _CURRICULUM_KEYWORDS.items():
        if keyword in query:
            return value
    return None


def _parse_class_type(query: str) -> ClassType | None:
    for keyword, value in _CLASS_TYPE_KEYWORDS.items():
        if keyword in query:
            return value
    return None


def _parse_budget_max(query: str) -> int | None:
    match = _BUDGET_PATTERN.search(query)
    if match:
        return int(match.group(1)) * 10_000
    return None


def parse_intent(query: str, limit: int) -> RecommendationRequest:
    """자연어 질문을 규칙 기반으로 `RecommendationRequest`(기존 필터)로 변환한다."""
    return RecommendationRequest(
        level=_parse_level(query),
        class_type=_parse_class_type(query),
        curriculum=_parse_curriculum(query),
        region=_parse_region(query),
        budget_max=_parse_budget_max(query),
        limit=limit,
        offset=0,
    )
