"""NAVER API HUB 지역 검색 (`GET /search/v1/local`)."""

from __future__ import annotations

import httpx

from app.providers import naver_hub
from app.providers.base import LocalPlace
from app.providers.naver_review import clean_text

__all__ = ["LocalPlace", "NaverLocalSearch"]


class NaverLocalSearch:
    """학원 매칭·정본 보강용 지역 검색. 리뷰 수집과는 별도."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str,
        client: httpx.Client | None = None,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._base_url = base_url.rstrip("/")
        self._client = client

    def search(self, query: str, limit: int = 5) -> list[LocalPlace]:
        display = max(1, min(limit, naver_hub.LOCAL_DISPLAY_MAX))
        rows = naver_hub.search(
            client_id=self._client_id,
            client_secret=self._client_secret,
            base_url=self._base_url,
            endpoint="local",
            query=query,
            display=display,
            sort="comment",
            client=self._client,
        )
        places: list[LocalPlace] = []
        for row in rows:
            places.append(
                LocalPlace(
                    title=clean_text(str(row.get("title") or "")),
                    link=str(row.get("link") or "").strip(),
                    category=clean_text(str(row.get("category") or "")),
                    address=str(row.get("address") or "").strip(),
                    road_address=str(row.get("roadAddress") or "").strip(),
                    telephone=str(row.get("telephone") or "").strip(),
                )
            )
        return places
