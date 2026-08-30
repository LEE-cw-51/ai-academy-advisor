"""검색으로 학원 subjects·URL 제안을 CSV로 뽑는다. JSON 정본은 쓰지 않는다.

사용:
    cd backend
    uv run python -m app.cli.enrich_academy_from_search ../data/academies --dry-run --limit 8
    uv run python -m app.cli.enrich_academy_from_search ../data/academies --from-raw ../data/raw/naver
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from app.core.config import get_settings
from app.providers.naver_local import NaverLocalSearch
from app.providers.naver_review import NaverReviewSource
from app.services import academy_enrich_service

_CSV_FIELDS = (
    "name",
    "address",
    "proposed_subjects",
    "website_url",
    "blog_url",
    "confidence",
    "evidence",
    "source_note",
)

_DEFAULT_RAW = Path("../data/raw/naver")
_DEFAULT_CSV = Path("../data/raw/naver/enrich-proposals.csv")


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(_CSV_FIELDS), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="NAVER API HUB 지역·블로그 검색으로 과목·URL 제안을 CSV로 만든다. JSON은 수정하지 않는다."
    )
    parser.add_argument("directory", type=Path, help="정본 JSON 디렉터리 (예: ../data/academies)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="API는 호출하되 data/raw 원본 파일은 쓰지 않는다. JSON은 어떤 플래그에서도 쓰지 않는다.",
    )
    parser.add_argument("--limit", type=int, default=None, help="처리할 학원 수 상한")
    parser.add_argument(
        "--output",
        type=Path,
        default=_DEFAULT_CSV,
        help=f"CSV 경로 (기본: {_DEFAULT_CSV}, gitignored data/raw/)",
    )
    parser.add_argument("--raw-dir", type=Path, default=_DEFAULT_RAW)
    parser.add_argument(
        "--from-raw",
        type=Path,
        default=None,
        help="예약. 이번 범위에서는 미지원 — 검색 --dry-run만 사용한다.",
    )
    args = parser.parse_args(argv)

    if args.from_raw is not None:
        print(
            "ERROR: --from-raw 재처리는 다음 배치에서 연결한다. 이번 범위는 --dry-run 검색이다.",
            file=sys.stderr,
        )
        return 1

    settings = get_settings()
    if not settings.naver_client_id or not settings.naver_client_secret:
        print("ERROR: NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 이 필요합니다.", file=sys.stderr)
        return 1

    records = academy_enrich_service.load_academy_records(args.directory)
    if args.limit is not None:
        records = records[: args.limit]

    local = NaverLocalSearch(
        settings.naver_client_id,
        settings.naver_client_secret,
        settings.naver_base_url,
    )
    blogs = NaverReviewSource(
        settings.naver_client_id,
        settings.naver_client_secret,
        settings.naver_base_url,
        endpoints=("blog",),
    )

    rows: list[dict[str, str]] = []
    for path, academy in records:
        proposal = academy_enrich_service.enrich_one(path, academy, local, blogs)
        rows.append(proposal.as_csv_row())
        print(
            f"{proposal.confidence}\t{academy.name}\t"
            f"subjects={proposal.proposed_subjects or '-'}"
        )

    _write_csv(args.output, rows)
    print(f"CSV {len(rows)}행 → {args.output}")
    print("JSON 정본은 수정하지 않았습니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
