"""Operational DB 감지 — import_academies가 Studio 수정을 덮어쓰지 않게 한다."""

from __future__ import annotations

import os
from urllib.parse import urlparse

_LOCAL_HOSTS = frozenset(
    {
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "db",
        "postgres",
        "host.docker.internal",
    }
)


def _normalized_host(database_url: str) -> str:
    url = database_url.replace("postgresql+psycopg://", "postgresql://")
    return (urlparse(url).hostname or "").lower()


def is_local_database_url(database_url: str) -> bool:
    """로컬·테스트 DB — JSON→DB sync가 기본 허용된다."""
    lowered = database_url.lower()
    if "sqlite" in lowered:
        return True
    return _normalized_host(database_url) in _LOCAL_HOSTS


def is_operational_database_url(database_url: str) -> bool:
    """Supabase/Railway 등 운영 DB — Studio가 정본이므로 import 기본 거부."""
    return not is_local_database_url(database_url)


def academy_import_allowed(
    database_url: str,
    *,
    force: bool = False,
) -> tuple[bool, str]:
    if force:
        return True, ""
    if os.environ.get("ALLOW_ACADEMY_IMPORT", "").strip() == "1":
        return True, ""
    if is_operational_database_url(database_url):
        return (
            False,
            "운영 DB(Supabase/Railway 등)에는 기본적으로 JSON 임포트를 거부합니다. "
            "Supabase Studio에서 수정한 학원 사실을 덮어쓸 수 있습니다. "
            "의도적 컷오버·재해복구 시에만 --force 또는 ALLOW_ACADEMY_IMPORT=1을 "
            "사용하세요.",
        )
    return True, ""
