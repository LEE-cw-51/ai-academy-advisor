"""비식별 집계 수요 리포트를 markdown 으로 낸다 (Phase 5c 2개월차 원장 리포트 시안 재료).

사용:
    cd backend
    # DATABASE_URL = Supabase session pooler 5432 (transaction 6543 금지). 읽기만 한다.
    uv run python -m app.cli.demand_report --since 2026-08-19 --out ../tmp_audit_out/demand-2026-09.md
    uv run python -m app.cli.demand_report --min-cell 5 --min-total 20 --by-academy

원문 질의는 출력하지 않는다. 검색 표본이 --min-total 미만이면 리포트를 만들지 않고 exit 2.
출력 파일은 커밋하지 않는다 (tmp_audit_out/ 은 gitignored). 규칙은
docs/data-strategy.md "사업 검증용 집계 원칙" 참고.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

from app.services import demand_report_service as svc


def _parse_day(value: str) -> datetime:
    return datetime.combine(date.fromisoformat(value), time.min, tzinfo=timezone.utc)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="search_history·click_logs 를 비식별 버킷으로만 집계한 markdown 리포트."
    )
    parser.add_argument(
        "--since", type=_parse_day, default=None, help="시작일 YYYY-MM-DD (기본: 30일 전)"
    )
    parser.add_argument(
        "--until",
        type=_parse_day,
        default=None,
        help="끝일 YYYY-MM-DD, 미포함 (기본: 내일 0시 UTC)",
    )
    parser.add_argument(
        "--min-cell",
        type=int,
        default=svc.DEFAULT_MIN_CELL,
        help=f"이 건수 미만인 셀은 가린다 (기본 {svc.DEFAULT_MIN_CELL})",
    )
    parser.add_argument(
        "--min-total",
        type=int,
        default=svc.DEFAULT_MIN_TOTAL,
        help=f"검색 표본이 이보다 적으면 리포트를 만들지 않는다 (기본 {svc.DEFAULT_MIN_TOTAL})",
    )
    parser.add_argument(
        "--by-academy",
        action="store_true",
        help="min-cell 이상인 학원의 행동 수를 id 로 낸다 (기본 끔 — 학원별 소표본 보류)",
    )
    parser.add_argument(
        "--out", type=Path, default=None, help="markdown 출력 경로 (기본 stdout)"
    )
    args = parser.parse_args(argv)

    now = datetime.now(timezone.utc)
    until = args.until or datetime.combine(
        now.date() + timedelta(days=1), time.min, tzinfo=timezone.utc
    )
    since = args.since or until - timedelta(days=30)
    if since >= until:
        parser.error("--since 는 --until 보다 앞이어야 합니다")

    from app.db.session import SessionLocal
    from app.repositories import engagement_repository

    db = SessionLocal()
    try:
        searches = [
            svc.SearchRow(row.created_at, row.query)
            for row in engagement_repository.list_search_history(db, since, until)
        ]
        clicks = [
            svc.ClickRow(row.created_at, row.event, row.academy_id)
            for row in engagement_repository.list_click_logs(db, since, until)
        ]
    finally:
        db.close()

    try:
        report = svc.build_report(
            searches,
            clicks,
            since=since,
            until=until,
            min_cell=args.min_cell,
            min_total=args.min_total,
            by_academy=args.by_academy,
            now=now,
        )
    except svc.InsufficientSample as exc:
        print(f"{exc} — 리포트를 만들지 않습니다.", file=sys.stderr)
        return 2

    text = svc.render_markdown(report)
    if args.out is None:
        sys.stdout.write(text)
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(
            f"완료: {args.out} (검색 {report.total_searches}건, "
            f"외부 행동 {report.total_clicks}건)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
