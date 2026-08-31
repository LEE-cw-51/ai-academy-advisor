"""NAVER API HUB 검색 기반 `ReviewSource` 구현.

크롤링이 아니라 **공식 Search API 호출**이다 (docs/decision-log.md 2026-08-30).
`blog`와 `cafearticle` 두 엔드포인트만 쓴다 — `cafearticle`은 공개 설정된 카페 글만
색인하므로 로그인 담벼락을 넘지 않는다. `local`(지역검색)은 리뷰가 아니라 학원 매칭용이라
여기 포함하지 않는다 (`naver_local.py`).

응답 `description`은 검색 결과 스니펫(~200자)이며 리뷰 전문이 아니다. 전문 수집은
의도적으로 하지 않는다 (그 순간 공식 API를 쓴 법적 근거가 사라진다).

Groq/OpenAI 어댑터와 동일하게 별도 SDK 없이 `httpx`만으로 호출한다.
"""

from __future__ import annotations

import html
import re
from datetime import date, datetime

import httpx

from app.providers import naver_hub
from app.providers.base import ReviewItem

# 네이버는 질의어와 일치한 부분을 <b>…</b>로 감싸고 나머지는 HTML escape해서 준다.
_TAG_RE = re.compile(r"<[^>]+>")

# 엔드포인트 → Review.source 에 기록할 라벨.
_SOURCE_LABELS = {
    "blog": "naver_blog",
    "cafearticle": "naver_cafearticle",
}


def clean_text(text: str) -> str:
    """검색 결과 텍스트에서 HTML 태그를 걷어내고 엔티티를 복원한다.

    **순서가 load-bearing이다.** 태그 제거 → `unescape` 순서를 뒤집으면, 원문에
    escape되어 있던 `&lt;b&gt;` 같은 문자열이 먼저 진짜 태그로 복원된 뒤 태그 제거에
    걸려 사용자가 실제로 쓴 텍스트가 조용히 사라진다.
    """
    return html.unescape(_TAG_RE.sub("", text)).strip()


def parse_postdate(value: object) -> date | None:
    """`blog`의 `postdate`("20260731")를 `date`로 바꾼다.

    `cafearticle` 응답에는 날짜 필드 자체가 없어 `None`이 정상이다. 형식이 어긋나도
    예외를 올리지 않는다 — 날짜 하나 때문에 리뷰를 버릴 이유가 없다.
    """
    try:
        return datetime.strptime(str(value), "%Y%m%d").date()
    except (ValueError, TypeError):
        return None


class NaverReviewSource:
    """NAVER API HUB Search를 호출하는 `ReviewSource` 구현."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str,
        endpoints: tuple[str, ...] = ("blog", "cafearticle"),
        client: httpx.Client | None = None,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._base_url = base_url.rstrip("/")
        self._endpoints = endpoints
        self._client = client

    def search(self, query: str, limit: int = 10) -> list[ReviewItem]:
        items: list[ReviewItem] = []
        for endpoint in self._endpoints:
            items.extend(self._search_one(endpoint, query, limit))
        return items

    def _search_one(self, endpoint: str, query: str, limit: int) -> list[ReviewItem]:
        rows = naver_hub.search(
            client_id=self._client_id,
            client_secret=self._client_secret,
            base_url=self._base_url,
            endpoint=endpoint,
            query=query,
            display=limit,
            sort="date",
            client=self._client,
        )
        source = _SOURCE_LABELS.get(endpoint, f"naver_{endpoint}")
        return [
            ReviewItem(
                title=clean_text(str(row.get("title") or "")),
                content=clean_text(str(row.get("description") or "")),
                url=str(row.get("link") or ""),
                source=source,
                published_at=parse_postdate(row.get("postdate")),
            )
            for row in rows
        ]
