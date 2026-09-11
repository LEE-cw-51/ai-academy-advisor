"""scoring.py 순수 랭킹 단위 테스트 (DB 픽스처 없음)."""

from __future__ import annotations

import ast
from datetime import date, timedelta
from pathlib import Path

import pytest

from app.core.constants import CurriculumType, SchoolLevel
from app.schemas.academy import AcademySummary, RecommendationRequest
from app.services import scoring
from app.services.scoring import (
    EVIDENCE_CAP,
    FRESHNESS_DAYS,
    WEIGHT_BUDGET_OVER,
    WEIGHT_BUDGET_WITHIN,
    WEIGHT_CONDITION_FALSE,
    WEIGHT_CONDITION_TRUE,
    WEIGHT_EVIDENCE_PER,
    WEIGHT_FRESHNESS,
    WEIGHT_REGION,
    WEIGHT_SUBJECT,
    extract_subjects,
    name_patterns,
    rank,
    score_one,
)


def _academy(**overrides) -> AcademySummary:
    base = dict(
        id=1,
        name="가온수학(예시)",
        address="경기도 하남시 미사강변대로 1",
        phone=None,
        tagline=None,
        subjects=None,
        level_elementary=None,
        level_middle=None,
        level_high=None,
        class_small_group=None,
        class_group=None,
        class_one_on_one=None,
        curriculum_seonhaeng=None,
        curriculum_naesin=None,
        curriculum_suneung=None,
        shuttle_available=None,
        tuition_monthly_fee=None,
        last_verified_at=None,
        latitude=None,
        longitude=None,
    )
    base.update(overrides)
    return AcademySummary(**base)


def test_null_vs_false_score_difference():
    """미확인(None)은 벌점 없고, 확인된 부재(False)는 감점 — 이 PR의 존재 이유."""
    req = RecommendationRequest(level=SchoolLevel.HIGH, limit=3)
    unknown = score_one(_academy(level_high=None), req)
    absent = score_one(_academy(level_high=False), req)

    assert unknown.score == 0.0
    assert "level_high" in unknown.unknown
    assert absent.score == pytest.approx(WEIGHT_CONDITION_FALSE)
    assert "level_high" in absent.conflicts
    assert absent.score < unknown.score


def test_true_condition_matches():
    req = RecommendationRequest(level=SchoolLevel.HIGH, limit=3)
    result = score_one(_academy(level_high=True), req)
    assert result.score == pytest.approx(WEIGHT_CONDITION_TRUE)
    assert result.matched == ["level_high"]


def test_budget_three_way():
    req = RecommendationRequest(budget_max=300_000, limit=3)
    within = score_one(_academy(tuition_monthly_fee=280_000), req)
    over = score_one(_academy(tuition_monthly_fee=400_000), req)
    unknown = score_one(_academy(tuition_monthly_fee=None), req)

    assert within.score == pytest.approx(WEIGHT_BUDGET_WITHIN)
    assert "budget_max" in within.matched
    assert over.score == pytest.approx(WEIGHT_BUDGET_OVER)
    assert "budget_max" in over.conflicts
    assert unknown.score == 0.0
    assert "budget_max" in unknown.unknown


def test_subject_name_match():
    req = RecommendationRequest(limit=3)
    result = score_one(_academy(name="하늘수학"), req, subjects=["수학"])
    assert result.score == pytest.approx(WEIGHT_SUBJECT)
    assert result.matched == ["subject"]


def test_subject_list_match():
    req = RecommendationRequest(limit=3)
    result = score_one(
        _academy(name="가온학원", subjects=["영어", "수학"]),
        req,
        subjects=["수학"],
    )
    assert "subject" in result.matched
    assert result.score == pytest.approx(WEIGHT_SUBJECT)


def test_subject_null_unknown():
    req = RecommendationRequest(limit=3)
    result = score_one(
        _academy(name="가온피아노", subjects=None),
        req,
        subjects=["수학"],
    )
    assert result.score == 0.0
    assert result.unknown == ["subject"]
    assert result.matched == []
    assert result.conflicts == []


