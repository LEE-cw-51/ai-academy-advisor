"""Operational DB 감지 — JSON 임포트·stub 리뷰 수집이 운영 DB를 오염시키지 않게 한다."""

from __future__ import annotations

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


def stub_review_ingest_allowed(database_url: str, review_source: str) -> tuple[bool, str]:
    """운영 DB에 stub 가짜 후기를 넣는 사고를 막는다.

    실수집은 REVIEW_SOURCE=naver. 로컬·테스트(SQLite 포함)에서만 stub을 허용한다.
    """
    if (review_source or "").strip().lower() != "stub":
        return True, ""
    if is_local_database_url(database_url):
        return True, ""
    return (
        False,
        "운영 DB(Supabase/Railway 등)에는 REVIEW_SOURCE=stub 수집을 거부합니다. "
        "stub은 결정적 가짜 후기라 사실 DB·공개 후기와 섞이면 안 됩니다. "
        "실수집은 REVIEW_SOURCE=naver 와 session pooler(5432)로 실행하세요.",
    )


def academy_import_allowed(
    database_url: str,
    *,
    force: bool = False,
    allow_academy_import: bool | None = None,
) -> tuple[bool, str]:
    if force:
        return True, ""
    if allow_academy_import is None:
        # 순환 import 방지: Settings가 is_local_database_url을 쓰므로 지연 로드.
        from app.core.config import get_settings

        allow_academy_import = get_settings().allow_academy_import
    if allow_academy_import:
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
