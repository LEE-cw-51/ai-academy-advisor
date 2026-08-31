"""과목 taxonomy·검색 제안 매칭 (네트워크 없음)."""

import json
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
    load_academy_records,
    names_match,
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


def test_extract_subjects_rejects_substring_false_positives():
    assert extract_subjects_from_text("카드 영수증 문의") == []
    assert "국어" not in extract_subjects_from_text("학원>외국어학원")
    assert "국어" not in extract_subjects_from_text("학원>중국어학원")
    assert extract_subjects_from_text("학원>외국어학원") == ["기타"]
    assert extract_subjects_from_text("학원>중국어학원") == ["기타"]
    assert extract_subjects_from_text("학원>국어학원") == ["국어"]


def test_addresses_match_road():
    canonical = "경기도 하남시 미사강변남로 103 , 408호 (망월동, 미사랑데르Ⅲ)"
    assert addresses_match(canonical, "경기 하남시 미사강변남로 103")
    assert not addresses_match(canonical, "서울특별시 강남구 테헤란로 1")


def test_homepage_rejects_place_and_blog():
    assert is_homepage_url("https://example-academy.com")
    assert not is_homepage_url("https://https//naver.me/5xL7F49a")
    assert not is_homepage_url("https://blog.naver.com/foo")
    assert not is_homepage_url("https://www.instagram.com/academy")
    assert not is_homepage_url("http://pf.kakao.com/_abc")
    assert not is_homepage_url("https://youtube.com/@channel")


def test_official_blog_home_only():
    assert is_official_blog_url("https://blog.naver.com/academyid")
    assert not is_official_blog_url("https://blog.naver.com/academyid/123456")
    assert not is_official_blog_url("https://cafe.naver.com/hanam")


def test_build_proposal_subjects_from_category_only_not_title():
    """과목은 category에서만 추출 — title의 '수학'은 무시한다."""
    record = AcademyRecord(name="미사수학학원", address="경기도 하남시 미사강변남로 1")
    place_general = LocalPlace(
        title="미사수학학원",
        link="",
        category="학원>종합학원",
        address="",
        road_address="경기도 하남시 미사강변남로 1",
    )
    proposal_general = build_proposal(Path("x.json"), record, [place_general], [])
    assert "수학" not in proposal_general.proposed_subjects
    assert "subjects_from=category" in proposal_general.evidence

    place_math = LocalPlace(
        title="미사수학학원",
        link="",
        category="학원>수학학원",
        address="",
        road_address="경기도 하남시 미사강변남로 1",
    )
    proposal_math = build_proposal(Path("x.json"), record, [place_math], [])
    assert "수학" in proposal_math.proposed_subjects


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
    record = AcademyRecord(name="gaontest학원")
    items = [
        ReviewItem(
            title="gaontest학원 안내",
            content="미사 gaontest학원 공지",
            url="https://blog.naver.com/gaontest/111",
            source="naver_blog",
            published_at=None,
        )
    ]
    assert pick_blog_url(record, items) == "https://blog.naver.com/gaontest"


def test_pick_blog_url_skips_parent_review_posts():
    record = AcademyRecord(name="gaontest학원")
    items = [
        ReviewItem(
            title="gaon테스트 후기",
            content="아이가 다녀본 미사 gaon테스트학원",
            url="https://blog.naver.com/gaontest/111",
            source="naver_blog",
            published_at=None,
        )
    ]
    assert pick_blog_url(record, items) == ""


def test_pick_blog_url_skips_unrelated_blog_id_even_without_parent_markers():
    record = AcademyRecord(name="수학의힘학원")
    items = [
        ReviewItem(
            title="수학의힘학원 소개",
            content="하남 미사 수학의힘학원 안내",
            url="https://blog.naver.com/royalsolar/111",
            source="naver_blog",
            published_at=None,
        )
    ]
    assert pick_blog_url(record, items) == ""


def test_pick_blog_url_from_legacy_postview_link():
    """PostView.nhn?blogId=... 형태는 blogId를 path가 아니라 쿼리에서 뽑는다."""
    record = AcademyRecord(name="gaontest학원")
    items = [
        ReviewItem(
            title="gaontest학원 안내",
            content="미사 gaontest학원 공지",
            url="https://blog.naver.com/PostView.nhn?blogId=gaontest&logNo=111",
            source="naver_blog",
            published_at=None,
        )
    ]
    assert pick_blog_url(record, items) == "https://blog.naver.com/gaontest"
    assert not is_official_blog_url(
        "https://blog.naver.com/PostView.nhn?blogId=gaontest&logNo=111"
    )


