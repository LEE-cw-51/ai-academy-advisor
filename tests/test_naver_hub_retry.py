"""naver_hub.search 429 재시도 (네트워크 없이 monkeypatch)."""

import httpx
import pytest

from app.providers.naver_hub import DEFAULT_BASE_URL, search


def test_search_retries_on_429_then_succeeds(monkeypatch):
    calls: list[int] = []

    def fake_get(url, headers=None, params=None, timeout=None):
        calls.append(1)
        if len(calls) <= 2:
            return httpx.Response(
                status_code=429,
                json={"errorMessage": "rate limit"},
                request=httpx.Request("GET", url),
            )
        return httpx.Response(
            status_code=200,
            json={"items": [{"title": "ok"}]},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr("app.providers.naver_hub.time.sleep", lambda _: None)

    items = search(
        client_id="id",
        client_secret="secret",
        base_url=DEFAULT_BASE_URL,
        endpoint="local",
        query="test",
        display=1,
        sort="comment",
    )

    assert len(calls) == 3
    assert items == [{"title": "ok"}]


def test_search_raises_after_max_429_retries(monkeypatch):
    def fake_get(url, headers=None, params=None, timeout=None):
        return httpx.Response(
            status_code=429,
            json={"errorMessage": "rate limit"},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr("app.providers.naver_hub.time.sleep", lambda _: None)

    with pytest.raises(httpx.HTTPStatusError):
        search(
            client_id="id",
            client_secret="secret",
            base_url=DEFAULT_BASE_URL,
            endpoint="local",
            query="test",
            display=1,
            sort="comment",
        )
