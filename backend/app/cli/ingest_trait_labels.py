"""리뷰 → academy_trait_labels 배치 CLI.

사용:
    cd backend
    # DATABASE_URL = Supabase session pooler 5432
    uv run python -m app.cli.ingest_trait_labels [--dry-run] [--limit N] [--academy-id ID]

idempotent: (academy_id, label, source_url) 가 있으면 건너뛴다.
기본 status=candidate. academies.curriculum_* 는 쓰지 않는다.
"""

from __future__ import annotations

import argparse
import json

from app.services import trait_label_ingest_service


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="리뷰 스니펫에서 닫힌 특징 라벨을 추출해 academy_trait_labels에 적재한다."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="집계만 하고 DB에 쓰지 않는다",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="스캔할 리뷰 행 상한",
    )
    parser.add_argument(
        "--academy-id",
        type=int,
        default=None,
        help="특정 학원만",
    )
    args = parser.parse_args(argv)

    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        report = trait_label_ingest_service.ingest_trait_labels_from_reviews(
            db,
            academy_id=args.academy_id,
            limit=args.limit,
            dry_run=args.dry_run,
        )
        payload = {
            "dry_run": args.dry_run,
            "reviews_scanned": report.reviews_scanned,
            "inserted": report.inserted,
            "skipped_duplicate": report.skipped_duplicate,
            "skipped_no_match": report.skipped_no_match,
            "by_label": report.by_label,
            "academies_touched_count": len(report.academies_touched),
            "academies_touched": sorted(report.academies_touched),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        print(report.summary_line())
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
