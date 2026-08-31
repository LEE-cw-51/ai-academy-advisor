"""학원 과목 정본 taxonomy (5종). JSON `subjects` 배열에만 이 값을 쓴다."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

SUBJECT_TAXONOMY: tuple[str, ...] = ("국어", "영어", "수학", "과학", "기타")

# 긴 키워드 우선 — "지구과학"이 "과학"보다 먼저 잡혀도 같은 버킷이다.
_KEYWORD_TO_SUBJECT: tuple[tuple[str, str], ...] = (
    ("지구과학", "과학"),
    ("통합과학", "과학"),
    ("외국어", "기타"),
    ("중국어", "기타"),
    ("독서", "국어"),
    ("논술", "국어"),
    ("영어", "영어"),
    ("토익", "영어"),
    ("토플", "영어"),
    ("수학", "수학"),
    ("과학", "과학"),
    ("물리", "과학"),
    ("화학", "과학"),
    ("생물", "과학"),
    ("코딩", "기타"),
    ("프로그래밍", "기타"),
    ("일본어", "기타"),
    ("예체능", "기타"),
    ("미술", "기타"),
    ("음악", "기타"),
    ("피아노", "기타"),
)

# "국어"는 위 튜플에서 뺐다 — "외국어"/"중국어"의 부분 문자열이라 그대로 두면
# 외국어학원·중국어학원 텍스트에도 국어가 잘못 잡힌다. 두 케이스를 제외한
# 뒤에만 별도로 검사한다 (extract_subjects_from_text 참고).
_KOREAN_KEYWORD = "국어"
_KOREAN_EXCLUDE = ("외국어", "중국어")


def normalize_subjects(values: Sequence[str]) -> list[str]:
    """중복 제거 후 taxonomy 순으로 정렬. 허용 목록 밖이면 ValueError."""
    unique: list[str] = []
    seen: set[str] = set()
    unknown: list[str] = []
    for raw in values:
        item = raw.strip()
        if item in seen:
            continue
        if item not in SUBJECT_TAXONOMY:
            unknown.append(item)
            continue
        seen.add(item)
        unique.append(item)
    if unknown:
        raise ValueError(
            "subjects는 "
            + ", ".join(SUBJECT_TAXONOMY)
            + f" 만 허용합니다. 거부: {unknown}"
        )
    return [name for name in SUBJECT_TAXONOMY if name in seen]


def extract_subjects_from_text(text: str) -> list[str]:
    """공개 텍스트(카테고리·제목·스니펫)에서 taxonomy 과목을 뽑는다."""
    found: list[str] = []
    if "영수" in text and "영수증" not in text:
        found.extend(["영어", "수학"])
    if _KOREAN_KEYWORD in text and not any(x in text for x in _KOREAN_EXCLUDE):
        found.append("국어")
    for keyword, subject in _KEYWORD_TO_SUBJECT:
        if keyword in text:
            found.append(subject)
    try:
        return normalize_subjects(found)
    except ValueError:
        return []


def subjects_csv(values: Iterable[str] | None) -> str:
    if not values:
        return ""
    return "|".join(values)