def test_subject_nonnull_mismatch_conflicts():
    req = RecommendationRequest(limit=3)
    result = score_one(
        _academy(name="가온피아노", subjects=["영어"]),
        req,
        subjects=["수학"],
    )
    assert result.score == pytest.approx(WEIGHT_CONDITION_FALSE)
    assert result.conflicts == ["subject"]


def test_subject_etc_label_matches_name():
    from app.core.subjects import SubjectHit

    req = RecommendationRequest(limit=3)
    result = score_one(
        _academy(name="뮤즈피아노교습소", subjects=["기타"], subject_detail=None),
        req,
        subjects=[SubjectHit("기타", "피아노")],
    )
    assert result.score == pytest.approx(WEIGHT_SUBJECT)
    assert result.matched == ["subject"]


def test_subject_etc_label_matches_detail():
    from app.core.subjects import SubjectHit

    req = RecommendationRequest(limit=3)
    result = score_one(
        _academy(name="가온학원", subjects=["기타"], subject_detail="피아노"),
        req,
        subjects=[SubjectHit("기타", "피아노")],
    )
    assert result.score == pytest.approx(WEIGHT_SUBJECT)
    assert result.matched == ["subject"]


def test_bare_etc_hit_never_matches_all_etc_academies():
    from app.core.subjects import SubjectHit

    req = RecommendationRequest(limit=3)
    result = score_one(
        _academy(name="미술학원", subjects=["기타"], subject_detail="미술"),
        req,
        subjects=[SubjectHit("기타", None)],
    )
    assert result.matched == []
    assert result.unknown == []
    assert result.conflicts == []
    assert result.score == 0.0


def test_subject_etc_without_detail_is_unknown_not_conflict():
    from app.core.subjects import SubjectHit

    req = RecommendationRequest(limit=3)
    result = score_one(
        _academy(name="가온학원", subjects=["기타"], subject_detail=None),
        req,
        subjects=[SubjectHit("기타", "피아노")],
    )
    assert result.unknown == ["subject"]
    assert result.conflicts == []
    assert result.score == 0.0


def test_subject_etc_with_different_detail_conflicts():
    from app.core.subjects import SubjectHit

    req = RecommendationRequest(limit=3)
    result = score_one(
        _academy(name="가온학원", subjects=["기타"], subject_detail="미술"),
        req,
        subjects=[SubjectHit("기타", "피아노")],
    )
    assert result.conflicts == ["subject"]
    assert result.score == pytest.approx(WEIGHT_CONDITION_FALSE)


def test_name_patterns_uses_etc_label():
    from app.core.subjects import SubjectHit

    assert name_patterns([SubjectHit("기타", "피아노")]) == ("%피아노%",)
    # 라벨 없는 기타 hit 은 패턴을 만들지 않는다.
    assert name_patterns([SubjectHit("기타", None)]) == ()
    assert name_patterns([SubjectHit("수학", None)]) == ("%수학%",)


def test_no_subjects_in_query_skips_subject_lists():
    req = RecommendationRequest(limit=3)
    result = score_one(_academy(name="가온수학"), req, subjects=())
    assert "subject" not in result.matched
    assert "subject" not in result.unknown
    assert "subject" not in result.conflicts


def test_evidence_bonus_cap():
    req = RecommendationRequest(limit=3)
    a = _academy()
    assert score_one(a, req, evidence_count=0).score == 0.0
    assert score_one(a, req, evidence_count=1).score == pytest.approx(
        WEIGHT_EVIDENCE_PER
    )
    assert score_one(a, req, evidence_count=4).score == pytest.approx(
        WEIGHT_EVIDENCE_PER * EVIDENCE_CAP
    )
    assert score_one(a, req, evidence_count=7).score == pytest.approx(
        WEIGHT_EVIDENCE_PER * EVIDENCE_CAP
    )


def test_negative_similarity_clamped():
    req = RecommendationRequest(limit=3)
    result = score_one(_academy(), req, similarity=-0.5)
    assert result.score == 0.0


