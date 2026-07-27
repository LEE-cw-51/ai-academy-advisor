"""리뷰 임베딩 백필 CLI.

사용:
    cd backend
    uv run python -m app.cli.ingest_review_embeddings [--batch-size 100] [--dry-run]

`embedding IS NULL`인 `Review` 행을 대상으로 embedding_provider/vector_store 설정에
따라 임베딩을 계산해 채운다. 대상 DB는 DATABASE_URL 환경변수(.env)를 따른다.
"""

import argparse

from app.services import review_embedding_service


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="embedding이 비어 있는 리뷰 행을 배치로 임베딩해 채운다."
    )
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="대상 건수만 출력하고 임베딩 호출/DB 변경은 하지 않는다",
    )
    args = parser.parse_args(argv)

    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        if args.dry_run:
            missing = review_embedding_service.count_missing_embeddings(db)
            print(f"dry-run: embedding 대상 {missing}건 (DB 변경 없음)")
            return 0

        report = review_embedding_service.backfill_missing_embeddings(
            db, batch_size=args.batch_size
        )
        print(f"완료: processed={report.processed}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