def test_build_proposal_ignores_blog_snippet_subjects():
    record = AcademyRecord(name="미사종합학원", address="경기도 하남시 미사강변남로 1")
    place = LocalPlace(
        title="미사종합학원",
        link="",
        category="학원>종합학원",
        address="",
        road_address="경기도 하남시 미사강변남로 1",
    )
    blogs = [
        ReviewItem(
            title="영어학원도 다녔다",
            content="영어 학원 후기",
            url="https://blog.naver.com/someone/1",
            source="naver_blog",
            published_at=None,
        )
    ]
    proposal = build_proposal(Path("x.json"), record, [place], blogs)
    assert "영어" not in proposal.proposed_subjects


def test_build_proposal_high_when_address_and_homepage_without_subjects():
    record = AcademyRecord(name="미사종합학원", address="경기도 하남시 미사강변남로 1")
    place = LocalPlace(
        title="미사종합학원",
        link="https://misa-jonghap.example.com",
        category="학원>종합학원",
        address="",
        road_address="경기도 하남시 미사강변남로 1",
        telephone="031-111-2222",
    )
    proposal = build_proposal(Path("x.json"), record, [place], [])
    assert proposal.confidence == "high"
    assert proposal.website_url == "https://misa-jonghap.example.com"
    assert proposal.proposed_phone == "031-111-2222"
    assert proposal.proposed_subjects == []


def test_build_proposal_skips_website_when_name_mismatch():
    record = AcademyRecord(
        name="비긴잉글리시학원",
        address="경기도 하남시 미사강변대로34번길 82",
    )
    place = LocalPlace(
        title="클루잉글리시",
        link="https://www.instagram.com/clue_english_/",
        category="어학교육>영어교육",
        address="",
        road_address="경기도 하남시 미사강변대로34번길 82",
    )
    proposal = build_proposal(Path("x.json"), record, [place], [])
    assert proposal.website_url == ""
    assert proposal.confidence == "high"
    assert "영어" in proposal.proposed_subjects


def test_names_match_bidirectional():
    assert names_match("이에스파워어학학원", "이에스파워 국제어학원")
    assert not names_match("비긴잉글리시학원", "클루잉글리시")
def test_names_match_ignores_spaces_on_both_sides():
    """학원명에 공백이 있어도(양쪽 다 제거 후 비교) 매칭돼야 한다."""
    assert names_match("미사 스타 영어학원", "미사스타영어학원")
    assert names_match("미사 스타 영어학원", "미사 스타 영어")


def test_load_academy_records_skips_malformed_file_instead_of_crashing(tmp_path, capsys):
    good = {"name": "정상학원", "address": "경기도 하남시 미사강변대로 1"}
    (tmp_path / "a-good.json").write_text(
        json.dumps(good, ensure_ascii=False), encoding="utf-8"
    )
    (tmp_path / "b-broken.json").write_text("{이건 JSON이 아님", encoding="utf-8")

    pairs = load_academy_records(tmp_path)

    assert [p.name for _, p in pairs] == ["정상학원"]
    assert "b-broken.json" in capsys.readouterr().err


def test_pick_local_name_only_match_without_corroboration_is_low_confidence():
    """주소가 아니라 이름만 맞은 후보는(블로그 근거도 없으면) medium이 아니라 low —
    동명이인 학원(다른 도시)에 사실을 잘못 붙이는 것을 막는다."""
    record = AcademyRecord(name="가온학원", address="경기도 하남시 미사강변대로 1")
    place = LocalPlace(
        title="가온학원",
        link="https://gaon-busan.example.com",
        category="학원>수학학원",
        address="부산광역시 해운대구 어딘가",
        road_address="부산광역시 해운대구 어딘가로 1",
    )
    proposal = build_proposal(Path("x.json"), record, [place], [])
    assert proposal.confidence == "low"
    assert proposal.website_url == ""
    assert proposal.proposed_subjects == []
