"""운영 DB의 academies 행을 JSON으로 덤프한다 (백업·재해복구용, git 정본 아님).

사용:
    cd backend
    uv run python -m app.cli.export_academies ../data/backups/2026-09-01
    uv run python -m app.cli.export_academies ../data/backups/2026-09-01 --prune
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.services import academy_export_service


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="DB academies 테이블을 JSON 파일로 덤프한다 (백업용)."
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="출력 디렉터리 (예: ../data/backups/2026-09-01)",
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        help="이번 덤프에 없는 orphan *.json을 삭제한다 (기본은 덮어쓰기만)",
    )
    args = parser.parse_args(argv)

    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        report = academy_export_service.export_records(
            db, args.directory, prune=args.prune
        )
    finally:
        db.close()

    print(
        f"완료: written={report.written} skipped={report.skipped} "
        f"pruned={report.pruned}"
    )
    for error in report.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
