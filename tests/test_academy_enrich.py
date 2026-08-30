"""과목 taxonomy·검색 제안 매칭 (네트워크 없음)."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.subjects import extract_subjects_from_text, normalize_subjects
from app.providers.naver_local import LocalPlace
from app.providers.base import ReviewItem
from app.schemas.academy import AcademyRecord
from app.services.academy_enrich_service import (
    addresses_match,
    build_proposal,
    is_homepage_url,
    is_official_blog_url,
    pick_blog_url,
)


def test_normalize_subjects_order_and_dedupe():
    assert normalize_subjects(["수학", "영어", "수학"]) == ["영어", "수학"]


def test_normalize_rejects_unknown():
    with pytest.raises(ValueError, match="거부"):
        normalize_subjects(["한문"])


def test_academy_record_subjects_taxonomy():
    record = AcademyRecord.model_validate(
        {
            "name": "테스트영수학원",
            "subjects": ["수학", "영어"],
        }
    )
    assert record.subjects == ["영어", "수학"]


def test_academy_record_rejects_unknown_subject():
    with pytest.raises(ValidationError):
        AcademyRecord.model_validate({"name": "테스트", "subjects": ["한문"]})


def test_extract_yeongsu_and_science():
    assert extract_subjects_from_text("학원>영수학원") == ["영어", "수학"]
    assert "과학" in extract_subjects_from_text("물리·화학 전문")


def test_addresses_match_road():
    canonical = "경기도 하남시 미사강변남로 103 , 408호 (망월동, 미사랑데르Ⅲ)"
    assert addresses_match(canonical, "경기 하남시 미사강변남로 103")
    assert not addresses_match(canonical, "서울특별시 강남구 테헤란로 1")


def test_homepage_rejects_place_and_blog():
    assert is_homepage_url("https://example-academy.com")
    assert not is_homepage_url("https://https//naver.me/5xL7F49a")
    assert not is_homepage_url("https://blog.naver.com/foo")


def test_official_blog_home_only():
    assert is_official_blog_url("https://blog.naver.com/academyid")
    assert not is_official_blog_url("https://blog.naver.com/academyid/123456")
    assert not is_official_blog_url("https://cafe.naver.com/hanam")


def test_build_proposal_high_when_address_and_category():
    record = AcademyRecord(
        name="하이엔드영수학원",
        address="경기도 하남시 미사강변남로 103",
    )
    place = LocalPlace(
        title="하이엔드영수학원",
        link="https://hyend-math.example.com",
        category="학원>수학학원",
        address="",
        road_address="경기도 하남시 미사강변남로 103",
    )
    proposal = build_proposal(Path("x.json"), record, [place], [])
    assert proposal.confidence == "high"
    assert "수학" in proposal.proposed_subjects
    assert proposal.website_url == "https://hyend-math.example.com"


def test_build_proposal_low_without_match():
    record = AcademyRecord(name="모르는학원", address="경기도 하남시 미사강변대로 1")
    proposal = build_proposal(Path("x.json"), record, [], [])
    assert proposal.confidence == "low"
    assert proposal.proposed_subjects == []


def test_pick_blog_url_from_post_link():
    record = AcademyRecord(name="가온수학학원")
    items = [
        ReviewItem(
            title="가온수학 후기",
            content="미사 가온수학학원",
            url="https://blog.naver.com/gaonmath/111",
            source="naver_blog",
            published_at=None,
        )
    ]
    assert pick_blog_url(record, items) == "https://blog.naver.com/gaonmath"
