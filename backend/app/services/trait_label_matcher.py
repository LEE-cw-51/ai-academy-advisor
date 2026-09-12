"""Closed trait-label keyword matcher (Stage 4a vocabulary).

Keyword-first extraction for review/homepage/blog snippets. Does not write DB.
Bare ``질문`` is intentionally excluded — too common in unrelated contexts;
prefer compounds like 질문대응 / 질문 가능 / 질문하기.
"""

from __future__ import annotations

import re

# Closed vocabulary (docs/data-strategy.md Stage 4a). Longer / multi-word first.
CLOSED_LABELS: tuple[str, ...] = (
    "mentions_seonhaeng",
    "mentions_naesin",
    "mentions_suneung",
    "mentions_homework",
    "mentions_clinic",
    "mentions_qna",
)

LABEL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "mentions_seonhaeng": ("선행",),
    "mentions_naesin": ("내신",),
    "mentions_suneung": ("수능",),
    "mentions_homework": ("숙제", "과제"),
    "mentions_clinic": ("클리닉", "보강"),
    # No bare "질문" — over-matches. Prefer operational compounds.
    "mentions_qna": (
        "질문대응",
        "질문 대응",
        "질문가능",
        "질문 가능",
        "질문하기",
        "질문할 수",
        "질문을 받",
        "질문 받",
        "질문도 가능",
        "질문 시간",
        "질문시간",
        "질문 코너",
        "질문코너",
        "질의응답",
        "질의 응답",
        "QnA",
        "Q&A",
        "Q/A",
    ),
}

SOURCE_TYPES: tuple[str, ...] = ("review", "homepage", "blog")
STATUSES: tuple[str, ...] = ("candidate", "published")

_COMPILED: dict[str, list[re.Pattern[str]]] = {
    label: [re.compile(re.escape(kw), re.IGNORECASE) for kw in kws]
    for label, kws in LABEL_KEYWORDS.items()
}


def match_labels(text_value: str) -> list[tuple[str, str]]:
    """Return (label, matched_keyword) pairs; at most one hit per label."""
    if not text_value:
        return []
    found: list[tuple[str, str]] = []
    for label, patterns in _COMPILED.items():
        for pattern, kw in zip(patterns, LABEL_KEYWORDS[label]):
            if pattern.search(text_value):
                found.append((label, kw))
                break
    return found


def snippet_around(text_value: str, keyword: str, radius: int = 40) -> str:
    """Short evidence window around the matched keyword."""
    idx = text_value.lower().find(keyword.lower())
    if idx < 0:
        return text_value[:120]
    start = max(0, idx - radius)
    end = min(len(text_value), idx + len(keyword) + radius)
    piece = text_value[start:end].replace("\n", " ").strip()
    if start > 0:
        piece = "…" + piece
    if end < len(text_value):
        piece = piece + "…"
    return piece


def source_type_from_review_source(source: str | None) -> str:
    """Map reviews.source → academy_trait_labels.source_type."""
    if source == "naver_blog":
        return "blog"
    if source == "naver_cafearticle":
        return "review"
    if source and source.endswith("blog"):
        return "blog"
    return "review"
