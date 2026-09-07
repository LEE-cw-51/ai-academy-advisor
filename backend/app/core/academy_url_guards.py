"""학원 URL 가드 — Python(`is_homepage_url`)과 Postgres CHECK가 같은 호스트 규칙을 쓴다.

호스트는 스킴 유무와 관계없이 뽑고, 포트는 제거한다. 거부는 `host == marker` 또는
`host.endswith("." + marker)`뿐이라 `notinstagram.com`·쿼리스트링 언급은 통과한다.
`is_homepage_url`은 추가로 http(s) 스킴과 점(.)이 포함된 netloc을 요구한다 —
깨진 이중 스킴 URL(`https://https//…`)은 netloc이 "https"로 잡혀 여기서 걸린다.
`names_match`·블로그 id 관련성은 여기에도 CHECK에도 없다.
"""

from __future__ import annotations

from urllib.parse import urlparse

PLACE_HOST_MARKERS: tuple[str, ...] = (
    "map.naver.com",
    "naver.me",
    "search.naver.com",
    "place.naver.com",
    "pcmap.place.naver.com",
)
CAFE_HOST_MARKERS: tuple[str, ...] = ("cafe.naver.com", "m.cafe.naver.com")
NON_HOMEPAGE_HOST_MARKERS: tuple[str, ...] = (
    "instagram.com",
    "pf.kakao.com",
    "youtube.com",
    "youtu.be",
    "litt.ly",
    "ok114.co.kr",
)
BLOG_HOST_MARKERS: tuple[str, ...] = ("blog.naver.com",)

# Postgres website_url CHECK가 거부하는 호스트 (is_homepage_url과 동일 목록).
WEBSITE_URL_DB_REJECT_MARKERS: tuple[str, ...] = (
    *NON_HOMEPAGE_HOST_MARKERS,
    *PLACE_HOST_MARKERS,
    *CAFE_HOST_MARKERS,
    *BLOG_HOST_MARKERS,
)


def website_url_host(url: str) -> str:
    """URL에서 소문자 호스트를 뽑는다. Postgres `website_url_host_sql`과 같다.

    스킴이 없으면 경로 앞을 호스트로 본다. `userinfo@`와 `:port`는 제거한다.
    """
    scheme_at = url.find("://")
    rest = url[scheme_at + 3 :] if scheme_at >= 0 else url
    authority = rest.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
    if "@" in authority:
        authority = authority.split("@")[1]
    return authority.split(":", 1)[0].lower()


def website_url_host_is_rejected(host: str, marker: str) -> bool:
    return host == marker or host.endswith("." + marker)


def website_url_has_rejected_host(url: str) -> bool:
    host = website_url_host(url)
    return any(
        website_url_host_is_rejected(host, marker)
        for marker in WEBSITE_URL_DB_REJECT_MARKERS
    )


def is_homepage_url(url: str) -> bool:
    if not url:
        return False
    if website_url_has_rejected_host(url):
        return False
    host = urlparse(url).netloc.lower()
    if "." not in host:
        # 깨진 이중 스킴("https://https//naver.me/…")은 netloc이 "https"로 잡힌다.
        # 점 없는 호스트는 공개 홈페이지일 수 없으므로 거부한다. (DB CHECK에는
        # 이 검증이 의도적으로 없다 — decision-log 2026-09-02)
        return False
    return url.startswith("http://") or url.startswith("https://")
