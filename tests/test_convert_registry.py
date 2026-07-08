import json
from pathlib import Path

from app.cli import convert_registry
from app.schemas.academy import AcademyRecord

NEIS_SAMPLE = Path(__file__).resolve().parent / "fixtures" / "neis_sample.json"
GG_SAMPLE = Path(__file__).resolve().parent / "fixtures" / "gg_sample.json"
GG_SAMPLE_XML = Path(__file__).resolve().parent / "fixtures" / "gg_sample.xml"


def read_all(directory: Path) -> dict[str, dict]:
    return {
        path.name: json.loads(path.read_text(encoding="utf-8"))
        for path in directory.glob("*.json")
    }


def test_convert_creates_canonical_files(tmp_path):
    exit_code = convert_registry.main([str(NEIS_SAMPLE), str(tmp_path)])
    assert exit_code == 0
    files = read_all(tmp_path)
    # 폐원 학원은 기본 제외 → 개원 2건만 생성
    assert len(files) == 2
    for data in files.values():
        # 정본 스키마의 모든 키가 존재하고 (미확인은 null), 그대로 검증을 통과해야 한다
        assert set(data.keys()) == set(AcademyRecord.model_fields.keys())
        AcademyRecord.model_validate(data)
    names = {data["name"] for data in files.values()}
    assert names == {"미사샘플수학학원(테스트)", "덕풍샘플영어학원(테스트)"}
    sample = next(
        data for data in files.values() if data["name"] == "미사샘플수학학원(테스트)"
    )
    assert sample["registration_number"] == "제0000-1호(테스트)"
    assert sample["address"] == "경기도 하남시 미사강변대로 1 2층 (테스트)"
    assert sample["established_year"] == 2018
    assert sample["subjects"] is None  # 과목은 수동 큐레이션 대상
    assert sample["level_high"] is None  # 미확인은 null로 남는다


def test_include_all_keeps_closed_academies(tmp_path):
    exit_code = convert_registry.main(
        [str(NEIS_SAMPLE), str(tmp_path), "--include-all"]
    )
    assert exit_code == 0
    assert len(read_all(tmp_path)) == 3


def test_filter_keyword(tmp_path):
    exit_code = convert_registry.main(
        [str(NEIS_SAMPLE), str(tmp_path), "--filter", "미사"]
    )
    assert exit_code == 0
    files = read_all(tmp_path)
    assert len(files) == 1
    assert next(iter(files.values()))["name"] == "미사샘플수학학원(테스트)"


