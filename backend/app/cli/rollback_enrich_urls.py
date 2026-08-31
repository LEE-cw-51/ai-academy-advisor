"""A3로 잘못 반영된 URL·이름 불일치 subjects를 정본 JSON에서 되돌린다.

사용:
    cd backend
    uv run python -m app.cli.rollback_enrich_urls ../data/raw/naver/enrich-proposals.csv --dry-run
    uv run python -m app.cli.rollback_enrich_urls ../data/raw/naver/enrich-proposals.csv --apply
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.services.academy_apply_service import rollback_enrich_urls


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="A3 enrich URL 롤백 — 비홈페이지·이름 불일치·약한 블로그"
    )
    parser.add_argument("csv", type=Path, help="enrich-proposals.csv 경로")
    parser.add_argument(
        "--json-dir",
        type=Path,
        default=Path("../data/academies"),
        help="정본 JSON 디렉터리 (기본: ../data/academies)",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="변경 미리보기만")
    mode.add_argument("--apply", action="store_true", help="JSON 파일에 반영")
    args = parser.parse_args(argv)

    report = rollback_enrich_urls(
        args.csv,
        args.json_dir,
        dry_run=args.dry_run,
    )

    for result in report.results:
        if result.action == "rolled_back":
            changes = ", ".join(result.changes)
            prefix = "WOULD ROLLBACK" if args.dry_run else "ROLLED BACK"
            print(f"{prefix}\t{result.file_name}\t{changes}")
        elif result.action == "skipped":
            pass
        else:
            print(f"ERROR\t{result.file_name}\t{result.detail}", file=sys.stderr)

    mode_label = "dry-run" if args.dry_run else "apply"
    print(
        f"{mode_label}: rolled_back={report.rolled_back} skipped={report.skipped} "
        f"errors={report.errors}"
    )
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
