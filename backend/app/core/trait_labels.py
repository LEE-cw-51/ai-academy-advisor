"""닫힌 특징 라벨 어휘 — DB CHECK 와 앱 코드의 단일 정의.

`studio_guards` 와 같은 자리다: Postgres 제약과 Python 허용 목록이 갈라지지 않게
`core` 에 둔다. 계층이 `api → services → repositories → models/DB` 이므로 모델이
서비스를 import 할 수 없고, 그래서 어휘가 여기 있다.

어휘를 바꾸면 **새 마이그레이션이 필요하다** (`academy_trait_labels` 의 CHECK 세 개).
`app.services.trait_label_matcher` 가 여기 라벨마다 키워드를 붙이며, 둘이 같은
집합인지는 `tests/test_trait_labels.py` 가 강제한다.
"""

from __future__ import annotations

# docs/data-strategy.md Stage 4a. 자유 태그 금지 — 좋음/나쁨·가성비·별점은 넣지 않는다.
CLOSED_LABELS: tuple[str, ...] = (
    "mentions_seonhaeng",
    "mentions_naesin",
    "mentions_suneung",
    "mentions_homework",
    "mentions_clinic",
    "mentions_qna",
)

SOURCE_TYPES: tuple[str, ...] = ("review", "homepage", "blog")
STATUSES: tuple[str, ...] = ("candidate", "published")


def sql_in_list(values: tuple[str, ...]) -> str:
    """CHECK `col IN (...)` 의 값 목록. 어휘가 상수라 이스케이프는 필요 없다."""
    return ", ".join(f"'{value}'" for value in values)
