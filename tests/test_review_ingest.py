"""리뷰 수집 서비스 테스트 (stub 소스 + in-memory DB, 네트워크 없음)."""

from datetime import date
from pathlib import Path

import pytest

from app.models.academy import Academy
from app.models.review import Review
from app.providers.base import ReviewItem
from app.providers.stub import StubReviewSource
from app.services import review_ingest_service


class FakeSource:
    """호출 횟수를 세고 정해진 항목만 돌려주는 소스."""

    def __init__(self, items_by_query: dict[str, list[ReviewItem]] | None = None):
        self.items_by_query = items_by_query or {}
        self.calls: list[str] = []

    def search(self, query: str, limit: int = 10) -> list[ReviewItem]:
        self.calls.append(query)
        return self.items_by_query.get(query, [])


class ExplodingSource:
    def search(self, query: str, limit: int = 10) -> list[ReviewItem]:
        raise RuntimeError("429 Too Many Requests")


def _item(url: str, *, title="가온수학 후기", content="가온수학 좋아요", published=None):
    return ReviewItem(
        title=title,
        content=content,
        url=url,
        source="naver_blog",
        published_at=published,
    )


@pytest.fixture()
def academy(db_session):
    row = Academy(name="가온수학", address="경기도 하남시 미사강변대로 84")
    db_session.add(row)
    db_session.commit()
    return row


def _reviews(db_session):
    return db_session.query(Review).order_by(Review.id).all()


def test_inserts_matching_items(db_session, academy):
    source = FakeSource({"가온수학": [_item("https://blog.example/1", published=date(2026, 7, 31))]})

    report = review_ingest_service.ingest_reviews(db_session, source)

    assert report.inserted == 1
    rows = _reviews(db_session)
    assert rows[0].source_url == "https://blog.example/1"
    assert rows[0].published_at == date(2026, 7, 31)
    assert rows[0].source == "naver_blog"
    # 제목 + 본문이 임베딩 입력으로 합쳐진다.
    assert rows[0].content == "가온수학 후기 가온수학 좋아요"


def test_query_is_name_only(db_session, academy):
    source = FakeSource()

    review_ingest_service.ingest_reviews(db_session, source)

    # 지역 토큰을 붙이면 네이버가 본문에 AND로 걸어 재현율이 무너진다.
    assert source.calls == ["가온수학"]


def test_second_run_is_deduplicated(db_session, academy):
    source = FakeSource({"가온수학": [_item("https://blog.example/1")]})

    first = review_ingest_service.ingest_reviews(db_session, source)
    second = review_ingest_service.ingest_reviews(db_session, source)

    assert first.inserted == 1
    assert second.inserted == 0
    assert second.skipped_duplicate == 1
    assert len(_reviews(db_session)) == 1


def test_duplicate_url_within_one_batch_inserted_once(db_session, academy):
    source = FakeSource(
        {"가온수학": [_item("https://blog.example/1"), _item("https://blog.example/1")]}
    )

    report = review_ingest_service.ingest_reviews(db_session, source)

    assert report.inserted == 1
    assert report.skipped_duplicate == 1


def test_item_without_academy_name_is_rejected(db_session, academy):
    """잘못 귀속된 리뷰는 없는 것보다 나쁘다 — 사용자에게 '근거 리뷰'로 보이기 때문."""
    source = FakeSource(
        {
            "가온수학": [
                _item("https://blog.example/2", title="옆집 영어학원 후기", content="영어 잘 가르쳐요")
            ]
        }
    )

    report = review_ingest_service.ingest_reviews(db_session, source)

    assert report.inserted == 0
    assert report.skipped_unmatched == 1
    assert _reviews(db_session) == []


def test_name_match_in_title_alone_is_enough(db_session, academy):
    source = FakeSource(
        {"가온수학": [_item("https://blog.example/3", title="가온수학 다녀왔어요", content="괜찮네요")]}
    )

    assert review_ingest_service.ingest_reviews(db_session, source).inserted == 1


def test_dry_run_writes_neither_db_nor_raw(db_session, academy, tmp_path):
    source = FakeSource({"가온수학": [_item("https://blog.example/1")]})

    report = review_ingest_service.ingest_reviews(
        db_session, source, dry_run=True, raw_dir=tmp_path
    )

    assert report.inserted == 1  # 집계는 된다
    assert _reviews(db_session) == []
    assert list(tmp_path.rglob("*.json")) == []


def test_normal_run_writes_raw_payload(db_session, academy, tmp_path):
    source = FakeSource({"가온수학": [_item("https://blog.example/1")]})

    review_ingest_service.ingest_reviews(
        db_session, source, raw_dir=tmp_path, today=date(2026, 8, 2)
    )

    written = list(tmp_path.rglob("*.json"))
    assert len(written) == 1
    assert written[0].parent.name == "2026-08-02"
    assert written[0].stem == str(academy.id)


def test_from_raw_roundtrip_makes_no_source_calls(db_session, academy, tmp_path):
    source = FakeSource({"가온수학": [_item("https://blog.example/1", published=date(2026, 7, 31))]})
    review_ingest_service.ingest_reviews(
        db_session, source, dry_run=False, raw_dir=tmp_path, today=date(2026, 8, 2)
    )
    db_session.query(Review).delete()
    db_session.commit()

    cached = review_ingest_service.load_raw(tmp_path)
    report = review_ingest_service.ingest_reviews(db_session, source=None, from_raw=cached)

    assert report.inserted == 1
    assert _reviews(db_session)[0].published_at == date(2026, 7, 31)
    assert source.calls == ["가온수학"]  # 최초 1회뿐, 재처리는 호출 없음


def test_load_raw_on_missing_dir_returns_empty(tmp_path):
    assert review_ingest_service.load_raw(tmp_path / "nope") == {}


def test_source_failure_is_isolated_per_academy(db_session, academy):
    report = review_ingest_service.ingest_reviews(db_session, ExplodingSource())

    assert report.failed == 1
    assert report.inserted == 0


def test_limit_caps_academies(db_session):
    for i in range(3):
        db_session.add(Academy(name=f"학원{i}"))
    db_session.commit()
    source = FakeSource()

    review_ingest_service.ingest_reviews(db_session, source, limit=2)

    assert len(source.calls) == 2


def test_coverage_histogram_buckets():
    report = review_ingest_service.IngestReport(per_academy={1: 0, 2: 3, 3: 7, 4: 0})

    assert report.coverage_histogram() == {"0건": 2, "1-4건": 1, "5건+": 1}


def test_stub_source_drives_full_path(db_session, academy):
    """키 없이 stub 만으로 수집 → 사후필터 → dedup 전 구간이 돌아야 한다."""
    first = review_ingest_service.ingest_reviews(db_session, StubReviewSource())
    second = review_ingest_service.ingest_reviews(db_session, StubReviewSource())

    assert first.inserted == 2
    assert second.inserted == 0
    assert second.skipped_duplicate == 2
