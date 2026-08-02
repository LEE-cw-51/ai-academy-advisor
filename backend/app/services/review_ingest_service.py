"""리뷰 수집 서비스 (`ReviewSource` → `reviews` 테이블).

RAG 파이프라인에서 유일하게 비어 있던 구간이다. 임베딩·벡터검색·근거조립은 이미
연결돼 있었지만 `reviews`에 행을 넣는 경로가 없었다.

수집은 실시간 폴링이 아니라 오프라인 배치다 (docs/decision-log.md 2026-07-31).
원본 응답은 gitignored `data/raw/`에만 남기고 git 정본에는 절대 커밋하지 않는다.

임베딩은 여기서 계산하지 않는다 — 수집(이 서비스)과 임베딩
(`review_embedding_service`)을 분리해, 임베딩 provider를 바꿔도 재수집이 필요 없게 한다.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.academy import Academy
from app.models.review import Review
from app.providers.base import ReviewItem, ReviewSource

_RAW_ENCODING = "utf-8"


@dataclass
class IngestReport:
    queried: int = 0  # 소스에 질의한 학원 수
    fetched: int = 0  # 소스가 돌려준 항목 수
    inserted: int = 0
    skipped_duplicate: int = 0  # 이미 같은 (academy_id, url) 이 있음
    skipped_unmatched: int = 0  # 학원명이 본문에 없어 귀속 실패
    failed: int = 0  # 소스 호출 자체가 실패한 학원 수
    per_academy: dict[int, int] = field(default_factory=dict)

    def coverage_histogram(self) -> dict[str, int]:
        """학원별 수집 건수 분포. 커버리지를 실행 직후에 보이게 하는 용도다.

        지역 맘카페는 대부분 회원 전용이라 `cafearticle`에 색인되지 않는다 — 0건인
        학원이 많이 나오는 게 정상이며, 그 사실을 RAG 결과가 빈약해진 뒤가 아니라
        수집 직후에 알아야 한다.
        """
        buckets = {"0건": 0, "1-4건": 0, "5건+": 0}
        for count in self.per_academy.values():
            if count == 0:
                buckets["0건"] += 1
            elif count < 5:
                buckets["1-4건"] += 1
            else:
                buckets["5건+"] += 1
        return buckets


def build_query(academy: Academy) -> str:
    """학원명 단독으로 질의한다.

    지역 토큰(`"미사 가온수학"`)을 붙이는 안은 기각했다 — 네이버는 그걸 본문에 AND로
    걸어서, "미사"를 명시하지 않은 정상 후기가 전부 탈락해 재현율이 무너진다.
    정밀도는 `matches_academy` 사후필터로 확보하며 API 호출을 추가로 쓰지 않는다.
    """
    return academy.name


def matches_academy(item: ReviewItem, academy: Academy) -> bool:
    """항목이 이 학원의 글이 맞는지 검사한다.

    네이버 키워드 검색은 OR성이라 "가온수학" 질의에 같은 동네 다른 학원 글이 섞여 온다.
    **잘못 귀속된 리뷰는 없는 것보다 훨씬 나쁘다** — `evidence_by_academy` →
    `_build_reason`을 타고 사용자에게 보이는 "근거 리뷰"로 둔갑하기 때문이다.
    그래서 학원명이 제목이나 본문에 실제로 등장할 때만 통과시킨다.
    """
    name = academy.name.strip()
    if not name:
        return False
    haystack = f"{item.title} {item.content}"
    return name in haystack


def _existing_urls(db: Session, academy_id: int) -> set[str]:
    rows = db.scalars(
        select(Review.source_url).where(
            Review.academy_id == academy_id, Review.source_url.is_not(None)
        )
    ).all()
    return {row for row in rows if row}


def _write_raw(raw_dir: Path, academy_id: int, items: list[ReviewItem], today: date) -> None:
    """소스 응답을 gitignored `data/raw/`에 남긴다 (`--from-raw` 재처리용)."""
    target_dir = raw_dir / today.isoformat()
    target_dir.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "title": item.title,
            "content": item.content,
            "url": item.url,
            "source": item.source,
            "published_at": item.published_at.isoformat() if item.published_at else None,
        }
        for item in items
    ]
    (target_dir / f"{academy_id}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding=_RAW_ENCODING
    )


def load_raw(raw_dir: Path) -> dict[int, list[ReviewItem]]:
    """`data/raw/` 아래 모든 날짜 디렉터리에서 학원별 항목을 읽는다.

    같은 학원이 여러 날짜에 있으면 전부 합친다 — 중복은 dedup 이 걸러낸다.
    """
    by_academy: dict[int, list[ReviewItem]] = {}
    if not raw_dir.is_dir():
        return by_academy
    for path in sorted(raw_dir.rglob("*.json")):
        try:
            academy_id = int(path.stem)
        except ValueError:
            continue
        rows = json.loads(path.read_text(encoding=_RAW_ENCODING))
        published = by_academy.setdefault(academy_id, [])
        for row in rows:
            raw_date = row.get("published_at")
            published.append(
                ReviewItem(
                    title=row.get("title") or "",
                    content=row.get("content") or "",
                    url=row.get("url") or "",
                    source=row.get("source") or "",
                    published_at=date.fromisoformat(raw_date) if raw_date else None,
                )
            )
    return by_academy


def ingest_reviews(
    db: Session,
    source: ReviewSource | None = None,
    *,
    limit: int | None = None,
    display: int = 10,
    dry_run: bool = False,
    raw_dir: Path | None = None,
    from_raw: dict[int, list[ReviewItem]] | None = None,
    today: date | None = None,
) -> IngestReport:
    """학원별로 리뷰를 수집해 `reviews`에 적재한다.

    `from_raw`가 주어지면 소스를 호출하지 않고 그 캐시만 처리한다 (`--from-raw`).
    `dry_run`이면 DB도 `data/raw/`도 건드리지 않는다 — 부작용 전무가 계약이다.

    **학원 단위로 커밋한다.** 411건 중간에 429나 네트워크 오류가 나도 앞선 학원의
    수집분은 보존되고, 재실행하면 dedup 이 이미 넣은 건을 건너뛴다. 재개 가능성을
    별도 체크포인트 없이 얻는 방법이다.
    """
    report = IngestReport()
    ref_date = today or date.today()

    stmt = select(Academy).order_by(Academy.id)
    if limit is not None:
        stmt = stmt.limit(limit)
    academies = list(db.scalars(stmt))

    for academy in academies:
        if from_raw is not None:
            items = from_raw.get(academy.id, [])
        else:
            if source is None:
                raise ValueError("source 또는 from_raw 중 하나는 있어야 합니다")
            try:
                items = source.search(build_query(academy), limit=display)
            except Exception as exc:  # noqa: BLE001 — 한 학원 실패가 배치를 죽이지 않는다
                report.failed += 1
                report.per_academy[academy.id] = 0
                print(f"WARNING: id={academy.id} {academy.name} 수집 실패 — {exc}")
                continue
            report.queried += 1
            if raw_dir is not None and not dry_run and items:
                _write_raw(raw_dir, academy.id, items, ref_date)

        report.fetched += len(items)
        inserted_here = _ingest_one(db, academy, items, report, dry_run=dry_run)
        report.per_academy[academy.id] = inserted_here

    return report


def _ingest_one(
    db: Session,
    academy: Academy,
    items: list[ReviewItem],
    report: IngestReport,
    *,
    dry_run: bool,
) -> int:
    # 중복 판정은 사전 조회로 한다. IntegrityError 를 잡는 방식은 Postgres 에서
    # 트랜잭션 전체를 abort 시켜 그 학원의 나머지 수집분까지 잃는다.
    seen = _existing_urls(db, academy.id)
    inserted = 0

    for item in items:
        if not matches_academy(item, academy):
            report.skipped_unmatched += 1
            continue
        if item.url and item.url in seen:
            report.skipped_duplicate += 1
            continue
        seen.add(item.url)
        inserted += 1
        report.inserted += 1
        if dry_run:
            continue
        db.add(
            Review(
                academy_id=academy.id,
                content=_content_for(item),
                source=item.source,
                source_url=item.url or None,
                published_at=item.published_at,
            )
        )

    if not dry_run and inserted:
        db.commit()
    return inserted


def _content_for(item: ReviewItem) -> str:
    """임베딩 입력 문자열. 제목은 정보 밀도가 높아 본문 앞에 붙인다."""
    return f"{item.title} {item.content}".strip()
