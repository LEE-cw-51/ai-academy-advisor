"""robots.txt 사전점검 CLI — "허용된 소스만" 브라우저 수집의 게이트.

사용:
    cd backend
    uv run python -m app.cli.check_robots https://map.naver.com/p/ https://place.map.kakao.com/

각 URL에 대해 기본 UA와 `*`로 robots.txt를 읽어 allow/deny·HTTP 상태를 출력한다.
- robots.txt가 200이 아니면(429/403/5xx) `blocked` — 봇 차단으로 간주, 수집 불가.
- robots가 `Disallow: /`이면 `disallowed`.
- 그 외 대상 경로가 허용되면 `allowed`.

하나라도 allowed가 아니면 종료코드 1. 이 도구가 "허용 소스가 나타났다"의 판정
기준이다. robots·약관을 무시하거나 우회하는 코드는 이 저장소에 두지 않는다
(docs/decision-log.md 2026-09-11).
"""

from __future__ import annotations

import argparse
import sys
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx

# 기본 UA는 위장하지 않는다 — 있는 그대로 판정받는다.
_USER_AGENT = "ai-academy-advisor-preflight"


def robots_url_for(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}/robots.txt"


def evaluate(url: str, robots_text: str | None, status: int | None) -> str:
    """allowed / disallowed / blocked 중 하나를 판정한다."""
    if robots_text is None:
        return f"blocked(status={status})"
    parser = RobotFileParser()
    parser.parse(robots_text.splitlines())
    allowed = parser.can_fetch(_USER_AGENT, url)
    return "allowed" if allowed else "disallowed"


def _fetch_robots(url: str, timeout: float) -> tuple[str | None, int | None]:
    robots = robots_url_for(url)
    try:
        resp = httpx.get(
            robots, headers={"User-Agent": _USER_AGENT}, timeout=timeout
        )
    except httpx.HTTPError as exc:
        print(f"  robots 요청 실패: {exc}", file=sys.stderr)
        return None, None
    if resp.status_code != 200:
        return None, resp.status_code
    return resp.text, resp.status_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="대상 URL이 robots.txt상 수집 허용인지 사전 점검한다 (우회 없음)."
    )
    parser.add_argument("urls", nargs="+", help="점검할 URL들")
    parser.add_argument("--timeout", type=float, default=15.0, help="요청 타임아웃(초)")
    args = parser.parse_args(argv)

    all_allowed = True
    for url in args.urls:
        robots_text, status = _fetch_robots(url, args.timeout)
        verdict = evaluate(url, robots_text, status)
        if verdict != "allowed":
            all_allowed = False
        print(f"{verdict}\t{url}\t(robots {robots_url_for(url)})")

    if not all_allowed:
        print(
            "\n하나 이상이 allowed가 아니다 — 그 소스는 수집하지 않는다. "
            "robots·약관을 우회하지 않는다.",
            file=sys.stderr,
        )
        return 1
    print("\n모든 URL이 allowed — 약관 확인·Founder 승인 후 어댑터를 연결한다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
