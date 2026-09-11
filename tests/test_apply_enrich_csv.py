"""apply_enrich_csv dry-run·apply fixture (네트워크 없음)."""

import csv
import json
from pathlib import Path

from app.services.academy_apply_service import apply_enrich_csv, rollback_enrich_urls


def _write_academy(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fields = [
        "name",
        "address",
        "proposed_subjects",
        "website_url",
        "blog_url",
        "proposed_phone",
        "confidence",
        "evidence",
        "source_note",
        "file_name",
        "matched_local_title",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _row(**overrides: str) -> dict[str, str]:
    base = {
        "name": "",
        "address": "",
        "proposed_subjects": "",
        "website_url": "",
        "blog_url": "",
        "proposed_phone": "",
        "confidence": "high",
        "evidence": "",
        "source_note": "",
        "file_name": "",
        "matched_local_title": "",
    }
    base.update(overrides)
    return base


def test_apply_dry_run_fills_nulls_skips_medium_low_preserves_existing(tmp_path):
    json_dir = tmp_path / "academies"
    json_dir.mkdir()
    high_null = {
        "name": "testsuhak학원",
        "address": "경기도 하남시 미사강변남로 1",
        "phone": "031-123-4567",
        "latitude": 37.5,
        "longitude": 127.1,
        "subjects": None,
        "website_url": None,
        "blog_url": None,
        "source_note": "원본",
        "last_verified_at": "2026-07-10",
    }
    existing = {
        "name": "이미채운학원",
        "subjects": ["영어"],
        "website_url": "https://already.example.com",
        "blog_url": "https://blog.naver.com/already",
        "phone": "031-000-0000",
    }
    _write_academy(json_dir / "high.json", high_null)
    _write_academy(json_dir / "medium.json", {"name": "미디엄학원", "subjects": None})
    _write_academy(json_dir / "low.json", {"name": "로우학원", "subjects": None})
    _write_academy(json_dir / "kept.json", existing)

    csv_path = tmp_path / "proposals.csv"
    _write_csv(
        csv_path,
        [
            _row(
                name="testsuhak학원",
                address=high_null["address"],
                proposed_subjects="수학",
                website_url="https://example-academy.com",
                blog_url="https://blog.naver.com/testsuhak",
                proposed_phone="031-999-9999",
                confidence="high",
                file_name="high.json",
                matched_local_title="testsuhak학원",
            ),
            _row(
                name="미디엄학원",
                proposed_subjects="영어",
                confidence="medium",
                file_name="medium.json",
            ),
            _row(
                name="로우학원",
                proposed_subjects="국어",
                confidence="low",
                file_name="low.json",
            ),
            _row(
                name="이미채운학원",
                proposed_subjects="수학",
                website_url="https://other.example.com",
                blog_url="https://blog.naver.com/other",
                proposed_phone="031-888-8888",
                confidence="high",
                file_name="kept.json",
            ),
        ],
    )

    report = apply_enrich_csv(csv_path, json_dir, dry_run=True)
    assert report.applied == 1
    assert report.skipped == 3
    assert report.errors == 0

    unchanged_high = json.loads((json_dir / "high.json").read_text(encoding="utf-8"))
    assert unchanged_high["subjects"] is None
    assert unchanged_high["phone"] == "031-123-4567"
    assert unchanged_high["address"] == high_null["address"]

    unchanged_kept = json.loads((json_dir / "kept.json").read_text(encoding="utf-8"))
    assert unchanged_kept["subjects"] == ["영어"]
    assert unchanged_kept["website_url"] == "https://already.example.com"
    assert unchanged_kept["phone"] == "031-000-0000"

    apply_report = apply_enrich_csv(csv_path, json_dir, dry_run=False)
    assert apply_report.applied == 1
    filled = json.loads((json_dir / "high.json").read_text(encoding="utf-8"))
    assert filled["subjects"] == ["수학"]
    assert filled["website_url"] == "https://example-academy.com"
    assert filled["blog_url"] == "https://blog.naver.com/testsuhak"
    assert filled["phone"] == "031-123-4567"
    kept = json.loads((json_dir / "kept.json").read_text(encoding="utf-8"))
    assert kept["subjects"] == ["영어"]
    assert kept["website_url"] == "https://already.example.com"
    assert kept["phone"] == "031-000-0000"


def test_apply_skips_non_homepage_and_post_blog_url(tmp_path):
    json_dir = tmp_path / "academies"
    json_dir.mkdir()
    _write_academy(
        json_dir / "test-b.json",
        {"name": "테스트", "website_url": None, "blog_url": None},
    )

    csv_path = tmp_path / "proposals.csv"
    _write_csv(
        csv_path,
        [
            {
                "name": "테스트",
                "address": "",
                "proposed_subjects": "",
                "website_url": "https://blog.naver.com/bad",
                "blog_url": "https://blog.naver.com/bad/12345",
                "proposed_phone": "",
                "confidence": "high",
                "evidence": "",
                "source_note": "",
                "file_name": "test-b.json",
                "matched_local_title": "",
            }
        ],
    )

    report = apply_enrich_csv(csv_path, json_dir, dry_run=True)
    assert report.applied == 0
    assert report.skipped == 1


def test_apply_skips_urls_when_name_mismatch_or_non_homepage(tmp_path):
    json_dir = tmp_path / "academies"
    json_dir.mkdir()
    _write_academy(
        json_dir / "mismatch.json",
        {
            "name": "비긴잉글리시학원",
            "website_url": None,
            "blog_url": None,
            "subjects": None,
        },
    )

    csv_path = tmp_path / "proposals.csv"
    _write_csv(
        csv_path,
        [
            _row(
                name="비긴잉글리시학원",
                website_url="https://www.instagram.com/clue_english_/",
                blog_url="https://blog.naver.com/clueenglish",
                file_name="mismatch.json",
                matched_local_title="클루잉글리시",
            )
        ],
    )

    report = apply_enrich_csv(csv_path, json_dir, dry_run=False)
    assert report.applied == 0
    assert report.skipped == 1

    unchanged = json.loads((json_dir / "mismatch.json").read_text(encoding="utf-8"))
    assert unchanged["website_url"] is None
    assert unchanged["blog_url"] is None


def test_apply_writes_json_on_apply(tmp_path):
    json_dir = tmp_path / "academies"
    json_dir.mkdir()
    _write_academy(
        json_dir / "test-c.json",
        {"name": "테스트", "subjects": None, "website_url": None, "blog_url": None},
    )

    csv_path = tmp_path / "proposals.csv"
    _write_csv(
        csv_path,
        [
            {
                "name": "테스트",
                "address": "",
                "proposed_subjects": "영어|수학",
                "website_url": "",
                "blog_url": "",
                "proposed_phone": "",
                "confidence": "high",
                "evidence": "",
                "source_note": "",
                "file_name": "test-c.json",
                "matched_local_title": "",
            }
        ],
    )

    report = apply_enrich_csv(csv_path, json_dir, dry_run=False)
    assert report.applied == 1

    updated = json.loads((json_dir / "test-c.json").read_text(encoding="utf-8"))
    assert updated["subjects"] == ["영어", "수학"]
    assert updated["last_verified_at"] == "2026-09-01"
    assert "A3 반영" in updated["source_note"]


def _write_csv_with_detail(path: Path, rows: list[dict[str, str]]) -> None:
    fields = [
        "name",
        "address",
        "proposed_subjects",
        "proposed_subject_detail",
        "website_url",
        "blog_url",
        "proposed_phone",
        "confidence",
        "evidence",
        "source_note",
        "file_name",
        "matched_local_title",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def test_apply_fills_subject_detail_from_column(tmp_path):
    json_dir = tmp_path / "academies"
    json_dir.mkdir()
    _write_academy(
        json_dir / "piano.json",
        {"name": "뮤즈피아노교습소", "subjects": None, "subject_detail": None},
    )
    csv_path = tmp_path / "proposals.csv"
    _write_csv_with_detail(
        csv_path,
        [
            {
                "name": "뮤즈피아노교습소",
                "proposed_subjects": "기타",
                "proposed_subject_detail": "피아노",
                "confidence": "high",
                "file_name": "piano.json",
            }
        ],
    )

    report = apply_enrich_csv(csv_path, json_dir, dry_run=False)
    assert report.applied == 1
    updated = json.loads((json_dir / "piano.json").read_text(encoding="utf-8"))
    assert updated["subjects"] == ["기타"]
    assert updated["subject_detail"] == "피아노"


def test_apply_derives_subject_detail_from_evidence_category(tmp_path):
    json_dir = tmp_path / "academies"
    json_dir.mkdir()
    _write_academy(
        json_dir / "art.json",
        {"name": "소년공방미술학원", "subjects": None, "subject_detail": None},
    )
    # 기존 CSV에는 proposed_subject_detail 컬럼이 없다 — evidence의 category=에서 파생.
    csv_path = tmp_path / "proposals.csv"
    _write_csv(
        csv_path,
        [
            _row(
                name="소년공방미술학원",
                proposed_subjects="기타",
                evidence="subjects_from=category; category=미술교육 | local title=소년공방미술학원",
                confidence="high",
                file_name="art.json",
            )
        ],
    )

    report = apply_enrich_csv(csv_path, json_dir, dry_run=False)
    assert report.applied == 1
    updated = json.loads((json_dir / "art.json").read_text(encoding="utf-8"))
    assert updated["subjects"] == ["기타"]
    assert updated["subject_detail"] == "미술"


def test_apply_skips_subject_detail_when_no_etc_bucket(tmp_path):
    json_dir = tmp_path / "academies"
    json_dir.mkdir()
    _write_academy(
        json_dir / "math.json",
        {"name": "가온수학", "subjects": None, "subject_detail": None},
    )
    csv_path = tmp_path / "proposals.csv"
    _write_csv_with_detail(
        csv_path,
        [
            {
                "name": "가온수학",
                "proposed_subjects": "수학",
                "proposed_subject_detail": "피아노",
                "confidence": "high",
                "file_name": "math.json",
            }
        ],
    )

    report = apply_enrich_csv(csv_path, json_dir, dry_run=False)
    assert report.applied == 1
    updated = json.loads((json_dir / "math.json").read_text(encoding="utf-8"))
    assert updated["subjects"] == ["수학"]
    # subjects에 기타가 없으므로 subject_detail은 채우지 않는다 (결합 규칙).
    assert updated.get("subject_detail") is None


def test_apply_today_and_note_override(tmp_path):
    from datetime import date

    json_dir = tmp_path / "academies"
    json_dir.mkdir()
    _write_academy(
        json_dir / "piano.json",
        {"name": "뮤즈피아노교습소", "subjects": None, "subject_detail": None},
    )
    csv_path = tmp_path / "proposals.csv"
    _write_csv_with_detail(
        csv_path,
        [
            {
                "name": "뮤즈피아노교습소",
                "proposed_subjects": "기타",
                "proposed_subject_detail": "피아노",
                "confidence": "high",
                "file_name": "piano.json",
            }
        ],
    )

    report = apply_enrich_csv(
        csv_path,
        json_dir,
        dry_run=False,
        source_note="세부 라벨 반영 2026-09-11",
        verified_at=date(2026, 9, 11),
    )
    assert report.applied == 1
    updated = json.loads((json_dir / "piano.json").read_text(encoding="utf-8"))
    assert updated["last_verified_at"] == "2026-09-11"
    assert "세부 라벨 반영 2026-09-11" in updated["source_note"]


def test_rollback_clears_bad_urls_and_name_mismatch_subjects(tmp_path):
    json_dir = tmp_path / "academies"
    json_dir.mkdir()
    _write_academy(
        json_dir / "bad.json",
        {
            "name": "비긴잉글리시학원",
            "website_url": "https://www.instagram.com/clue_english_/",
            "blog_url": None,
            "subjects": ["영어"],
            "source_note": "원본; 네이버 API HUB 지역·블로그 검색 A3 반영 (category 과목·URL), 2026-09-01",
            "last_verified_at": "2026-09-01",
        },
    )

    csv_path = tmp_path / "proposals.csv"
    _write_csv(
        csv_path,
        [
            _row(
                name="비긴잉글리시학원",
                confidence="high",
                website_url="https://www.instagram.com/clue_english_/",
                file_name="bad.json",
                matched_local_title="클루잉글리시",
            )
        ],
    )

    report = rollback_enrich_urls(csv_path, json_dir, dry_run=False)
    assert report.rolled_back == 1

    updated = json.loads((json_dir / "bad.json").read_text(encoding="utf-8"))
    assert updated["website_url"] is None
    assert updated["subjects"] is None
    assert "A3 URL 롤백" in updated["source_note"]
