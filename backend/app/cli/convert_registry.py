"""나이스 학원민원서비스(acaInsTiInfo) / 경기데이터드림 "경기도_학원 및 교습소
현황" 응답을 정본 JSON 파일로 변환하는 CLI.

공식 등록 데이터로 정본 파일의 뼈대를 만들고, 나머지 필드는 전부 null(미확인)로
남긴다. 과목/학교급 등은 수동 큐레이션 대상.

두 소스는 상호보완적이다:
- neis (acaInsTiInfo): 등록번호·개원년도·폐원상태가 강점
- gg   (경기데이터드림/공공데이터포털 "경기도_학원 및 교습소 현황"): 전화번호·
  좌표(위경도)·교습과정명(과목 힌트)이 강점

**gg 소스 필드명은 2026-07-08 실제 API 응답(`openapi.gg.go.kr/TninsttInstutM`)으로
확정됐다** (`FACLT_NM`/`REFINE_ROADNM_ADDR`/`TELNO`/`REFINE_WGS84_LAT`/
`REFINE_WGS84_LOGT`/`CRSE_CLASS_NM` 등, `docs/decision-log.md` 참고). 이 API는
`Type=json`을 줘도 XML로 응답하므로 `.xml` 입력도 지원한다.

입력 봉투(envelope)는 다음 4가지를 모두 인식한다: row 객체의 bare 배열 /
나이스류 `{"...": [{"head": [...]}, {"row": [...]}]}` / 공공데이터포털 표준
`{"response": {"body": {"items": {"item": [...]}}}}` / gg의 XML 응답
(`<서비스명><head>...</head><row>...</row>...</서비스명>`, 자동으로 나이스류
구조로 변환되어 처리된다).

사용:
    cd backend
    uv run python -m app.cli.convert_registry <입력.json> ../data/academies \\
        --source neis --filter 미사

    uv run python -m app.cli.convert_registry <입력.json> ../data/academies \\
        --source gg --filter 미사 --course-keyword 수학 --enrich

이미 존재하는 학원(등록번호 또는 이름+주소 매치)의 파일은 기본적으로 절대
덮어쓰지 않고 차이만 리포트한다. `--enrich`를 주면 그 대신 **null 필드만** 새
값으로 채운다(이미 채워진 값은 절대 덮어쓰지 않음) — 나이스로 먼저 골격을
만들고 경기데이터드림으로 전화번호·좌표를 보강하는 식의 워크플로를 지원한다.
"""

import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

from pydantic import ValidationError

from app.schemas.academy import AcademyRecord

# 상태 필드 값 자체를 소스별로 정확히 알 수 없으므로(neis="개원"/"폐원"이 확인된 전부),
# "개원과 같다"가 아니라 "폐원류 키워드를 포함하지 않는다"로 판단한다 — 미확인 소스의
# 상태 값이 다른 어휘를 쓰더라도 개원 학원을 안전하게 기본 포함하기 위함.
_CLOSED_STATUS_KEYWORDS = ("폐원", "폐업", "휴원")


def _first_present(row: dict, *keys: str) -> str | None:
    """여러 후보 키 중 처음으로 비어있지 않은 값을 반환한다."""
    for key in keys:
        value = row.get(key)
        if value is None:
            continue
        value = str(value).strip()
        if value:
            return value
    return None


def extract_rows(payload: object) -> list[dict]:
    """행 리스트를 추출한다. 소스에 무관하게 다음 3가지 봉투를 인식한다:

    1) row 객체의 bare 배열
    2) 나이스/학교계열: {"<root>": [{"head": [...]}, {"row": [...]}]}
    3) 공공데이터포털 표준: {"response": {"body": {"items": {"item": [...] | {...}}}}}
    """
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        response = payload.get("response")
        if isinstance(response, dict):
            body = response.get("body")
            if isinstance(body, dict):
                items = body.get("items")
                if isinstance(items, dict):
                    item = items.get("item")
                    if isinstance(item, list):
                        return [row for row in item if isinstance(row, dict)]
                    if isinstance(item, dict):
                        return [item]
                elif isinstance(items, list):
                    return [row for row in items if isinstance(row, dict)]
        for blocks in payload.values():
            if not isinstance(blocks, list):
                continue
            rows: list[dict] = []
            found_row_block = False
            for block in blocks:
                if isinstance(block, dict) and isinstance(block.get("row"), list):
                    rows.extend(r for r in block["row"] if isinstance(r, dict))
                    found_row_block = True
            if found_row_block:
                return rows
    raise ValueError(
        "지원하지 않는 입력 형식 (row 배열 / head-row 래퍼 / "
        "공공데이터포털 response.body.items 래퍼 중 하나여야 함)"
    )


