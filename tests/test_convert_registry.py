import json
from pathlib import Path

from app.cli import convert_registry
from app.schemas.academy import AcademyRecord

NEIS_SAMPLE = Path(__file__).resolve().parent / "fixtures" / "neis_sample.json"


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
