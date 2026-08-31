"""enrich_academy_from_search CLI 통합 테스트 (네트워크 없이 --dry-run)."""

import csv
import json
from pathlib import Path

from app.cli import enrich_academy_from_search as cli
from app.services import academy_enrich_service


def write_record(directory: Path, filename: str, **overrides) -> None:
    record = {"name": "테스트수학학원", "address": "경기도 하남시 미사강변대로 10"}
    record.update(overrides)
    (directory / filename).write_text(
        json.dumps(record, ensure_ascii=False), encoding="utf-8"
    )


def test_dry_run_needs_no_credentials_and_writes_all_csv_columns(tmp_path):
    write_record(tmp_path, "a.json")
    output = tmp_path / "out.csv"

    exit_code = cli.main([str(tmp_path), "--dry-run", "--output", str(output)])

    assert exit_code == 0
    with output.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    # 지금까지 CSV에서 조용히 빠지던 두 컬럼이 실제로 채워져 있어야 한다.
    assert rows[0]["file_name"] == "a.json"
    assert rows[0]["matched_local_title"] != ""
    assert "proposed_phone" in rows[0]


def test_one_academy_failure_does_not_lose_other_rows(tmp_path, monkeypatch):
    write_record(tmp_path, "a-ok.json", name="정상학원")
    write_record(tmp_path, "b-boom.json", name="문제학원")
    output = tmp_path / "out.csv"

    real_enrich_one = academy_enrich_service.enrich_one

    def flaky_enrich_one(path, academy, local, blogs):
        if academy.name == "문제학원":
            raise RuntimeError("가짜 네트워크 에러")
        return real_enrich_one(path, academy, local, blogs)

    monkeypatch.setattr(academy_enrich_service, "enrich_one", flaky_enrich_one)

    exit_code = cli.main([str(tmp_path), "--dry-run", "--output", str(output)])

    assert exit_code == 0
    with output.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["name"] for row in rows] == ["정상학원"]


def test_dry_run_is_deterministic_across_runs(tmp_path):
    write_record(tmp_path, "a.json")
    output1, output2 = tmp_path / "out1.csv", tmp_path / "out2.csv"

    cli.main([str(tmp_path), "--dry-run", "--output", str(output1)])
    cli.main([str(tmp_path), "--dry-run", "--output", str(output2)])

    assert output1.read_text(encoding="utf-8-sig") == output2.read_text(
        encoding="utf-8-sig"
    )


class _EmptyNaverSettings:
    naver_client_id = ""
    naver_client_secret = ""
    naver_base_url = "https://naverapihub.apigw.ntruss.com"


def test_missing_credentials_without_dry_run_fails_fast(tmp_path, monkeypatch, capsys):
    # 로컬 backend/.env에 실제 자격증명이 있을 수 있으므로 monkeypatch.delenv가 아니라
    # get_settings() 자체를 대체해 "키 없음" 상태를 확실히 재현한다.
    monkeypatch.setattr(cli, "get_settings", lambda: _EmptyNaverSettings())
    write_record(tmp_path, "a.json")

    exit_code = cli.main([str(tmp_path), "--output", str(tmp_path / "out.csv")])

    assert exit_code == 1
    assert "NAVER_CLIENT_ID" in capsys.readouterr().err