def test_positive_similarity_added():
    req = RecommendationRequest(limit=3)
    result = score_one(_academy(), req, similarity=0.8)
    assert result.score == pytest.approx(0.8)


def test_rank_tiebreak_deterministic():
    """입력을 섞어도 (-score, name, id) 로 순서가 고정된다."""
    req = RecommendationRequest(
        level=SchoolLevel.HIGH,
        curriculum=CurriculumType.NAESIN,
        region="미사",
        limit=3,
    )
    a = _academy(
        id=2,
        name="나래수학(예시)",
        address="경기도 하남시 미사대로 2",
        level_high=True,
        curriculum_naesin=True,
    )
    b = _academy(
        id=1,
        name="가온수학(예시)",
        address="경기도 하남시 미사강변대로 1",
        level_high=True,
        curriculum_naesin=True,
    )
    # 둘 다 과목+level+naesin+region = 6.0
    ordered = rank([a, b], req, subjects=["수학"])
    assert [s.academy_id for s in ordered] == [1, 2]
    shuffled = rank([a, b], req, subjects=["수학"])
    assert [s.score for s in shuffled] == [6.0, 6.0]
    assert [s.academy_id for s in shuffled] == [1, 2]


def test_freshness_boundary():
    today = date(2026, 7, 31)
    req = RecommendationRequest(limit=3)
    exact = score_one(
        _academy(last_verified_at=today - timedelta(days=FRESHNESS_DAYS)),
        req,
        today=today,
    )
    stale = score_one(
        _academy(last_verified_at=today - timedelta(days=FRESHNESS_DAYS + 1)),
        req,
        today=today,
    )
    missing = score_one(_academy(last_verified_at=None), req, today=today)

    assert exact.score == pytest.approx(WEIGHT_FRESHNESS)
    assert stale.score == 0.0
    assert missing.score == 0.0


@pytest.mark.parametrize(
    "query, expected",
    [
        ("고1 내신 미사 수학학원", ["수학"]),
        ("영어 학원", ["영어"]),
        ("수학 영어", ["영어", "수학"]),
        ("숙제 적은 학원", []),
        # taxonomy가 4종이라 과학은 "기타" 버킷으로 들어간다 (세부 라벨은 "과학").
        ("물리화학", ["기타"]),
        ("과학 좋아하는 아이", ["기타"]),
    ],
)
def test_extract_subjects(query, expected):
    assert extract_subjects(query) == expected


def test_extract_subject_hits_carries_etc_label():
    from app.core.subjects import SubjectHit
    from app.services.scoring import extract_subject_hits

    assert extract_subject_hits("과학 좋아하는 아이") == [SubjectHit("기타", "과학")]
    assert extract_subject_hits("피아노 학원") == [SubjectHit("기타", "피아노")]
    # 맨 "기타"는 라벨이 없어 신호를 만들지 않는다.
    assert extract_subject_hits("기타 상담") == []


def test_name_patterns():
    assert name_patterns(["수학", "영어"]) == ("%수학%", "%영어%")
    assert name_patterns([]) == ()


def test_region_match_and_mismatch():
    req = RecommendationRequest(region="미사", limit=3)
    hit = score_one(_academy(address="하남시 미사대로"), req)
    miss = score_one(_academy(address="서울시 강남구"), req)
    assert hit.score == pytest.approx(WEIGHT_REGION)
    assert hit.matched == ["region"]
    assert miss.score == 0.0
    assert miss.conflicts == ["region"]


def test_scoring_module_imports_no_sqlalchemy():
    """실행 가능한 아키텍처 가드: scoring.py 는 sqlalchemy/app.models 를 import 하지 않는다."""
    path = Path(scoring.__file__)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                forbidden.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            forbidden.add(node.module.split(".")[0])
            if node.module.startswith("app.models"):
                forbidden.add("app.models")
    assert "sqlalchemy" not in forbidden
    assert "app.models" not in forbidden
    # ImportFrom app.models...
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("app.models")
            assert node.module != "sqlalchemy" and not node.module.startswith(
                "sqlalchemy."
            )
