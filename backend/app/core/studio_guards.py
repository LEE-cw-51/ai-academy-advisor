"""Studio/Postgres CHECK 조건과 같은 규칙의 Python 부분집합.

Alembic `0006`이 이 모듈의 SQL을 그대로 쓴다. 허용 과목·거부 호스트를
바꾸면 새 마이그레이션이 필요하다.
"""

from __future__ import annotations

import json

from app.core.academy_url_guards import (
    WEBSITE_URL_DB_REJECT_MARKERS,
    website_url_has_rejected_host,
)
from app.core.subjects import SUBJECT_TAXONOMY


def subjects_pass_db_check(subjects: list[str] | None) -> bool:
    """Postgres `ck_academies_subjects_taxonomy`와 같은 허용 규칙."""
    if subjects is None:
        return True
    if not isinstance(subjects, list):
        return False
    return all(item in SUBJECT_TAXONOMY for item in subjects)


def website_url_pass_db_check(url: str | None) -> bool:
    """Postgres `ck_academies_website_not_social`과 같은 호스트 거부.

    `is_homepage_url`보다 느슨하다 — 스킴/netloc은 CHECK에 없다.
    """
    if url is None or url == "":
        return True
    return not website_url_has_rejected_host(url)


def subjects_check_predicate_sql() -> str:
    taxonomy_json = json.dumps(list(SUBJECT_TAXONOMY), ensure_ascii=False)
    return f"""
            subjects IS NULL
            OR (
                jsonb_typeof(subjects) = 'array'
                AND subjects <@ '{taxonomy_json}'::jsonb
            )
    """


def website_url_host_sql(column: str = "website_url") -> str:
    """Postgres 호스트 표현식. Python `website_url_host`와 같아야 한다."""
    rest = (
        f"CASE WHEN position('://' in {column}) > 0 "
        f"THEN substring({column} from position('://' in {column}) + 3) "
        f"ELSE {column} END"
    )
    authority = (
        f"split_part(split_part(split_part({rest}, '/', 1), '?', 1), '#', 1)"
    )
    after_userinfo = (
        f"CASE WHEN position('@' in {authority}) > 0 "
        f"THEN split_part({authority}, '@', 2) "
        f"ELSE {authority} END"
    )
    return f"lower(split_part({after_userinfo}, ':', 1))"


def website_url_check_predicate_sql() -> str:
    host = website_url_host_sql()
    clauses = []
    for marker in WEBSITE_URL_DB_REJECT_MARKERS:
        escaped = marker.replace("'", "''")
        clauses.append(
            f"NOT ({host} = '{escaped}' OR {host} LIKE '%.{escaped}')"
        )
    joined = "\n                AND ".join(clauses)
    return f"""
            website_url IS NULL
            OR (
                {joined}
            )
    """


def academies_violation_select_sql() -> str:
    """CHECK 추가 전 위반 행 조회. 0006 사전 검사와 같은 SQL."""
    return f"""
        SELECT id, name FROM academies
        WHERE NOT ({subjects_check_predicate_sql()})
           OR NOT ({website_url_check_predicate_sql()})
    """
