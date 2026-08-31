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
