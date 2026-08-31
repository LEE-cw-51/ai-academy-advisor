"""NAVER API HUB 지역 검색 (`GET /search/v1/local`)."""

from __future__ import annotations

from dataclasses import dataclass

from app.providers import naver_hub
from app.providers.naver_review import clean_text


@dataclass(frozen=True)
class LocalPlace:
    title: str
    link: str
    category: str
    address: str
    road_address: str


class NaverLocalSearch:
    """학원 매칭·정본 보강용 지역 검색. 리뷰 수집과는 별도."""

    def __init__(self, client_id: str, client_secret: str, base_url: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._base_url = base_url.rstrip("/")

    def search(self, query: str, limit: int = 5) -> list[LocalPlace]:
        display = max(1, min(limit, naver_hub.LOCAL_DISPLAY_MAX))
        rows = naver_hub.search(
            client_id=self._client_id,
            client_secret=self._client_secret,
            base_url=self._base_url,
            endpoint="local",
            query=query,
            display=display,
            sort="random",
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
                )
            )
        return places
