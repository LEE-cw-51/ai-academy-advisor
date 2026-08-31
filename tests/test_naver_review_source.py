"""NAVER API HUB Search `ReviewSource` 테스트 (네트워크 없이 monkeypatch)."""

from datetime import date

import httpx
import pytest

from app.core.config import get_settings
from app.providers.base import ReviewItem, ReviewSource
from app.providers.factory import get_review_source
from app.providers.naver_hub import DEFAULT_BASE_URL
from app.providers.naver_review import (
    NaverReviewSource,
    clean_text,
    parse_postdate,
)
from app.providers.stub import StubReviewSource

BASE_URL = DEFAULT_BASE_URL


def _blog_payload(**overrides):
    row = {
        "title": "미사 <b>가온수학</b> 후기",
        "link": "https://blog.naver.com/someone/1",
        "description": "아이가 다녀본 <b>가온수학</b> 이야기 &amp; 정리",
        "postdate": "20260731",
    }
    row.update(overrides)
    return {"items": [row]}


def _fake_get(payload, captured=None, status_code=200):
    def fake_get(url, headers=None, params=None, timeout=None):
        if captured is not None:
            captured.setdefault("calls", []).append(
                {"url": url, "headers": headers, "params": params, "timeout": timeout}
            )
        return httpx.Response(
            status_code=status_code,
            json=payload,
            request=httpx.Request("GET", url),
        )

    return fake_get


def _source(**kwargs):
    return NaverReviewSource(
        client_id="test-id",
        client_secret="test-secret",
        base_url=BASE_URL,
        **kwargs,
    )


def test_sends_expected_url_headers_and_params(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr(httpx, "get", _fake_get(_blog_payload(), captured))

    _source(endpoints=("blog",)).search("가온수학", limit=5)

    call = captured["calls"][0]
    assert call["url"] == f"{BASE_URL}/search/v1/blog"
    assert call["headers"] == {
        "X-NCP-APIGW-API-KEY-ID": "test-id",
        "X-NCP-APIGW-API-KEY": "test-secret",
    }
    assert call["params"] == {"query": "가온수학", "display": 5, "sort": "date"}


def test_queries_both_endpoints_and_labels_source(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr(httpx, "get", _fake_get(_blog_payload(), captured))

    items = _source().search("가온수학")

    urls = [call["url"] for call in captured["calls"]]
    assert urls == [
        f"{BASE_URL}/search/v1/blog",
        f"{BASE_URL}/search/v1/cafearticle",
    ]
    assert [item.source for item in items] == ["naver_blog", "naver_cafearticle"]


def test_strips_bold_tags_and_unescapes_entities(monkeypatch):
    monkeypatch.setattr(httpx, "get", _fake_get(_blog_payload()))

    item = _source(endpoints=("blog",)).search("가온수학")[0]

    assert item.title == "미사 가온수학 후기"
    assert item.content == "아이가 다녀본 가온수학 이야기 & 정리"


def test_tag_strip_happens_before_unescape(monkeypatch):
    """순서가 뒤집히면 사용자가 실제로 쓴 텍스트가 조용히 사라진다.

    원문에 escape되어 있던 `&lt;b&gt;`는 태그가 아니라 **보이는 글자**다. unescape를
    먼저 하면 진짜 태그로 복원된 뒤 태그 제거에 걸려 없어진다.
    """
    monkeypatch.setattr(
        httpx,
        "get",
        _fake_get(_blog_payload(description="설명에 &lt;b&gt; 라고 적혀 있었다")),
    )

    item = _source(endpoints=("blog",)).search("가온수학")[0]

    assert item.content == "설명에 <b> 라고 적혀 있었다"


def test_blog_postdate_parsed_cafearticle_has_none(monkeypatch):
    # cafearticle 응답에는 날짜 필드가 아예 없다 — 결측이 아니라 정상이다.
    monkeypatch.setattr(httpx, "get", _fake_get(_blog_payload()))
    assert _source(endpoints=("blog",)).search("가온수학")[0].published_at == date(
        2026, 7, 31
    )

    payload = _blog_payload()
    del payload["items"][0]["postdate"]
    monkeypatch.setattr(httpx, "get", _fake_get(payload))
    assert _source(endpoints=("cafearticle",)).search("가온수학")[0].published_at is None


@pytest.mark.parametrize("value", ["", "2026-07-31", "notadate", None, 20260731.5])
def test_malformed_postdate_becomes_none_instead_of_raising(value):
    assert parse_postdate(value) is None


def test_clean_text_on_empty_and_tag_only():
    assert clean_text("") == ""
    assert clean_text("<b></b>") == ""


def test_raises_on_http_error(monkeypatch):
    monkeypatch.setattr(httpx, "get", _fake_get({"errorMessage": "nope"}, status_code=401))

    with pytest.raises(httpx.HTTPStatusError):
        _source(endpoints=("blog",)).search("가온수학")


def test_empty_items_returns_empty_list(monkeypatch):
    monkeypatch.setattr(httpx, "get", _fake_get({"items": []}))

    assert _source().search("없는학원") == []


def test_stub_review_source_is_deterministic():
    # 같은 질의 → 같은 url 이어야 ingest 의 dedup 을 네트워크 없이 검증할 수 있다.
    stub = StubReviewSource()
    first = stub.search("가온수학")
    second = stub.search("가온수학")

    assert first == second
    assert all(isinstance(item, ReviewItem) for item in first)
    # 이름 사후필터를 통과해야 stub 만으로 수집 경로 전체가 돈다.
    assert all("가온수학" in item.content for item in first)
    assert stub.search("다른학원")[0].url != first[0].url


def test_stub_respects_limit():
    assert len(StubReviewSource().search("가온수학", limit=1)) == 1


def test_factory_returns_stub_by_default():
    source = get_review_source()

    assert isinstance(source, StubReviewSource)
    assert isinstance(source, ReviewSource)


def test_factory_returns_naver_when_configured(monkeypatch):
    monkeypatch.setenv("REVIEW_SOURCE", "naver")
    monkeypatch.setenv("NAVER_CLIENT_ID", "test-id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "test-secret")
    get_settings.cache_clear()
    get_review_source.cache_clear()
    try:
        assert isinstance(get_review_source(), NaverReviewSource)
    finally:
        get_settings.cache_clear()
        get_review_source.cache_clear()


def test_factory_rejects_unknown_review_source(monkeypatch):
    monkeypatch.setenv("REVIEW_SOURCE", "hwacha")
    get_settings.cache_clear()
    get_review_source.cache_clear()
    try:
        with pytest.raises(ValueError, match="지원하지 않는 review_source"):
            get_review_source()
    finally:
        get_settings.cache_clear()
        get_review_source.cache_clear()
