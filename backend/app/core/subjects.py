"""학원 과목 정본 taxonomy (4종) + 기타 세부 라벨.

JSON `subjects` 배열에는 taxonomy 4종만 쓴다. 국어·영어·수학은 확정 분류하고,
그 외 모든 과목은 `기타` 버킷에 넣되 원래 이름은 `subject_detail`(자유 라벨)에
따로 남긴다 — 배지·랭킹에서 "피아노"·"미술"·"과학"을 잃지 않기 위해서다.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

SUBJECT_TAXONOMY: tuple[str, ...] = ("국어", "영어", "수학", "기타")


@dataclass(frozen=True)
class SubjectHit:
    """텍스트에서 뽑은 과목 신호 1건. `label`은 `기타` 버킷의 세부 이름."""

    subject: str
    label: str | None = None


# (키워드, 버킷들, 세부 라벨). 버킷이 비면 "소비 전용"(오탐 방지)이다.
# extract_subject_hits 가 **긴 키워드부터 매치 구간을 소비**하므로, 짧은 키워드가
# 이미 소비된 자리에서 다시 걸리지 않는다. "국어"가 "외국어/중국어"에, "영수"가
# "영수증"에, "독서"가 "독서실"에 오탐하던 예전 특례를 이 방식이 통째로 대체한다.
# `기타` 버킷 키워드의 라벨은 절대 "기타"가 아니다(악기 기타는 "기타(악기)").
_KEYWORDS: tuple[tuple[str, tuple[str, ...], str | None], ...] = (
    # 소비 전용 — 오탐 방지
    ("영수증", (), None),
    ("독서실", (), None),
    # 국어
    ("영어독서", ("영어",), None),
    ("원서읽기", ("영어",), None),
    ("영수", ("영어", "수학"), None),
    ("독서", ("국어",), None),
    ("논술", ("국어",), None),
    ("글쓰기", ("국어",), None),
    ("국어", ("국어",), None),
    # 영어
    ("영어회화", ("영어",), None),
    ("영어", ("영어",), None),
    ("토익", ("영어",), None),
    ("토플", ("영어",), None),
    # 수학
    ("수학", ("수학",), None),
    # 기타 + 세부 라벨 (과학은 taxonomy에서 빠져 기타/과학으로 들어간다)
    ("지구과학", ("기타",), "과학"),
    ("통합과학", ("기타",), "과학"),
    ("과학", ("기타",), "과학"),
    ("물리", ("기타",), "과학"),
    ("화학", ("기타",), "과학"),
    ("생물", ("기타",), "과학"),
    ("클래식기타", ("기타",), "기타(악기)"),
    ("통기타", ("기타",), "기타(악기)"),
    ("실용음악", ("기타",), "실용음악"),
    ("바이올린", ("기타",), "바이올린"),
    ("첼로", ("기타",), "첼로"),
    ("피아노", ("기타",), "피아노"),
    ("음악", ("기타",), "음악"),
    ("미술", ("기타",), "미술"),
    ("발레", ("기타",), "무용"),
    ("무용", ("기타",), "무용"),
    ("댄스", ("기타",), "댄스"),
    ("바둑", ("기타",), "바둑"),
    ("프로그래밍", ("기타",), "코딩"),
    ("코딩", ("기타",), "코딩"),
    ("컴퓨터", ("기타",), "코딩"),
    ("로봇", ("기타",), "로봇"),
    ("중국어", ("기타",), "중국어"),
    ("일본어", ("기타",), "일본어"),
    ("외국어", ("기타",), "외국어"),
    ("한자", ("기타",), "한자"),
    ("속독", ("기타",), "속독"),
    ("웅변", ("기타",), "스피치"),
    ("화술", ("기타",), "스피치"),
    ("스피치", ("기타",), "스피치"),
    ("태권도", ("기타",), "태권도"),
    ("체육", ("기타",), "체육"),
    ("바리스타", ("기타",), "바리스타"),
    ("요리", ("기타",), "요리"),
    ("예체능", ("기타",), "예체능"),
)

# 긴 키워드가 먼저 소비되도록 길이 내림차순으로 고정한다.
_KEYWORDS_SORTED = tuple(sorted(_KEYWORDS, key=lambda entry: len(entry[0]), reverse=True))

_TAXONOMY_ORDER = {name: index for index, name in enumerate(SUBJECT_TAXONOMY)}


def normalize_subjects(values: Sequence[str]) -> list[str]:
    """중복 제거 후 taxonomy 순으로 정렬. 허용 목록 밖이면 ValueError."""
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
    if unknown:
        raise ValueError(
            "subjects는 "
            + ", ".join(SUBJECT_TAXONOMY)
            + f" 만 허용합니다. 거부: {unknown}"
        )
    return [name for name in SUBJECT_TAXONOMY if name in seen]


def normalize_subject_detail(value: str | None) -> str | None:
    """세부 라벨 정규화. 어휘는 강제하지 않는다(느슨하게 시작). 빈 값은 None."""
    if value is None:
        return None
    text = value.strip()
    return text or None


def extract_subject_hits(text: str) -> list[SubjectHit]:
    """공개 텍스트(카테고리·제목·질문)에서 과목 신호를 버킷+라벨로 뽑는다.

    긴 키워드부터 매치 구간을 소비하므로 부분 문자열 오탐이 구조적으로 막힌다.
    """
    working = text
    hits: list[SubjectHit] = []
    seen: set[tuple[str, str | None]] = set()
    for keyword, buckets, label in _KEYWORDS_SORTED:
        if keyword not in working:
            continue
        working = working.replace(keyword, " ")  # 매치 구간 소비
        for bucket in buckets:
            key = (bucket, label)
            if key in seen:
                continue
            seen.add(key)
            hits.append(SubjectHit(bucket, label))
    # taxonomy 순으로 안정 정렬 (같은 버킷 안 라벨은 발견 순서 유지).
    hits.sort(key=lambda hit: _TAXONOMY_ORDER.get(hit.subject, len(_TAXONOMY_ORDER)))
    return hits


def extract_subjects_from_text(text: str) -> list[str]:
    """공개 텍스트에서 taxonomy 버킷만 뽑는다 (세부 라벨은 버린다)."""
    subjects: list[str] = []
    for hit in extract_subject_hits(text):
        if hit.subject not in subjects:
            subjects.append(hit.subject)
    return subjects


def subjects_csv(values: Iterable[str] | None) -> str:
    if not values:
        return ""
    return "|".join(values)
