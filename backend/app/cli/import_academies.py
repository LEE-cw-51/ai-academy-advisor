"""JSON 시드(data/academies/*.json)를 DB로 임포트하는 CLI.

운영 DB(Supabase)는 Studio가 정본이므로 기본적으로 거부한다.
컷오버·재해복구 시에만 --force 또는 ALLOW_ACADEMY_IMPORT=1.

사용:
    cd backend
    uv run python -m app.cli.import_academies ../data/academies [--dry-run] [--force]

대상 DB는 DATABASE_URL 환경변수(.env)를 따른다.
"""

import argparse
import sys
from pathlib import Path

from app.core.config import get_settings
from app.core.import_guard import academy_import_allowed
from app.services import academy_import_service


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="시드 JSON을 검증하고 DB로 업서트한다 (운영 URL은 --force 필요)."
    )
    parser.add_argument(
        "directory", type=Path, help="정본 JSON 디렉터리 (예: ../data/academies)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="검증만 수행하고 DB는 변경하지 않는다 (DB 접속 불필요)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="운영 DB에도 JSON을 덮어쓴다 (Studio 수정 소실 위험 — 컷오버·복구만)",
    )
    args = parser.parse_args(argv)

    load = academy_import_service.load_records(args.directory)
    if load.errors:
        for error in load.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"검증 실패: 오류 {len(load.errors)}건", file=sys.stderr)
        return 1

    print(f"{len(load.records)}개 파일 검증 통과")
    if args.dry_run:
        print("dry-run 모드: DB 변경 없음")
        return 0

    database_url = get_settings().database_url
    allowed, reason = academy_import_allowed(database_url, force=args.force)
    if not allowed:
        print(f"ERROR: {reason}", file=sys.stderr)
        return 1

    # DB 연결은 dry-run이 아닐 때만 만든다.
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        report = academy_import_service.import_records(
            db, [record for _, record in load.records], force=args.force
        )
    finally:
        db.close()

    print(
        f"완료: created={report.created} updated={report.updated} "
        f"unchanged={report.unchanged}"
    )
    for warning in report.warnings:
        print(f"WARNING: {warning}")
    if report.orphans:
        print("파일에 없는 DB 행 (필요 시 수동 삭제):")
        for orphan in report.orphans:
            print(f"  - {orphan}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
