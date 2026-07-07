import json
from pathlib import Path

from sqlalchemy import select

from app.cli import import_academies
from app.models.academy import Academy
from app.services import academy_import_service

REPO_ROOT = Path(__file__).resolve().parents[1]
SHIPPED_FIXTURES = REPO_ROOT / "data" / "academies"


def write_record(directory: Path, filename: str, **overrides) -> None:
    record = {
        "name": "테스트수학학원",
        "address": "경기도 하남시 미사강변대로 10",
    }
    record.update(overrides)
    (directory / filename).write_text(
        json.dumps(record, ensure_ascii=False), encoding="utf-8"
    )


def load_and_import(db, directory: Path):
    load = academy_import_service.load_records(directory)
    assert load.errors == []
    return academy_import_service.import_records(
        db, [record for _, record in load.records]
    )


def all_rows(db) -> list[Academy]:
    return list(db.scalars(select(Academy)))


def test_import_shipped_fixtures(db_session):
    """저장소에 실린 정본 픽스처가 항상 유효함을 CI가 보장한다."""
    report = load_and_import(db_session, SHIPPED_FIXTURES)
    assert report.created == 4
    assert report.updated == 0
    assert report.orphans == []


def test_reimport_is_idempotent(db_session):
    load_and_import(db_session, SHIPPED_FIXTURES)
    report = load_and_import(db_session, SHIPPED_FIXTURES)
    assert report.created == 0
    assert report.updated == 0
    assert report.unchanged == 4


def test_upsert_by_registration_number_updates_fields(tmp_path, db_session):
    write_record(tmp_path, "a.json", registration_number="R-1", phone="031-000-0001")
    load_and_import(db_session, tmp_path)

    write_record(
        tmp_path,
        "a.json",
        registration_number="R-1",
        name="테스트수학학원 리브랜딩",
        phone="031-000-0002",
    )
    report = load_and_import(db_session, tmp_path)
    assert report.updated == 1
    assert report.created == 0
    rows = all_rows(db_session)
    assert len(rows) == 1
    assert rows[0].name == "테스트수학학원 리브랜딩"
    assert rows[0].phone == "031-000-0002"


def test_upsert_fallback_name_address(tmp_path, db_session):
    write_record(tmp_path, "a.json", phone="031-000-0001")
    load_and_import(db_session, tmp_path)

    write_record(tmp_path, "a.json", phone="031-000-0009")
    report = load_and_import(db_session, tmp_path)
    assert report.updated == 1
    rows = all_rows(db_session)
    assert len(rows) == 1
    assert rows[0].phone == "031-000-0009"


def test_name_address_match_backfills_registration_number(tmp_path, db_session):
    write_record(tmp_path, "a.json")
    load_and_import(db_session, tmp_path)

    write_record(tmp_path, "a.json", registration_number="R-99")
    report = load_and_import(db_session, tmp_path)
    assert report.created == 0
    assert report.updated == 1
    rows = all_rows(db_session)
    assert len(rows) == 1
    assert rows[0].registration_number == "R-99"


def test_full_overwrite_writes_nulls(tmp_path, db_session):
    """sync 의미론: 파일에서 값이 null로 바뀌면 DB도 NULL이 된다."""
    write_record(tmp_path, "a.json", phone="031-000-0001", shuttle_available=True)
    load_and_import(db_session, tmp_path)

    write_record(tmp_path, "a.json", phone=None, shuttle_available=None)
    load_and_import(db_session, tmp_path)
    row = all_rows(db_session)[0]
    assert row.phone is None
    assert row.shuttle_available is None


def test_unknown_key_rejected(tmp_path):
    write_record(tmp_path, "a.json", rating=4.5)  # 평가 필드는 스키마에 없다
    load = academy_import_service.load_records(tmp_path)
    assert load.records == []
    assert len(load.errors) == 1
    assert "a.json" in load.errors[0]


def test_invalid_json_reports_error(tmp_path):
    (tmp_path / "broken.json").write_text("{not json", encoding="utf-8")
    load = academy_import_service.load_records(tmp_path)
    assert load.records == []
    assert len(load.errors) == 1


def test_duplicate_registration_number_across_files_fails(tmp_path):
    write_record(tmp_path, "a.json", registration_number="R-1")
    write_record(
        tmp_path,
        "b.json",
        registration_number="R-1",
        name="다른수학학원",
        address="경기도 하남시 미사대로 20",
    )
    load = academy_import_service.load_records(tmp_path)
    assert len(load.errors) == 1
    assert "registration_number 중복" in load.errors[0]


def test_duplicate_name_address_across_files_fails(tmp_path):
    write_record(tmp_path, "a.json")
    write_record(tmp_path, "b.json")
    load = academy_import_service.load_records(tmp_path)
    assert len(load.errors) == 1
    assert "(name, address) 중복" in load.errors[0]


def test_orphan_reported_when_file_removed(tmp_path, db_session):
    write_record(tmp_path, "a.json", registration_number="R-1")
    write_record(
        tmp_path,
        "b.json",
        registration_number="R-2",
        name="사라질수학학원",
        address="경기도 하남시 미사대로 30",
    )
    load_and_import(db_session, tmp_path)

    (tmp_path / "b.json").unlink()
    report = load_and_import(db_session, tmp_path)
    assert len(report.orphans) == 1
    assert "사라질수학학원" in report.orphans[0]
    # 삭제는 하지 않는다 — 리포트만.
    assert len(all_rows(db_session)) == 2


def test_dry_run_validates_without_db(tmp_path, capsys):
    """--dry-run은 DB 접속 없이 검증만 수행한다."""
    write_record(tmp_path, "a.json")
    exit_code = import_academies.main([str(tmp_path), "--dry-run"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "1개 파일 검증 통과" in out
    assert "dry-run" in out


def test_cli_returns_1_on_validation_error(tmp_path, capsys):
    write_record(tmp_path, "a.json", rating=5)
    exit_code = import_academies.main([str(tmp_path), "--dry-run"])
    assert exit_code == 1
    assert "검증 실패" in capsys.readouterr().err
