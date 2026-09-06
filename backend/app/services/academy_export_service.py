"""운영 DB → JSON 덤프 (재해복구·백업용, git 정본 아님)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy.orm import Session

from app.repositories import academy_repository
from app.schemas.academy import AcademyRecord

_RECORD_FIELDS = tuple(AcademyRecord.model_fields.keys())


@dataclass
class ExportReport:
    written: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)


def _record_to_dict(row) -> dict:
    payload: dict = {}
    for field_name in _RECORD_FIELDS:
        value = getattr(row, field_name)
        if hasattr(value, "isoformat"):
            payload[field_name] = value.isoformat()
        else:
            payload[field_name] = value
    return payload


def _file_name_for(row) -> str:
    if row.registration_number:
        safe = row.registration_number.replace("/", "-").replace("\\", "-")
        return f"registry-{safe}.json"
    slug = str(row.id).zfill(8)
    return f"academy-{slug}.json"


def export_records(db: Session, directory: Path) -> ExportReport:
    """DB academies 행을 JSON 파일로 덤프한다."""
    report = ExportReport()
    directory.mkdir(parents=True, exist_ok=True)

    for row in academy_repository.list_all(db):
        try:
            payload = _record_to_dict(row)
            AcademyRecord.model_validate(payload)
            path = directory / _file_name_for(row)
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            report.written += 1
        except Exception as exc:  # noqa: BLE001 — 행 단위 실패를 모아 리포트
            report.errors.append(f"id={row.id} name={row.name}: {exc}")
            report.skipped += 1
    return report
