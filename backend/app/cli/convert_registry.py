"""나이스 학원민원서비스(acaInsTiInfo) 응답을 정본 JSON 파일로 변환하는 CLI.

공식 등록 데이터(등록번호·학원명·주소·개원년도)로 정본 파일의 뼈대를 만들고,
나머지 필드는 전부 null(미확인)로 남긴다. 과목/학교급 등은 수동 큐레이션 대상.

입력: open.neis.go.kr의 acaInsTiInfo 응답 JSON(원 응답 그대로) 또는 row 객체 배열.
(경기도교육청 코드 J10, 행정구역명 '하남시'로 조회한 결과를 저장해 사용)

사용:
    cd backend
    uv run python -m app.cli.convert_registry <입력.json> ../data/academies [--filter 미사]

이미 존재하는 학원(등록번호 또는 이름+주소 매치)의 파일은 절대 덮어쓰지 않고
차이만 리포트한다 — 수동 큐레이션 데이터 보호.
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

from pydantic import ValidationError

from app.schemas.academy import AcademyRecord

OPEN_STATUS = "개원"


def extract_rows(payload: object) -> list[dict]:
    """NEIS 원 응답(dict) 또는 row 객체 배열(list)을 모두 허용한다."""
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        blocks = payload.get("acaInsTiInfo")
        if isinstance(blocks, list):
            rows: list[dict] = []
            for block in blocks:
                if isinstance(block, dict) and isinstance(block.get("row"), list):
                    rows.extend(r for r in block["row"] if isinstance(r, dict))
            return rows
    raise ValueError(
        "지원하지 않는 입력 형식 (acaInsTiInfo 응답 또는 row 배열이어야 함)"
    )


def row_to_record(row: dict, today: date) -> AcademyRecord:
    """NEIS row → 정본 레코드. 공식 등록 데이터가 제공하는 필드만 채운다."""
    address_parts = [
        str(row.get("FA_RDNMA") or "").strip(),
        str(row.get("FA_RDNDA") or "").strip(),
    ]
    address = " ".join(part for part in address_parts if part) or None

    established_year = None
    estbl = str(row.get("ESTBL_YMD") or "").strip()
    if len(estbl) >= 4 and estbl[:4].isdigit():
        established_year = int(estbl[:4])

    return AcademyRecord(
        registration_number=str(row.get("ACA_ASNUM") or "").strip() or None,
        name=str(row.get("ACA_NM") or "").strip(),
        address=address,
        established_year=established_year,
        source_note=f"나이스 학원민원서비스(acaInsTiInfo), {today.isoformat()} 변환",
        last_verified_at=today,
    )


def slug_for(record: AcademyRecord) -> str:
    base = ""
    if record.registration_number:
        base = re.sub(r"[^0-9a-zA-Z]+", "-", record.registration_number).strip("-")
    if not base:
        digest = hashlib.sha1(
            f"{record.name}|{record.address}".encode()
        ).hexdigest()
        base = digest[:10]
    return f"registry-{base.lower()}"


def load_existing_keys(
    output_dir: Path,
) -> tuple[dict[str, Path], dict[tuple[str, str | None], Path]]:
    """기존 정본 파일들의 자연키를 수집한다 (엄격 검증은 importer의 몫)."""
    by_registration: dict[str, Path] = {}
    by_name_address: dict[tuple[str, str | None], Path] = {}
    for path in sorted(output_dir.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(raw, dict):
            continue
        registration = raw.get("registration_number")
        if isinstance(registration, str) and registration.strip():
            by_registration[registration.strip()] = path
        name = raw.get("name")
        if isinstance(name, str) and name.strip():
            address = raw.get("address")
            address = address.strip() if isinstance(address, str) else None
            by_name_address[(name.strip(), address or None)] = path
    return by_registration, by_name_address


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="NEIS 학원민원서비스 응답을 정본 JSON 파일로 변환한다."
    )
    parser.add_argument("input", type=Path, help="NEIS 응답 JSON 파일")
    parser.add_argument(
        "output_dir", type=Path, help="정본 디렉터리 (예: ../data/academies)"
    )
    parser.add_argument(
        "--filter",
        dest="keyword",
        default=None,
        help="학원명 또는 주소에 이 키워드가 포함된 행만 변환 (예: 미사)",
    )
    parser.add_argument(
        "--include-all",
        action="store_true",
        help="등록상태가 '개원'이 아닌 행(폐원/휴원 등)도 포함한다",
    )
    args = parser.parse_args(argv)

    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        rows = extract_rows(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: 입력을 읽을 수 없습니다 — {exc}", file=sys.stderr)
        return 1
    if not args.output_dir.is_dir():
        print(f"ERROR: 출력 디렉터리가 없습니다: {args.output_dir}", file=sys.stderr)
        return 1

    today = date.today()
    by_registration, by_name_address = load_existing_keys(args.output_dir)
    created = skipped_existing = skipped_filtered = errors = 0

    for row in rows:
        status = str(row.get("REG_STTUS_NM") or "").strip()
        if not args.include_all and status and status != OPEN_STATUS:
            skipped_filtered += 1
            continue
        try:
            record = row_to_record(row, today)
        except ValidationError as exc:
            print(f"ERROR: 행 변환 실패 ({row.get('ACA_NM')!r}) — {exc}", file=sys.stderr)
            errors += 1
            continue

        if args.keyword and not (
            args.keyword in record.name or args.keyword in (record.address or "")
        ):
            skipped_filtered += 1
            continue

        existing = None
        if record.registration_number:
            existing = by_registration.get(record.registration_number)
        if existing is None:
            existing = by_name_address.get((record.name, record.address))
        if existing is not None:
            skipped_existing += 1
            existing_raw = json.loads(existing.read_text(encoding="utf-8"))
            diffs = [
                f"{key}: 파일={existing_raw.get(key)!r} 공공데이터={value!r}"
                for key, value in (
                    ("name", record.name),
                    ("address", record.address),
                )
                if existing_raw.get(key) != value
            ]
            if diffs:
                print(f"DIFF {existing.name}: " + "; ".join(diffs))
            continue

        target = args.output_dir / f"{slug_for(record)}.json"
        suffix = 2
        while target.exists():
            target = args.output_dir / f"{slug_for(record)}-{suffix}.json"
            suffix += 1
        target.write_text(
            json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )
        if record.registration_number:
            by_registration[record.registration_number] = target
        by_name_address[(record.name, record.address)] = target
        created += 1
        print(f"CREATED {target.name}: {record.name}")

    print(
        f"완료: 생성 {created}, 기존 스킵 {skipped_existing}, "
        f"필터 제외 {skipped_filtered}, 오류 {errors}"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
