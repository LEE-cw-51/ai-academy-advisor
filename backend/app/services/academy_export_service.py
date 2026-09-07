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
    """DB academies 행을 JSON 파일로 덤프한다.

    같은 경로를 재export할 때 DB에 없는 orphan `*.json`을 남기지 않도록,
    이번 실행에서 성공적으로 쓴 파일 집합 밖의 `*.json`은 삭제한다.
    """
    report = ExportReport()
    directory.mkdir(parents=True, exist_ok=True)
    written_names: set[str] = set()

    for row in academy_repository.list_all(db):
        try:
            payload = _record_to_dict(row)
            AcademyRecord.model_validate(payload)
            path = directory / _file_name_for(row)
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            written_names.add(path.name)
            report.written += 1
        except Exception as exc:  # noqa: BLE001 — 행 단위 실패를 모아 리포트
            report.errors.append(f"id={row.id} name={row.name}: {exc}")
            report.skipped += 1

    for stale in directory.glob("*.json"):
        if stale.name not in written_names:
            stale.unlink()
    return report
