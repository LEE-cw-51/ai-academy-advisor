"""규칙 기반 의도 분석(parse_intent) 단위 테스트."""

from app.core.constants import ClassType, CurriculumType, SchoolLevel
from app.services.intent import parse_intent


def test_parse_full_query():
    req = parse_intent("고1 내신 미사 수학학원", limit=3)
    assert req.level == SchoolLevel.HIGH
    assert req.curriculum == CurriculumType.NAESIN
    assert req.region == "미사"
    assert req.limit == 3


def test_parse_levels():
    assert parse_intent("고2 이과", 3).level == SchoolLevel.HIGH
    assert parse_intent("중3 대비", 3).level == SchoolLevel.MIDDLE
    assert parse_intent("초등 저학년", 3).level == SchoolLevel.ELEMENTARY
    assert parse_intent("수학학원 추천", 3).level is None


def test_parse_class_type_and_budget():
    req = parse_intent("1:1 관리, 30만원 이하", 3)
    assert req.class_type == ClassType.ONE_ON_ONE
    assert req.budget_max == 300_000


def test_parse_curriculum_variants():
    assert parse_intent("수능 대비", 3).curriculum == CurriculumType.SUNEUNG
    assert parse_intent("선행 위주", 3).curriculum == CurriculumType.SEONHAENG


def test_parse_empty_intent_is_all_none():
    req = parse_intent("좋은 학원 알려줘", 3)
    assert req.level is None
    assert req.class_type is None
    assert req.curriculum is None
    assert req.region is None
    assert req.budget_max is None
