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


def test_attributed_item_skips_name_filter_and_stores_rating(db_session, academy):
    # 플레이스형 소스: 학원명이 본문에 없어도(귀속이 자명) 수집하고 rating을 저장한다.
    unmatched = ReviewItem(
        title="정말 좋은 학원",
        content="선생님이 친절해요",  # "가온수학" 문자열 없음
        url="https://place.example/review/1",
        source="naver_place",
        published_at=None,
        rating=5,
        attributed=True,
    )
    source = FakeSource({"가온수학": [unmatched]})

    report = review_ingest_service.ingest_reviews(db_session, source)

    assert report.inserted == 1
    assert report.skipped_unmatched == 0
    rows = _reviews(db_session)
    assert rows[0].rating == 5
    assert rows[0].source == "naver_place"


def test_unattributed_item_without_name_is_skipped(db_session, academy):
    # 기본(attributed=False)은 이름 사후필터로 오귀속을 막는다.
    unmatched = ReviewItem(
        title="정말 좋은 학원",
        content="선생님이 친절해요",
        url="https://blog.example/2",
        source="naver_blog",
        published_at=None,
    )
    source = FakeSource({"가온수학": [unmatched]})

    report = review_ingest_service.ingest_reviews(db_session, source)

    assert report.inserted == 0
    assert report.skipped_unmatched == 1


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


@pytest.mark.parametrize(
    ("short_name", "long_name"),
    [
        ("한수학학원", "더(The)착한수학학원"),
        ("피플미술학원", "미사피플미술학원"),
        ("탑수학학원", "아이탑수학학원"),
        ("김종인국어전문학원", "김종인국어전문학원중등관학원"),
    ],
)
def test_shorter_seed_name_does_not_claim_longer_academy_review(
    db_session, short_name, long_name
):
    """시드 충돌 쌍: 짧은 등록명이 긴 등록명의 부분 문자열이면 경계·긴 이름 우선."""
    short = Academy(name=short_name, address="경기도 하남시")
    long = Academy(name=long_name, address="경기도 하남시")
    db_session.add_all([short, long])
    db_session.commit()

    about_long = ReviewItem(
        title=f"{long_name} 후기",
        content=f"{long_name} 다녀왔어요",
        url="https://blog.example/longer",
        source="naver_blog",
        published_at=None,
    )
    assert not review_ingest_service.matches_academy(
        about_long,
        short,
        registered_names=[short_name, long_name],
    )
    assert review_ingest_service.matches_academy(
        about_long,
        long,
        registered_names=[short_name, long_name],
    )

    # 짧은 학원만 언급된 글은 짧은 쪽에만 귀속된다.
    about_short = ReviewItem(
        title=f"{short_name} 후기",
        content=f"{short_name} 좋아요",
        url="https://blog.example/shorter",
        source="naver_blog",
        published_at=None,
    )
    assert review_ingest_service.matches_academy(
        about_short,
        short,
        registered_names=[short_name, long_name],
    )
    assert not review_ingest_service.matches_academy(
        about_short,
        long,
        registered_names=[short_name, long_name],
    )


def test_academy_name_with_trailing_josa_still_matches(db_session, academy):
    """본문에 조사가 붙어도 (`가온수학은`) 귀속된다."""
    item = ReviewItem(
        title="후기",
        content="가온수학은 숙제가 많아요",
        url="https://blog.example/josa",
        source="naver_blog",
        published_at=None,
    )
    assert review_ingest_service.matches_academy(item, academy)


def test_ingest_skips_substring_collision_pair(db_session):
    """수집 경로에서도 짧은 학원이 긴 학원 글을 가져가지 않는다."""
    short = Academy(name="한수학학원", address="경기도 하남시")
    long = Academy(name="더(The)착한수학학원", address="경기도 하남시")
    db_session.add_all([short, long])
    db_session.commit()

    about_long = ReviewItem(
        title="더(The)착한수학학원 후기",
        content="더(The)착한수학학원 강사가 친절해요",
        url="https://blog.example/collision",
        source="naver_blog",
        published_at=None,
    )
    source = FakeSource(
        {
            "한수학학원": [about_long],
            "더(The)착한수학학원": [about_long],
        }
    )

    report = review_ingest_service.ingest_reviews(db_session, source)

    rows = _reviews(db_session)
    assert report.inserted == 1
    assert report.skipped_unmatched == 1
    assert len(rows) == 1
    assert rows[0].academy_id == long.id


