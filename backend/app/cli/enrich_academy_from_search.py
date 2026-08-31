"""검색으로 학원 subjects·URL 제안을 CSV로 뽑는다. JSON 정본은 쓰지 않는다.

사용:
    cd backend
    uv run python -m app.cli.enrich_academy_from_search ../data/academies --dry-run --limit 8
    uv run python -m app.cli.enrich_academy_from_search ../data/academies
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import httpx

from app.core.config import get_settings
from app.providers.base import LocalSearchProvider, ReviewSource
from app.providers.naver_local import NaverLocalSearch
from app.providers.naver_review import NaverReviewSource
from app.providers.stub import StubLocalSearchProvider, StubReviewSource
from app.schemas.academy import AcademyRecord
from app.services import academy_enrich_service
from app.services.academy_enrich_service import EnrichReport

_CSV_FIELDS = (
    "name",
    "address",
    "proposed_subjects",
    "website_url",
    "blog_url",
    "proposed_phone",
    "confidence",
    "evidence",
    "source_note",
    "file_name",
    "matched_local_title",
)

_DEFAULT_CSV = Path("../data/raw/naver/enrich-proposals.csv")


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(_CSV_FIELDS), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _run(
    records: list[tuple[Path, AcademyRecord]],
    local: LocalSearchProvider,
    blogs: ReviewSource,
    report: EnrichReport,
) -> None:
    for path, academy in records:
        try:
            proposal = academy_enrich_service.enrich_one(path, academy, local, blogs)
        except Exception as exc:  # noqa: BLE001 - 한 건 실패로 전체 배치를 잃지 않는다
            report.errors.append(f"{academy.name} ({path.name}): {exc}")
            print(f"ERROR\t{academy.name}\t{exc}", file=sys.stderr)
            continue
        report.proposals.append(proposal)
        print(
            f"{proposal.confidence}\t{academy.name}\t"
            f"subjects={proposal.proposed_subjects or '-'}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="NAVER API HUB 지역·블로그 검색으로 과목·URL 제안을 CSV로 만든다. JSON은 수정하지 않는다."
    )
    parser.add_argument("directory", type=Path, help="정본 JSON 디렉터리 (예: ../data/academies)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="라이브 NAVER API를 호출하지 않고 stub 제공자로 전체 파이프라인을 돌린다 "
        "(자격증명 불필요, 항상 같은 결정적 가짜 결과). JSON은 어떤 플래그에서도 쓰지 않는다.",
    )
    parser.add_argument("--limit", type=int, default=None, help="처리할 학원 수 상한")
    parser.add_argument(
        "--output",
        type=Path,
        default=_DEFAULT_CSV,
        help=f"CSV 경로 (기본: {_DEFAULT_CSV}, gitignored data/raw/)",
    )
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

    records = academy_enrich_service.load_academy_records(args.directory)
    if args.limit is not None:
        records = records[: args.limit]

    report = EnrichReport()

    if args.dry_run:
        _run(records, StubLocalSearchProvider(), StubReviewSource(), report)
    else:
        settings = get_settings()
        if not settings.naver_client_id or not settings.naver_client_secret:
            print(
                "ERROR: NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 이 필요합니다 "
                "(자격증명 없이 시험해 보려면 --dry-run).",
                file=sys.stderr,
            )
            return 1
        with httpx.Client() as client:
            local = NaverLocalSearch(
                settings.naver_client_id,
                settings.naver_client_secret,
                settings.naver_base_url,
                client=client,
            )
            blogs = NaverReviewSource(
                settings.naver_client_id,
                settings.naver_client_secret,
                settings.naver_base_url,
                endpoints=("blog",),
                client=client,
            )
            _run(records, local, blogs, report)

    rows = [proposal.as_csv_row() for proposal in report.proposals]
    _write_csv(args.output, rows)
    print(f"CSV {len(rows)}행 → {args.output}")
    if report.errors:
        print(f"실패 {len(report.errors)}건 (CSV에는 성공한 행만 담김):", file=sys.stderr)
        for line in report.errors:
            print(f"  - {line}", file=sys.stderr)
    print("JSON 정본은 수정하지 않았습니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
