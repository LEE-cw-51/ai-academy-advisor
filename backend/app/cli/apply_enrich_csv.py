"""enrich-proposals CSV를 정본 JSON에 반영한다.

사용:
    cd backend
    uv run python -m app.cli.apply_enrich_csv ../data/raw/naver/enrich-proposals.csv --dry-run
    uv run python -m app.cli.apply_enrich_csv ../data/raw/naver/enrich-proposals.csv --apply
"""

from __future__ import annotations

import argparse
import sys
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

    report = apply_enrich_csv(
        args.csv,
        args.json_dir,
        confidence=args.confidence,
        dry_run=args.dry_run,
    )

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
