"""export_academies service."""

import json
from pathlib import Path

from app.services import academy_export_service, academy_import_service


def write_record(directory: Path, filename: str, **overrides) -> None:
    record = {
        "name": "테스트수학학원",
        "address": "경기도 하남시 미사강변대로 10",
    }
    record.update(overrides)
    (directory / filename).write_text(
        json.dumps(record, ensure_ascii=False), encoding="utf-8"
    )


def test_export_writes_json_files(tmp_path, db_session):
    import_dir = tmp_path / "import"
    export_dir = tmp_path / "export"
    import_dir.mkdir()
    write_record(import_dir, "a.json", registration_number="R-export-1")
    load = academy_import_service.load_records(import_dir)
    academy_import_service.import_records(
        db_session, [record for _, record in load.records]
    )

    report = academy_export_service.export_records(db_session, export_dir)
    assert report.written == 1
    assert report.errors == []

    files = list(export_dir.glob("*.json"))
    assert len(files) == 1
    payload = json.loads(files[0].read_text(encoding="utf-8"))
    assert payload["registration_number"] == "R-export-1"
    assert payload["name"] == "테스트수학학원"


def test_export_roundtrip_reimports(tmp_path, db_session):
    import_dir = tmp_path / "import"
    export_dir = tmp_path / "export"
    import_dir.mkdir()
    write_record(
        import_dir,
        "a.json",
        registration_number="R-roundtrip",
        phone="031-111-2222",
        subjects=["수학"],
    )
    load = academy_import_service.load_records(import_dir)
    academy_import_service.import_records(
        db_session, [record for _, record in load.records]
    )

    academy_export_service.export_records(db_session, export_dir)
    reloaded = academy_import_service.load_records(export_dir)
    assert reloaded.errors == []
    assert len(reloaded.records) == 1
    record = reloaded.records[0][1]
    assert record.registration_number == "R-roundtrip"
    assert record.phone == "031-111-2222"
    assert record.subjects == ["수학"]
