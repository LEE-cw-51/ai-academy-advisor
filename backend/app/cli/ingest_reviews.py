"""네이버 검색 API 리뷰 수집 CLI.

사용:
    cd backend
    uv run python -m app.cli.ingest_reviews [--dry-run] [--limit N]
    uv run python -m app.cli.ingest_reviews --from-raw ../data/raw/naver

REVIEW_SOURCE 환경변수로 소스를 고른다 (stub/naver). 대상 DB는 DATABASE_URL(.env)을 따른다.

플래그 조합별 부작용:

    (없음)                  API 호출 O · data/raw 기록 O · DB 기록 O
    --dry-run               API 호출 O · data/raw 기록 X · DB 기록 X
    --from-raw DIR          API 호출 X · data/raw 기록 X · DB 기록 O
    --from-raw + --dry-run  전부 X (무료 오프라인 미리보기)

`--dry-run`은 **부작용 전무**가 계약이다(파일 포함). 원본 캐시는 정상 실행으로 만들고,
같은 응답을 다시 처리할 땐 `--from-raw`로 쿼터를 쓰지 않는다.

쿼터: 학원당 1질의 × 2엔드포인트 × 411건 = 822회로, 무료 25,000회/일의 3.3%다.
동시 실행하지 않는다 — 봇 트래픽 패턴을 만들지 않기 위한 의도적 순차 실행이다.
"""

import argparse
import sys
from pathlib import Path

from app.services import review_ingest_service

_DEFAULT_RAW_DIR = Path("../data/raw/naver")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="공개 게시물 검색 결과를 학원별 리뷰 스니펫으로 수집해 DB에 적재한다."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="집계만 하고 DB·원본 파일을 모두 건드리지 않는다",
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="처리할 학원 수 상한 (예: 5로 먼저 시험)"
    )
    parser.add_argument(
        "--display",
        type=int,
        default=None,
        help="엔드포인트당 받아올 건수 (기본: NAVER_DISPLAY 설정값)",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=_DEFAULT_RAW_DIR,
        help=f"원본 응답 저장 위치 (기본: {_DEFAULT_RAW_DIR}, gitignored)",
    )
    parser.add_argument(
        "--from-raw",
        type=Path,
        default=None,
        help="소스를 호출하지 않고 이 디렉터리의 저장된 응답만 재처리한다",
    )
    args = parser.parse_args(argv)

    # app.db.session 임포트는 DATABASE_URL로 엔진을 만드는 부작용이 있다. 이 CLI는
    # dry-run 에서도 학원 목록과 중복 판정에 DB가 필요하므로 여기서 임포트한다
    # (모듈 최상단으로 올리지 말 것 — import 만으로 DB 접속이 생긴다).
    from app.core.config import get_settings
    from app.db.session import SessionLocal
    from app.providers.factory import get_review_source

    settings = get_settings()
    display = args.display if args.display is not None else settings.naver_display

    from_raw = None
    if args.from_raw is not None:
        from_raw = review_ingest_service.load_raw(args.from_raw)
        if not from_raw:
            print(f"ERROR: 저장된 응답이 없습니다: {args.from_raw}", file=sys.stderr)
            return 1
        print(f"--from-raw: {len(from_raw)}개 학원의 저장된 응답을 재처리한다 (API 호출 없음)")

    db = SessionLocal()
    try:
        report = review_ingest_service.ingest_reviews(
            db,
            source=None if from_raw is not None else get_review_source(),
            limit=args.limit,
            display=display,
            dry_run=args.dry_run,
            raw_dir=None if from_raw is not None else args.raw_dir,
            from_raw=from_raw,
        )
    finally:
        db.close()

    prefix = "dry-run: " if args.dry_run else ""
    print(
        f"{prefix}완료: queried={report.queried} fetched={report.fetched} "
        f"inserted={report.inserted} duplicate={report.skipped_duplicate} "
        f"unmatched={report.skipped_unmatched} failed={report.failed}"
    )

    # 커버리지를 즉시 보이게 한다 — 회원 전용 카페 글은 색인되지 않아 0건 학원이
    # 많이 나오는 게 정상이고, 그 사실을 RAG 결과가 빈약해진 뒤에 알면 늦다.
    histogram = report.coverage_histogram()
    print("커버리지: " + " / ".join(f"{k} {v}개 학원" for k, v in histogram.items()))

    if args.dry_run:
        print("dry-run 모드: DB·원본 파일 변경 없음")
    elif report.inserted:
        print("다음 단계: uv run python -m app.cli.ingest_review_embeddings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
