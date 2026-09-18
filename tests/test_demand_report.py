"""비식별 집계 수요 리포트 — 버킷만 세고, 작은 셀은 가리고, 원문은 절대 내보내지 않는다."""

from __future__ import annotations

import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.models.engagement import ClickLog, SearchHistory
from app.repositories import engagement_repository
from app.services import demand_report_service as svc

SINCE = datetime(2026, 8, 19, tzinfo=timezone.utc)
UNTIL = datetime(2026, 9, 19, tzinfo=timezone.utc)
T0 = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)

# /app 이 실제로 보내는 형태: "하남 미사 · 학년 · 과목 · 고민". 고민 문장은 사람이 쓴 것이라
# 리포트에 새면 안 된다 — 아래 마커 문장이 그 감시 대상이다.
SECRET = "우리 아이 이름은 김철수이고 미사중학교 2학년이에요"


def _searches(spec: list[tuple[str, int]]) -> list[svc.SearchRow]:
    rows = []
    for query, n in spec:
        rows += [svc.SearchRow(T0, query) for _ in range(n)]
    return rows


def _clicks(spec: list[tuple[str, int | None, int]]) -> list[svc.ClickRow]:
    rows = []
    for event, academy_id, n in spec:
        rows += [svc.ClickRow(T0, event, academy_id) for _ in range(n)]
    return rows


def test_build_report_counts_broad_buckets_only():
    searches = _searches(
        [
            (f"하남 미사 · 중2 · 수학 · {SECRET}", 12),
            ("하남 미사 · 고1 · 영어 · 내신 대비가 걱정", 8),
            ("미사 · 초3 · 피아노 · 취미로", 5),
        ]
    )
    clicks = _clicks([("phone", 1, 7), ("website", 1, 2), ("home_check_clicked", None, 1)])

    report = svc.build_report(searches, clicks, since=SINCE, until=UNTIL, now=T0)

    assert report.total_searches == 25
    assert report.total_clicks == 10
    assert report.dimensions["학년군"] == {"중등": 12, "고등": 8, "초등": 5}
    # 피아노는 4종 taxonomy 에서 "기타" 버킷 — 세부 이름은 리포트에 나오지 않는다.
    assert report.dimensions["과목"] == {"수학": 12, "영어": 8, "기타": 5}
    assert report.dimensions["지역"] == {"미사": 25}
    assert report.dimensions["커리큘럼"] == {"내신": 8, svc.UNSPECIFIED: 17}
    assert report.clicks_by_event == {"전화": 7, "웹사이트": 2, "기타(퇴역 이벤트)": 1}
    assert report.clicks_by_academy is None


def test_render_hides_small_cells_and_never_echoes_queries():
    searches = _searches(
        [(f"하남 미사 · 중2 · 수학 · {SECRET}", 18), ("하남 미사 · 고1 · 영어 · 내신", 3)]
    )
    clicks = _clicks([("phone", 1, 6), ("website", 1, 2)])
    report = svc.build_report(searches, clicks, since=SINCE, until=UNTIL, now=T0)

    text = svc.render_markdown(report)

    assert "| 수학 | 18 |" in text
    assert "| 영어 | <5 |" in text
    assert "| 고등 | <5 |" in text
    assert "| 전화 | 6 |" in text
    assert "| 웹사이트 | <5 |" in text
    assert "2026-08-19 ~ 2026-09-19" in text
    assert "검색 21건, 외부 행동 8건" in text
    # 원문·학교명·자녀 이름은 어디에도 없다.
    for leak in (SECRET, "김철수", "미사중학교", "취미로", "걱정"):
        assert leak not in text, leak
    # 학원별 표는 기본 꺼짐.
    assert "학원별 외부 행동" not in text


def test_insufficient_sample_refuses_to_report():
    searches = _searches([("하남 미사 · 중2 · 수학 · 고민", 19)])
    with pytest.raises(svc.InsufficientSample) as excinfo:
        svc.build_report(searches, [], since=SINCE, until=UNTIL, min_total=20)
    assert excinfo.value.total == 19
    assert excinfo.value.min_total == 20
    # 기준을 낮추면 만들어진다 — 기준이 실제로 작동하는지.
    svc.build_report(searches, [], since=SINCE, until=UNTIL, min_total=19)


def test_by_academy_lists_only_academies_at_or_above_min_cell():
    searches = _searches([("하남 미사 · 중2 · 수학 · 고민", 20)])
    clicks = _clicks([("phone", 1, 6), ("directions", 2, 2), ("detail", None, 3)])

    report = svc.build_report(
        searches, clicks, since=SINCE, until=UNTIL, by_academy=True, now=T0
    )
    # 2번 학원(2건)은 "<5" 로도 나오지 않는다 — 존재 자체를 목록에 올리지 않는다.
    assert report.clicks_by_academy == {1: 6}
    text = svc.render_markdown(report)
    assert "| 1 | 6 |" in text
    assert "| 2 |" not in text


def test_repository_lists_rows_inside_period_only(db_session):
    inside = T0.replace(tzinfo=None)
    before = (SINCE - timedelta(days=1)).replace(tzinfo=None)
    at_until = UNTIL.replace(tzinfo=None)
    db_session.add_all(
        [
            SearchHistory(query="안", created_at=inside),
            SearchHistory(query="전", created_at=before),
            SearchHistory(query="끝", created_at=at_until),
            ClickLog(event="phone", academy_id=None, created_at=inside),
            ClickLog(event="phone", academy_id=None, created_at=before),
        ]
    )
    db_session.commit()

    searches = engagement_repository.list_search_history(
        db_session, SINCE.replace(tzinfo=None), UNTIL.replace(tzinfo=None)
    )
    clicks = engagement_repository.list_click_logs(
        db_session, SINCE.replace(tzinfo=None), UNTIL.replace(tzinfo=None)
    )
    assert [row.query for row in searches] == ["안"]  # 끝 날짜는 미포함
    assert len(clicks) == 1


def test_cli_writes_markdown_and_refuses_small_samples(tmp_path, db_session, monkeypatch):
    from app.cli import demand_report

    db_session.add_all(
        [SearchHistory(query=f"하남 미사 · 중2 · 수학 · {SECRET}") for _ in range(21)]
    )
    db_session.add(ClickLog(event="phone", academy_id=None))
    db_session.commit()
    monkeypatch.setattr("app.db.session.SessionLocal", lambda: db_session)

    out = tmp_path / "demand.md"
    code = demand_report.main(
        ["--since", "2026-01-01", "--until", "2030-01-01", "--out", str(out)]
    )
    assert code == 0
    text = out.read_text(encoding="utf-8")
    assert text.startswith("# 비식별 집계 수요 리포트")
    assert "| 수학 | 21 |" in text
    assert SECRET not in text

    code = demand_report.main(
        ["--since", "2026-01-01", "--until", "2030-01-01", "--min-total", "22"]
    )
    assert code == 2


def test_demand_report_service_imports_no_orm():
    """집계는 값 객체만 받는다 — 세션·ORM 이 들어오면 원문이 새기 쉬워진다."""
    tree = ast.parse(Path(svc.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module]
        else:
            continue
        for name in names:
            assert not name.startswith("sqlalchemy"), name
            assert not name.startswith("app.models"), name
            assert not name.startswith("app.db"), name