def test_raw_payload_has_stub_source_detects_stub_items():
    stub_item = ReviewItem(
        title="stub",
        content="stub",
        url="https://example.invalid/stub/1",
        source="stub",
        published_at=None,
    )
    naver_item = ReviewItem(
        title="real",
        content="real",
        url="https://blog.example/1",
        source="naver_blog",
        published_at=None,
    )
    assert review_ingest_service.raw_payload_has_stub_source({1: [stub_item]})
    assert review_ingest_service.raw_payload_has_stub_source(
        {1: [naver_item], 2: [stub_item]}
    )
    assert not review_ingest_service.raw_payload_has_stub_source({1: [naver_item]})


def test_cli_from_raw_refuses_stub_cache_on_operational(tmp_path, monkeypatch, capsys):
    """REVIEW_SOURCE=naver 여도 운영 DB + stub 캐시 --from-raw 는 CLI에서 막는다."""
    from app.cli import ingest_reviews

    day = tmp_path / "2026-08-02"
    day.mkdir()
    (day / "1.json").write_text(
        '[{"title":"t","content":"c","url":"https://example.invalid/s","source":"stub"}]',
        encoding="utf-8",
    )

    class _Settings:
        database_url = (
            "postgresql+psycopg://postgres:pass@db.abcdef.supabase.co:5432/postgres"
        )
        review_source = "naver"
        naver_display = 10

    monkeypatch.setattr("app.core.config.get_settings", lambda: _Settings())
    exit_code = ingest_reviews.main(["--from-raw", str(tmp_path), "--dry-run"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "stub" in captured.err
    assert "거부" in captured.err


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


def test_source_yield_line_zeros_when_empty():
    assert (
        review_ingest_service.IngestReport().source_yield_line()
        == "소스: naver_blog=0 naver_cafearticle=0"
    )


def test_source_yield_line_reports_every_configured_source():
    """NAVER_REVIEW_ENDPOINTS 는 설정값이다 — kin/webkr 을 켜면 그 수율도 보여야 한다.

    고정 2종만 찍으면 운영자는 "아무것도 안 들어왔다"로 읽지만 실제로는 적재된다.
    """
    report = review_ingest_service.IngestReport(
        by_source={"naver_blog": 1, "naver_kin": 5, "naver_webkr": 2}
    )
    line = report.source_yield_line()
    assert line.startswith("소스: naver_blog=1 naver_cafearticle=0")
    assert "naver_kin=5" in line
    assert "naver_webkr=2" in line


def test_report_counts_blog_and_cafearticle_yield(db_session, academy):
    """수율은 삽입 전 fetched. 이름 필터에 걸린 카페글도 cafearticle 건수에 남긴다."""
    cafe_hit = ReviewItem(
        title="가온수학 공개 카페",
        content="가온수학 다녀왔어요",
        url="https://cafe.example/1",
        source="naver_cafearticle",
        published_at=None,
    )
    cafe_unmatched = ReviewItem(
        title="옆집 후기",
        content="영어 잘 가르쳐요",
        url="https://cafe.example/2",
        source="naver_cafearticle",
        published_at=None,
    )
    source = FakeSource(
        {"가온수학": [_item("https://blog.example/1"), cafe_hit, cafe_unmatched]}
    )

    report = review_ingest_service.ingest_reviews(db_session, source)

    assert report.by_source["naver_blog"] == 1
    assert report.by_source["naver_cafearticle"] == 2
    assert report.inserted == 2
    assert report.skipped_unmatched == 1
    assert report.source_yield_line() == "소스: naver_blog=1 naver_cafearticle=2"


def test_stub_source_drives_full_path(db_session, academy):
    """키 없이 stub 만으로 수집 → 사후필터 → dedup 전 구간이 돌아야 한다."""
    first = review_ingest_service.ingest_reviews(db_session, StubReviewSource())
    second = review_ingest_service.ingest_reviews(db_session, StubReviewSource())

    assert first.inserted == 2
    assert second.inserted == 0
    assert second.skipped_duplicate == 2
