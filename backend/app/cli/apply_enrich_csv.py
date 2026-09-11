"""enrich-proposals CSV를 정본 JSON에 반영한다.

사용:
    cd backend
    uv run python -m app.cli.apply_enrich_csv ../data/raw/naver/enrich-proposals.csv --dry-run
    uv run python -m app.cli.apply_enrich_csv ../data/raw/naver/enrich-proposals.csv --apply
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from app.services.academy_apply_service import apply_enrich_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="enrich-proposals CSV의 high 신뢰 제안을 정본 JSON null 필드에 반영한다."
    )
    parser.add_argument("csv", type=Path, help="enrich-proposals.csv 경로")
    parser.add_argument(
        "--json-dir",
        type=Path,
        default=Path("../data/academies"),
        help="정본 JSON 디렉터리 (기본: ../data/academies)",
    )
    parser.add_argument(
        "--confidence",
        default="high",
        help="반영할 confidence 값 (기본: high)",
    )
    parser.add_argument(
        "--today",
        type=date.fromisoformat,
        default=None,
        help="last_verified_at·source_note에 쓸 날짜 (예: 2026-09-11). "
        "subject_detail 백필 실행 때 오늘 날짜로 준다. 기본: 2026-09-01 유지",
    )
    parser.add_argument(
        "--note",
        default=None,
        help="source_note 문구 재정의 (기본: A3 category 과목·URL 반영 문구)",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="변경 미리보기만 (JSON 미수정)",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="JSON 파일에 반영",
    )
    args = parser.parse_args(argv)

    kwargs: dict = {"confidence": args.confidence, "dry_run": args.dry_run}
    if args.today is not None:
        kwargs["verified_at"] = args.today
        kwargs["source_note"] = args.note or (
            f"네이버 지역검색 category 기반 subject_detail 반영, {args.today.isoformat()}"
        )
    elif args.note is not None:
        kwargs["source_note"] = args.note
    report = apply_enrich_csv(args.csv, args.json_dir, **kwargs)

    for result in report.results:
        if result.action == "applied":
            changes = ", ".join(result.changes)
            prefix = "WOULD APPLY" if args.dry_run else "APPLIED"
            print(f"{prefix}\t{result.file_name}\t{changes}")
        elif result.action == "skipped":
            print(f"SKIP\t{result.file_name}\t{result.detail}", file=sys.stderr)
        else:
            print(f"ERROR\t{result.file_name}\t{result.detail}", file=sys.stderr)

    mode_label = "dry-run" if args.dry_run else "apply"
    print(
        f"{mode_label}: applied={report.applied} skipped={report.skipped} "
        f"errors={report.errors}"
    )
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