def parse_xml_payload(text: str) -> dict:
    """gg 소스처럼 XML로 응답하는 공공데이터 API 출력을 나이스류 봉투로 변환한다.

    `<서비스명><head>...</head><row>...</row><row>...</row></서비스명>` 형태를
    `{"서비스명": [{"head": {...}}, {"row": [...]}]}`로 바꿔, 기존 `extract_rows()`가
    처리하는 "나이스류" 케이스를 그대로 재사용할 수 있게 한다.
    """
    root = ET.fromstring(text)
    rows = [
        {child.tag: (child.text.strip() if child.text else None) for child in row_el}
        for row_el in root.findall("row")
    ]
    return {root.tag: [{"head": {}}, {"row": rows}]}


def neis_row_to_record(row: dict, today: date) -> AcademyRecord:
    """NEIS acaInsTiInfo row → 정본 레코드. 공식 등록 데이터가 제공하는 필드만 채운다."""
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


def gg_row_to_record(row: dict, today: date) -> AcademyRecord:
    """경기데이터드림 '학원 및 교습소 현황' row → 정본 레코드.

    필드명은 실제 API 응답(`openapi.gg.go.kr/TninsttInstutM`, 2026-07-08)으로
    확정됐다 (`docs/decision-log.md` 참고). 다른 유사 공공데이터셋 대비 하위호환을
    위해 기존 한글 후보 키도 폴백으로 남겨둔다.
    """
    name = _first_present(row, "FACLT_NM", "시설명", "학원교습소명", "학원명")
    address = _first_present(
        row, "REFINE_ROADNM_ADDR", "REFINE_LOTNO_ADDR", "도로명주소", "지번주소"
    )
    phone = _first_present(row, "TELNO", "전화번호")
    latitude = _first_present(row, "REFINE_WGS84_LAT", "위도")
    longitude = _first_present(row, "REFINE_WGS84_LOGT", "경도")

    return AcademyRecord(
        name=name or "",
        address=address,
        phone=phone,
        latitude=latitude,  # type: ignore[arg-type]  # pydantic이 숫자 문자열을 float로 강제 변환
        longitude=longitude,  # type: ignore[arg-type]
        source_note=f"경기데이터드림(학원 및 교습소 현황), {today.isoformat()} 변환",
        last_verified_at=today,
    )


def _status_of(row: dict) -> str | None:
    """등록/영업 상태류 필드를 소스 무관하게 찾는다 (필드가 없으면 None)."""
    return _first_present(
        row, "REG_STTUS_NM", "등록상태", "영업상태명", "운영상태명"
    )


def _is_closed_status(status: str) -> bool:
    return any(keyword in status for keyword in _CLOSED_STATUS_KEYWORDS)


def _course_keyword_match(row: dict, keyword: str) -> bool:
    """교습과정명류 필드에 keyword가 포함되는지 확인한다 (소스 무관하게 시도)."""
    course = _first_present(row, "CRSE_CLASS_NM", "교습과정명", "교습과정", "LE_CRSE_NM")
    return course is not None and keyword in course


SOURCE_ROW_TO_RECORD = {
    "neis": neis_row_to_record,
    "gg": gg_row_to_record,
}


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


