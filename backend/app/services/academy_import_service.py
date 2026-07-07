"""정본 데이터 파일(data/academies/*.json) → DB 임포트 로직.

정본은 git의 JSON 파일이고 DB는 파생 저장소다. 임포트는 sync 의미론을 따른다:
매치된 행은 파일 내용으로 전 필드를 덮어쓴다 (null 포함).
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.academy import Academy
from app.repositories import academy_repository
from app.schemas.academy import AcademyRecord

_RECORD_FIELDS = tuple(AcademyRecord.model_fields.keys())


@dataclass
class LoadResult:
    records: list[tuple[Path, AcademyRecord]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class ImportReport:
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    warnings: list[str] = field(default_factory=list)
    orphans: list[str] = field(default_factory=list)


def load_records(directory: Path) -> LoadResult:
    """디렉터리의 모든 JSON을 검증한다. DB에는 접속하지 않는다."""
    result = LoadResult()
    if not directory.is_dir():
        result.errors.append(f"디렉터리가 없습니다: {directory}")
        return result
    paths = sorted(directory.glob("*.json"))
    if not paths:
        result.errors.append(f"JSON 파일이 없습니다: {directory}")
        return result

    seen_registration: dict[str, Path] = {}
    seen_name_address: dict[tuple[str, str | None], Path] = {}
    for path in paths:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            result.errors.append(f"{path.name}: JSON 파싱 실패 — {exc}")
            continue
        try:
            record = AcademyRecord.model_validate(raw)
        except ValidationError as exc:
            result.errors.append(f"{path.name}: 스키마 검증 실패 — {exc}")
            continue

        if record.registration_number is not None:
            dup = seen_registration.get(record.registration_number)
            if dup is not None:
                result.errors.append(
                    f"{path.name}: registration_number 중복 — "
                    f"{dup.name}과 같은 등록번호 ({record.registration_number})"
                )
                continue
            seen_registration[record.registration_number] = path

        key = (record.name, record.address)
        dup = seen_name_address.get(key)
        if dup is not None:
            result.errors.append(
                f"{path.name}: (name, address) 중복 — {dup.name}과 같은 학원 "
                f"({record.name} / {record.address})"
            )
            continue
        seen_name_address[key] = path

        result.records.append((path, record))
    return result


def import_records(db: Session, records: list[AcademyRecord]) -> ImportReport:
    """검증된 레코드를 단일 트랜잭션으로 업서트한다."""
    report = ImportReport()
    touched_ids: set[int] = set()
    try:
        for record in records:
            existing = _find_existing(db, record, report)
            if existing is None:
                academy = Academy()
                _apply_record(academy, record)
                db.add(academy)
                db.flush()
                report.created += 1
                touched_ids.add(academy.id)
            else:
                if _apply_record(existing, record):
                    report.updated += 1
                else:
                    report.unchanged += 1
                touched_ids.add(existing.id)
        db.flush()
        for row in academy_repository.list_all(db):
            if row.id not in touched_ids:
                report.orphans.append(
                    f"id={row.id} name={row.name} address={row.address}"
                )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return report


def _find_existing(
    db: Session, record: AcademyRecord, report: ImportReport
) -> Academy | None:
    """자연키 매치: 등록번호 우선, 없으면 (name, address).

    등록번호가 파일에 새로 추가된 경우 (name, address) 매치가 잡아서
    기존 행에 등록번호를 backfill하게 된다.
    """
    by_registration = None
    if record.registration_number is not None:
        by_registration = academy_repository.find_by_registration_number(
            db, record.registration_number
        )
    by_name_address = academy_repository.find_by_name_and_address(
        db, record.name, record.address
    )
    if (
        by_registration is not None
        and by_name_address is not None
        and by_registration.id != by_name_address.id
    ):
        report.warnings.append(
            f"{record.name}: 등록번호 매치(id={by_registration.id})와 "
            f"이름+주소 매치(id={by_name_address.id})가 서로 다른 행입니다 — "
            f"등록번호 매치를 사용합니다"
        )
        return by_registration
    return by_registration or by_name_address


def _apply_record(academy: Academy, record: AcademyRecord) -> bool:
    """파일 내용으로 전 필드를 덮어쓴다(null 포함). 실제 변경 여부를 반환."""
    changed = False
    for field_name in _RECORD_FIELDS:
        value = getattr(record, field_name)
        if isinstance(value, list):
            # JSON 컬럼은 in-place 변경이 추적되지 않으므로 항상 새 리스트를 할당
            value = list(value)
        if getattr(academy, field_name) != value:
            setattr(academy, field_name, value)
            changed = True
    return changed
