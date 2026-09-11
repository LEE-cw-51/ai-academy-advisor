"""check_robots.evaluate 판정 (네트워크 없음, fixture 텍스트)."""

from app.cli.check_robots import evaluate, robots_url_for


def test_robots_url_for():
    assert robots_url_for("https://map.naver.com/p/x") == "https://map.naver.com/robots.txt"


def test_disallow_all_is_disallowed():
    robots = "User-agent: *\nDisallow: /\nAllow: /$"
    assert evaluate("https://map.naver.com/p/entry", robots, 200) == "disallowed"


def test_non_200_robots_is_blocked():
    assert evaluate("https://m.place.naver.com/x", None, 429).startswith("blocked")


def test_open_robots_is_allowed():
    robots = "User-agent: *\nAllow: /"
    assert evaluate("https://example.com/reviews", robots, 200) == "allowed"


def test_home_only_allow_disallows_deep_path():
    # 네이버 지도 패턴: 홈만 허용, 나머지 차단.
    robots = "User-agent: *\nDisallow: /\nAllow: /$\nAllow: /p/$"
    assert evaluate("https://map.naver.com/p/review/123", robots, 200) == "disallowed"
