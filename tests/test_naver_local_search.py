"""NAVER API HUB Search `LocalSearchProvider` 테스트 (네트워크 없이 monkeypatch)."""

import httpx
import pytest

from app.core.config import get_settings
from app.providers.base import LocalPlace, LocalSearchProvider
from app.providers.factory import get_local_search_provider
from app.providers.naver_hub import DEFAULT_BASE_URL
from app.providers.naver_local import NaverLocalSearch
from app.providers.stub import StubLocalSearchProvider

BASE_URL = DEFAULT_BASE_URL


def _local_payload(**overrides):
    row = {
        "title": "미사 <b>가온수학</b>학원",
        "link": "https://gaon-math.example.com",
        "category": "학원>수학학원",
        "address": "경기 하남시 미사동 1",
        "roadAddress": "경기 하남시 미사강변대로 1",
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
    return NaverLocalSearch(
        client_id="test-id",
        client_secret="test-secret",
        base_url=BASE_URL,
        **kwargs,
    )


def test_sends_expected_url_headers_and_params(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr(httpx, "get", _fake_get(_local_payload(), captured))

    _source().search("가온수학", limit=5)

    call = captured["calls"][0]
    assert call["url"] == f"{BASE_URL}/search/v1/local"
    assert call["headers"] == {
        "X-NCP-APIGW-API-KEY-ID": "test-id",
        "X-NCP-APIGW-API-KEY": "test-secret",
    }
    assert call["params"] == {"query": "가온수학", "display": 5, "sort": "random"}


def test_parses_place_and_strips_tags(monkeypatch):
    monkeypatch.setattr(httpx, "get", _fake_get(_local_payload()))

    place = _source().search("가온수학")[0]

    assert place == LocalPlace(
        title="미사 가온수학학원",
        link="https://gaon-math.example.com",
        category="학원>수학학원",
        address="경기 하남시 미사동 1",
        road_address="경기 하남시 미사강변대로 1",
    )


def test_raises_on_http_error(monkeypatch):
    monkeypatch.setattr(httpx, "get", _fake_get({"errorMessage": "nope"}, status_code=401))

    with pytest.raises(httpx.HTTPStatusError):
        _source().search("가온수학")


def test_empty_items_returns_empty_list(monkeypatch):
    monkeypatch.setattr(httpx, "get", _fake_get({"items": []}))

    assert _source().search("없는학원") == []


def test_stub_local_search_is_deterministic():
    stub = StubLocalSearchProvider()
    first = stub.search("가온수학")
    second = stub.search("가온수학")

    assert first == second
    assert all(isinstance(place, LocalPlace) for place in first)
    assert stub.search("다른학원")[0].link != first[0].link


def test_factory_returns_stub_by_default():
    provider = get_local_search_provider()

    assert isinstance(provider, StubLocalSearchProvider)
    assert isinstance(provider, LocalSearchProvider)


def test_factory_returns_naver_when_configured(monkeypatch):
    monkeypatch.setenv("LOCAL_SEARCH_PROVIDER", "naver")
    monkeypatch.setenv("NAVER_CLIENT_ID", "test-id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "test-secret")
    get_settings.cache_clear()
    get_local_search_provider.cache_clear()
    try:
        assert isinstance(get_local_search_provider(), NaverLocalSearch)
    finally:
        get_settings.cache_clear()
        get_local_search_provider.cache_clear()


def test_factory_rejects_unknown_local_search_provider(monkeypatch):
    monkeypatch.setenv("LOCAL_SEARCH_PROVIDER", "hwacha")
    get_settings.cache_clear()
    get_local_search_provider.cache_clear()
    try:
        with pytest.raises(ValueError, match="지원하지 않는 local_search_provider"):
            get_local_search_provider()
    finally:
        get_settings.cache_clear()
        get_local_search_provider.cache_clear()