def test_existing_files_never_overwritten(tmp_path):
    convert_registry.main([str(NEIS_SAMPLE), str(tmp_path)])
    before = read_all(tmp_path)
    # 손으로 큐레이션한 값을 흉내낸다
    target = next(iter(tmp_path.glob("*.json")))
    curated = json.loads(target.read_text(encoding="utf-8"))
    curated["level_high"] = True
    target.write_text(
        json.dumps(curated, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    exit_code = convert_registry.main([str(NEIS_SAMPLE), str(tmp_path)])
    assert exit_code == 0
    after = read_all(tmp_path)
    assert len(after) == len(before)
    assert after[target.name]["level_high"] is True  # 큐레이션 값 보존


def test_extract_rows_accepts_bare_list():
    rows = convert_registry.extract_rows([{"a": 1}, {"b": 2}])
    assert rows == [{"a": 1}, {"b": 2}]


def test_extract_rows_accepts_data_go_kr_envelope():
    payload = {
        "response": {
            "header": {"resultCode": "00"},
            "body": {"items": {"item": [{"a": 1}, {"b": 2}]}},
        }
    }
    assert convert_registry.extract_rows(payload) == [{"a": 1}, {"b": 2}]


def test_extract_rows_accepts_data_go_kr_envelope_single_item():
    # totalCount=1일 때 item이 배열이 아니라 단일 객체로 오는 경우가 있다.
    payload = {"response": {"body": {"items": {"item": {"a": 1}}}}}
    assert convert_registry.extract_rows(payload) == [{"a": 1}]


def test_gg_source_creates_canonical_files(tmp_path):
    exit_code = convert_registry.main(
        [str(GG_SAMPLE), str(tmp_path), "--source", "gg"]
    )
    assert exit_code == 0
    files = read_all(tmp_path)
    assert len(files) == 3
    for data in files.values():
        assert set(data.keys()) == set(AcademyRecord.model_fields.keys())
        AcademyRecord.model_validate(data)
        assert data["subjects"] is None  # gg 소스도 과목은 수동 큐레이션 대상
    sample = next(
        data
        for data in files.values()
        if data["name"] == "미사지에이지수학학원(테스트)"
    )
    assert sample["address"] == "경기도 하남시 미사강변대로 50"  # 도로명주소 우선
    assert sample["phone"] == "031-000-9001"
    assert sample["latitude"] == 37.56
    assert sample["longitude"] == 127.194
    assert sample["registration_number"] is None  # 이 데이터셋엔 등록번호가 없다
    assert "경기데이터드림" in sample["source_note"]


def test_gg_filter_and_course_keyword_combine_with_and(tmp_path):
    exit_code = convert_registry.main(
        [
            str(GG_SAMPLE),
            str(tmp_path),
            "--source",
            "gg",
            "--filter",
            "미사",
            "--course-keyword",
            "수학",
        ]
    )
    assert exit_code == 0
    files = read_all(tmp_path)
    # 미사+영어(과목 불일치), 덕풍+수학(지역 불일치) 둘 다 제외되고 미사+수학만 남는다
    assert len(files) == 1
    assert next(iter(files.values()))["name"] == "미사지에이지수학학원(테스트)"


def _write_curated(path: Path, **overrides) -> None:
    record = {
        "name": "미사지에이지수학학원(테스트)",
        "address": "경기도 하남시 미사강변대로 50",
        "phone": None,
        "latitude": None,
        "longitude": None,
        "tagline": "이미 확인된 소개(큐레이션됨)",
        "level_high": True,
    }
    record.update(overrides)
    path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")


def test_enrich_fills_only_null_fields(tmp_path):
    curated = tmp_path / "curated.json"
    _write_curated(curated)

    exit_code = convert_registry.main(
        [str(GG_SAMPLE), str(tmp_path), "--source", "gg", "--filter", "미사지에이지", "--enrich"]
    )
    assert exit_code == 0
    after = json.loads(curated.read_text(encoding="utf-8"))
    # 이전에 null이던 필드는 채워진다
    assert after["phone"] == "031-000-9001"
    assert after["latitude"] == 37.56
    assert after["longitude"] == 127.194
    # 이미 채워져 있던 값은 절대 덮어쓰지 않는다
    assert after["tagline"] == "이미 확인된 소개(큐레이션됨)"
    assert after["level_high"] is True
    # gg 소스가 값을 주지 않는 필드는 그대로 null
    assert after.get("level_elementary") is None
    # 정본 스키마 전체를 여전히 통과해야 한다
    AcademyRecord.model_validate(after)


def test_enrich_no_op_when_all_fields_already_present(tmp_path):
    curated = tmp_path / "curated.json"
    _write_curated(
        curated,
        phone="031-999-9999",
        latitude=1.0,
        longitude=2.0,
        source_note="이미 확인됨(전화 문의)",
        last_verified_at="2020-01-01",
    )
    before = curated.read_text(encoding="utf-8")

    exit_code = convert_registry.main(
        [str(GG_SAMPLE), str(tmp_path), "--source", "gg", "--filter", "미사지에이지", "--enrich"]
    )
    assert exit_code == 0
    assert curated.read_text(encoding="utf-8") == before


def test_parse_xml_payload_matches_head_row_envelope():
    payload = convert_registry.parse_xml_payload(GG_SAMPLE_XML.read_text(encoding="utf-8"))
    rows = convert_registry.extract_rows(payload)
    assert len(rows) == 2
    assert rows[0]["FACLT_NM"] == "미사엑스수학학원(테스트)"
    assert rows[0]["SIGUN_CD"] is None  # 빈 엘리먼트는 None


def test_gg_source_from_real_xml_response_shape(tmp_path):
    # 실제 API(openapi.gg.go.kr/TninsttInstutM)는 Type=json을 줘도 XML로 응답한다.
    exit_code = convert_registry.main(
        [str(GG_SAMPLE_XML), str(tmp_path), "--source", "gg"]
    )
    assert exit_code == 0
    files = read_all(tmp_path)
    assert len(files) == 2
    for data in files.values():
        assert set(data.keys()) == set(AcademyRecord.model_fields.keys())
        AcademyRecord.model_validate(data)
    sample = next(
        data for data in files.values() if data["name"] == "미사엑스수학학원(테스트)"
    )
    assert sample["address"] == "경기도 하남시 미사강변대로 100"  # 도로명주소 우선
    assert sample["phone"] == "031-000-9101"
    assert sample["latitude"] == 37.56
    assert sample["longitude"] == 127.194


def test_closed_status_excluded_by_default_regardless_of_vocabulary(tmp_path):
    input_file = tmp_path / "status_rows.json"
    input_file.write_text(
        json.dumps(
            [
                {
                    "시설명": "상태정상학원(테스트)",
                    "도로명주소": "경기도 하남시 상태정상로 1",
                    "등록상태": "영업",
                },
                {
                    "시설명": "상태폐업학원(테스트)",
                    "도로명주소": "경기도 하남시 상태폐업로 1",
                    "등록상태": "폐업",
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    default_dir = tmp_path / "default"
    default_dir.mkdir()
    convert_registry.main([str(input_file), str(default_dir), "--source", "gg"])
    files = read_all(default_dir)
    assert len(files) == 1
    assert next(iter(files.values()))["name"] == "상태정상학원(테스트)"

    include_all_dir = tmp_path / "include_all"
    include_all_dir.mkdir()
    convert_registry.main(
        [str(input_file), str(include_all_dir), "--source", "gg", "--include-all"]
    )
    assert len(read_all(include_all_dir)) == 2