def _fill_null_fields(existing_raw: dict, record: AcademyRecord) -> list[str]:
    """existing_raw에서 null인 필드만 record 값으로 채운다 (in-place). 채운 필드명 리스트 반환."""
    filled: list[str] = []
    for field_name, value in record.model_dump(mode="json").items():
        if value is None:
            continue
        if existing_raw.get(field_name) is None:
            existing_raw[field_name] = value
            filled.append(field_name)
    return filled


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "나이스 학원민원서비스 또는 경기데이터드림 학원/교습소 현황 응답을 "
            "정본 JSON 파일로 변환한다."
        )
    )
    parser.add_argument("input", type=Path, help="원 응답 파일 (JSON 또는 XML)")
    parser.add_argument(
        "output_dir", type=Path, help="정본 디렉터리 (예: ../data/academies)"
    )
    parser.add_argument(
        "--source",
        choices=sorted(SOURCE_ROW_TO_RECORD),
        default="neis",
        help="입력 데이터 출처 (기본: neis)",
    )
    parser.add_argument(
        "--filter",
        dest="keyword",
        default=None,
        help="학원명 또는 주소에 이 키워드가 포함된 행만 변환 (예: 미사)",
    )
    parser.add_argument(
        "--course-keyword",
        dest="course_keyword",
        default=None,
        help="교습과정명류 필드에 이 키워드가 포함된 행만 변환 (예: 수학; gg 소스에서 특히 유용)",
    )
    parser.add_argument(
        "--include-all",
        action="store_true",
        help="폐원/폐업/휴원 등 종료 상태로 보이는 행도 포함한다",
    )
    parser.add_argument(
        "--enrich",
        action="store_true",
        help=(
            "기존 파일과 매치되면 diff만 보고하는 대신, null인 필드만 채워 "
            "갱신한다 (이미 채워진 값은 절대 덮어쓰지 않음)"
        ),
    )
    args = parser.parse_args(argv)

    try:
        text = args.input.read_text(encoding="utf-8")
        is_xml = args.input.suffix.lower() == ".xml" or text.lstrip().startswith("<")
        payload = parse_xml_payload(text) if is_xml else json.loads(text)
        rows = extract_rows(payload)
    except (OSError, json.JSONDecodeError, ET.ParseError, ValueError) as exc:
        print(f"ERROR: 입력을 읽을 수 없습니다 — {exc}", file=sys.stderr)
        return 1
    if not args.output_dir.is_dir():
        print(f"ERROR: 출력 디렉터리가 없습니다: {args.output_dir}", file=sys.stderr)
        return 1

    row_to_record = SOURCE_ROW_TO_RECORD[args.source]

    today = date.today()
    by_registration, by_name_address = load_existing_keys(args.output_dir)
    created = skipped_existing = skipped_filtered = enriched = errors = 0

    for row in rows:
        status = _status_of(row)
        if not args.include_all and status and _is_closed_status(status):
            skipped_filtered += 1
            continue
        try:
            record = row_to_record(row, today)
        except ValidationError as exc:
            row_name = _first_present(
                row, "ACA_NM", "FACLT_NM", "시설명", "학원명", "학원교습소명"
            )
            print(f"ERROR: 행 변환 실패 ({row_name!r}) — {exc}", file=sys.stderr)
            errors += 1
            continue

        if args.keyword and not (
            args.keyword in record.name or args.keyword in (record.address or "")
        ):
            skipped_filtered += 1
            continue
        if args.course_keyword and not _course_keyword_match(row, args.course_keyword):
            skipped_filtered += 1
            continue

        existing = None
        if record.registration_number:
            existing = by_registration.get(record.registration_number)
        if existing is None:
            existing = by_name_address.get((record.name, record.address))

        if existing is not None:
            if args.enrich:
                existing_raw = json.loads(existing.read_text(encoding="utf-8"))
                filled = _fill_null_fields(existing_raw, record)
                if filled:
                    existing.write_text(
                        json.dumps(existing_raw, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
                    enriched += 1
                    print(f"ENRICHED {existing.name}: {', '.join(filled)}")
                else:
                    skipped_existing += 1
                continue
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
        f"완료: 생성 {created}, 보강 {enriched}, 기존 스킵 {skipped_existing}, "
        f"필터 제외 {skipped_filtered}, 오류 {errors}"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
