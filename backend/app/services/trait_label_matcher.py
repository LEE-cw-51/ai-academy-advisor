"""Closed trait-label keyword matcher (Stage 4a vocabulary).

Keyword-first extraction for review/homepage/blog snippets. Does not write DB.

한국어에는 어절 경계가 없어서 bare 키워드를 부분 문자열로 찾으면 반드시 오탐한다.
실제로 걸렸던 것들: ``보내신``·``안내신청``·``지내신``(내신), ``보강공사``(보강),
``수능시계``(수능), ``과제물 배송``(과제). 이 스니펫은 후보 카드의 "주관 신호" 근거로
그대로 노출되므로, 잘못 붙은 라벨은 없는 것보다 나쁘다 (`review_ingest_service`의
귀속 원칙과 같다).

그래서 bare 키워드는 **앞뒤 문맥 규칙**으로만 매칭한다:

- 앞: 한글이 아니거나(문장 시작·공백·문장부호·영숫자) 허용 접두사(`중등`·`수학`…)
- 뒤: 한글이 아니거나 조사(`은`·`이랑`…) 또는 허용 복합어(`대비`·`관리`…)

정밀도를 재현율보다 앞에 둔 선택이다. 예상 못 한 복합어(`내신컨설팅` 같은)는 놓치며,
놓친 게 보이면 `_SUFFIXES`에 추가한다. 조사와 공백이 명사 뒤 대부분을 차지하므로
재현율 손실은 명사+명사 복합어로 한정된다.

``질문``은 이 규칙으로도 과하다 (`질문했습니다`·`질문이 많아요`는 학원 운영 특징이
아니다). 그래서 bare 키워드를 아예 두지 않고 ``질문대응``류 복합어만 쓰며, 그 복합어는
이미 경계가 분명하므로 위 규칙을 적용하지 않는다 (`_COMPOUND_ONLY_LABELS`).
"""

from __future__ import annotations

import re

_HANGUL = "가-힣"

# 키워드 앞에 붙어도 뜻이 같은 말 — 과목·학년·운영 수식어.
# 여기에 없는 한글이 앞에 붙으면 다른 단어다 (보내신·안내신·지내신).
_PREFIXES: tuple[str, ...] = (
    "국어",
    "영어",
    "수학",
    "과학",
    "사회",
    "초등",
    "중등",
    "고등",
    "중학",
    "고교",
    "학교",
    "학기",
    "정시",
    "매일",
    "오답",
    "무료",
    "결석",
    "추가",
    "개별",
    "내신",
)

# 키워드 뒤 조사. 긴 것을 앞에 둬서 `이랑`이 `이`로 잘리지 않게 한다.
_JOSA: tuple[str, ...] = (
    "입니다",
    "이에요",
    "이랑",
    "으로",
    "까지",
    "부터",
    "이나",
    "보다",
    "처럼",
    "마다",
    "밖에",
    "이고",
    "이라",
    "예요",
    "은",
    "는",
    "이",
    "가",
    "을",
    "를",
    "도",
    "만",
    "과",
    "와",
    "에",
    "의",
    "로",
    "랑",
    "요",
    "나",
    "고",
    "라",
    "인",
    "임",
)

# 키워드 뒤에 붙어도 뜻이 같은 말 — 명사+명사 복합어와 용언화.
# 완전 토큰으로 맞춘다: `시`가 아니라 `시험`이어야 `수능시계`가 걸러진다.
_SUFFIXES: tuple[str, ...] = (
    "클래스",
    "대비",
    "준비",
    "관리",
    "수업",
    "시험",
    "특강",
    "성적",
    "기간",
    "위주",
    "전문",
    "과정",
    "시간",
    "검사",
    "학습",
    "진도",
    "점수",
    "등급",
    "반",
    "량",
    "중",
    "하",
    "해",
    "했",
    "합",
    "함",
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

# Closed vocabulary (docs/data-strategy.md Stage 4a). 손으로 쓴 사본을 두지 않는다 —
# 모델 CHECK(`app.models.academy_trait_label`)가 이 값을 그대로 쓴다.
CLOSED_LABELS: tuple[str, ...] = tuple(LABEL_KEYWORDS)

SOURCE_TYPES: tuple[str, ...] = ("review", "homepage", "blog")
STATUSES: tuple[str, ...] = ("candidate", "published")

# 키워드 자체가 이미 복합어라 경계 규칙을 적용하지 않는 라벨.
# `질문을 받` 처럼 어절 중간에서 끝나는 패턴이 있어 뒤 문맥을 강제할 수 없다.
_COMPOUND_ONLY_LABELS: frozenset[str] = frozenset({"mentions_qna"})


def _boundary_pattern(keyword: str) -> str:
    """bare 키워드를 앞뒤 문맥 규칙으로 감싼 정규식 소스."""
    kw = re.escape(keyword)
    pre_alt = "|".join(re.escape(p) for p in _PREFIXES)
    post_alt = "|".join(re.escape(s) for s in (*_JOSA, *_SUFFIXES))
    head = f"(?:(?<![{_HANGUL}]){kw}|(?:{pre_alt}){kw})"
    tail = f"(?:(?![{_HANGUL}])|(?:{post_alt}))"
    return head + tail


def _compile(label: str, keyword: str) -> re.Pattern[str]:
    if label in _COMPOUND_ONLY_LABELS:
        return re.compile(re.escape(keyword), re.IGNORECASE)
    return re.compile(_boundary_pattern(keyword), re.IGNORECASE)


_COMPILED: dict[str, list[re.Pattern[str]]] = {
    label: [_compile(label, kw) for kw in kws] for label, kws in LABEL_KEYWORDS.items()
}

# 키워드는 라벨 간 겹치지 않으므로 역인덱스가 성립한다 (스니펫 위치 계산용).
_PATTERN_BY_KEYWORD: dict[str, re.Pattern[str]] = {
    kw: pattern
    for label, kws in LABEL_KEYWORDS.items()
    for kw, pattern in zip(kws, _COMPILED[label])
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


def _accepted_index(text_value: str, keyword: str) -> int:
    """경계 규칙을 통과한 occurrence 의 위치. 없으면 단순 탐색으로 되돌아간다.

    `보내신 ... 내신 대비` 처럼 거부된 occurrence 가 앞설 수 있다. 단순 `find` 로
    창을 잡으면 근거 스니펫이 매칭되지 않은 자리를 가리킨다.
    """
    pattern = _PATTERN_BY_KEYWORD.get(keyword)
    if pattern is not None:
        match = pattern.search(text_value)
        if match is not None:
            accepted = text_value.lower().find(keyword.lower(), match.start())
            if accepted >= 0:
                return accepted
    return text_value.lower().find(keyword.lower())


def snippet_around(text_value: str, keyword: str, radius: int = 40) -> str:
    """Short evidence window around the matched keyword."""
    idx = _accepted_index(text_value, keyword)
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
