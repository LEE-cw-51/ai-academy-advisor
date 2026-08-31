"""NAVER API HUB Search 공통 HTTP 헬퍼.

개발자센터(`openapi.naver.com`, `X-Naver-Client-*`)는 쓰지 않는다.
공식: https://api.ncloud-docs.com/docs/naver-api-hub-overview
"""

from __future__ import annotations

from typing import Any

import httpx

DEFAULT_BASE_URL = "https://naverapihub.apigw.ntruss.com"

# 지역 검색 display 최댓값 (HUB 문서).
LOCAL_DISPLAY_MAX = 5


def auth_headers(client_id: str, client_secret: str) -> dict[str, str]:
    return {
        "X-NCP-APIGW-API-KEY-ID": client_id,
        "X-NCP-APIGW-API-KEY": client_secret,
    }


def endpoint_url(base_url: str, endpoint: str) -> str:
    """`endpoint`는 `blog` / `local` / `cafearticle` 등 HUB 경로 마지막 조각."""
    return f"{base_url.rstrip('/')}/search/v1/{endpoint}"


def search(
    *,
    client_id: str,
    client_secret: str,
    base_url: str,
    endpoint: str,
    query: str,
    display: int,
    sort: str,
    timeout: float = 30.0,
    client: httpx.Client | None = None,
) -> list[dict[str, Any]]:
    """Search API GET. 성공 시 `items` 배열. HTTP 오류는 그대로 올린다.

    `client`를 넘기면 그 커넥션을 재사용한다 (배치 호출용) — 없으면 매번
    `httpx.get`으로 새 연결을 연다 (기존 단발 호출과 동일하게 동작).
    """
    getter = client.get if client is not None else httpx.get
    response = getter(
        endpoint_url(base_url, endpoint),
        headers=auth_headers(client_id, client_secret),
        params={"query": query, "display": display, "sort": sort},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        return []
    return [row for row in items if isinstance(row, dict)]
