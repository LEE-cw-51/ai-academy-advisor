"""비식별 집계 수요 리포트 — search_history·click_logs 를 넓은 단위로만 센다.

Phase 5c 2개월차 원장 리포트 **시안**의 재료다 (docs/roadmap.md, docs/data-strategy.md
"사업 검증용 집계 원칙", docs/decisions/2026-09-19-round1-engineering-scope.md). 판매 상품이
아니고, 개별 학부모·아동·학원을 역추론할 수 없어야 한다. 그래서:

- ORM·세션을 받지 않는다. 입력은 `SearchRow`/`ClickRow` 값 객체뿐이다 (테스트로 강제).
- 원문 질의는 어떤 출력에도 넣지 않는다. 기존 의도 파서(`intent.parse_intent`)와 과목
  추출(`scoring.extract_subjects`)로 학년군·과목·지역·커리큘럼 **버킷만** 뽑는다.
- 검색 표본이 `min_total` 미만이면 리포트를 만들지 않는다(`InsufficientSample`).
  셀이 `min_cell` 미만이면 값을 `<N` 으로 가린다. 초기 시안용 단순 억제라, 가려진 셀이
  하나뿐이면 합계에서 역산될 수 있다 — 표본이 커지면 억제 규칙을 다시 본다.
- 학원별 행은 `by_academy=True` 일 때만, 그것도 `min_cell` 이상인 학원만 id 로 낸다
  (roadmap: 학원별 소표본 리포트는 보류).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Sequence

from app.services import intent, scoring

DEFAULT_MIN_CELL = 5
DEFAULT_MIN_TOTAL = 20
UNSPECIFIED = "구분 없음"

_LEVEL_LABELS = {"elementary": "초등", "middle": "중등", "high": "고등"}
_CURRICULUM_LABELS = {"seonhaeng": "선행", "naesin": "내신", "suneung": "수능"}
# app.core.constants.ClickEvent 의 현행 값. 퇴역 이벤트(옛 click_logs 행)는 한 버킷으로 묶는다.
_EVENT_LABELS = {
    "phone": "전화",
    "website": "웹사이트",
    "directions": "길찾기",
    "detail": "상세 보기",
    "kakao_channel": "카카오 채널 추가",
}
_RETIRED_EVENT_LABEL = "기타(퇴역 이벤트)"

DIMENSION_ORDER = ("학년군", "과목", "지역", "커리큘럼")


@dataclass(frozen=True)
class SearchRow:
    created_at: datetime
    query: str


@dataclass(frozen=True)
class ClickRow:
    created_at: datetime
    event: str
    academy_id: int | None


class InsufficientSample(Exception):
    """검색 표본이 최소 기준에 못 미쳐 리포트를 만들지 않는다."""

    def __init__(self, total: int, min_total: int) -> None:
        super().__init__(f"표본 부족: 검색 {total}건 < 최소 {min_total}건")
        self.total = total
        self.min_total = min_total


@dataclass
class DemandReport:
    since: datetime
    until: datetime
    generated_at: datetime
    min_cell: int
    total_searches: int
    total_clicks: int
    # 차원 이름 → (버킷 라벨 → 원시 건수). 억제는 렌더링에서 한다 — 집계 자체는 검증용으로 남긴다.
    dimensions: dict[str, Counter[str]] = field(default_factory=dict)
    clicks_by_event: Counter[str] = field(default_factory=Counter)
    # by_academy 일 때만. 이미 min_cell 미만은 걸러져 있다.
    clicks_by_academy: dict[int, int] | None = None


def _search_dimensions(query: str) -> dict[str, list[str]]:
    """질의 한 건을 버킷 라벨로만 바꾼다. 원문은 여기서 끝난다."""
    req = intent.parse_intent(query, limit=1)
    level = _LEVEL_LABELS.get(req.level.value, UNSPECIFIED) if req.level else UNSPECIFIED
    curriculum = (
        _CURRICULUM_LABELS.get(req.curriculum.value, UNSPECIFIED)
        if req.curriculum
        else UNSPECIFIED
    )
    region = req.region or UNSPECIFIED
    subjects = scoring.extract_subjects(query) or [UNSPECIFIED]
    return {
        "학년군": [level],
        "과목": subjects,
        "지역": [region],
        "커리큘럼": [curriculum],
    }


def build_report(
    searches: Sequence[SearchRow],
    clicks: Sequence[ClickRow],
    *,
    since: datetime,
    until: datetime,
    min_cell: int = DEFAULT_MIN_CELL,
    min_total: int = DEFAULT_MIN_TOTAL,
    by_academy: bool = False,
    now: datetime | None = None,
) -> DemandReport:
    total = len(searches)
    if total < min_total:
        raise InsufficientSample(total, min_total)

    dimensions: dict[str, Counter[str]] = {name: Counter() for name in DIMENSION_ORDER}
    for row in searches:
        for name, values in _search_dimensions(row.query).items():
            dimensions[name].update(values)

    clicks_by_event: Counter[str] = Counter(
        _EVENT_LABELS.get(click.event, _RETIRED_EVENT_LABEL) for click in clicks
    )

    clicks_by_academy: dict[int, int] | None = None
    if by_academy:
        raw = Counter(
            click.academy_id for click in clicks if click.academy_id is not None
        )
        clicks_by_academy = {
            academy_id: count for academy_id, count in raw.items() if count >= min_cell
        }

    return DemandReport(
        since=since,
        until=until,
        generated_at=now or datetime.now(timezone.utc),
        min_cell=min_cell,
        total_searches=total,
        total_clicks=len(clicks),
        dimensions=dimensions,
        clicks_by_event=clicks_by_event,
        clicks_by_academy=clicks_by_academy,
    )


def _cell(count: int, min_cell: int) -> str:
    return str(count) if count >= min_cell else f"<{min_cell}"


def _table(
    title: str, counter: Counter[str], min_cell: int, value_header: str
) -> list[str]:
    lines = [f"### {title}", "", f"| 값 | {value_header} |", "|---|---:|"]
    for label, count in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"| {label} | {_cell(count, min_cell)} |")
    lines.append("")
    return lines


def render_markdown(report: DemandReport) -> str:
    day = "%Y-%m-%d"
    lines = [
        "# 비식별 집계 수요 리포트 (시안)",
        "",
        f"- 기간: {report.since.strftime(day)} ~ {report.until.strftime(day)} (끝 날짜 미포함)",
        f"- 생성: {report.generated_at.strftime('%Y-%m-%d %H:%M')} UTC",
        f"- 표본: 검색 {report.total_searches}건, 외부 행동 {report.total_clicks}건",
        f"- 억제: {report.min_cell}건 미만인 셀은 `<{report.min_cell}`로 표시",
        "",
        "> 지역·학년군·과목·커리큘럼 버킷과 행동 유형만 센 비식별 집계다. 입력 원문·학교명·자녀",
        "> 정보는 포함하지 않는다. 판매 상품이 아니라 수요 검증 자료이며, 학원의 지불 여부가 후보",
        '> 순서·AI 근거에 영향을 주지 않는다 (docs/data-strategy.md "사업 검증용 집계 원칙").',
        "",
        "## 검색(상황 입력) 분포",
        "",
    ]
    for name in DIMENSION_ORDER:
        lines += _table(
            name, report.dimensions.get(name, Counter()), report.min_cell, "검색 수"
        )
    lines += ["## 외부 행동", ""]
    lines += _table("행동 유형", report.clicks_by_event, report.min_cell, "행동 수")
    if report.clicks_by_academy is not None:
        lines += [
            f"### 학원별 외부 행동 ({report.min_cell}건 이상인 학원만, id)",
            "",
            "| 학원 id | 행동 수 |",
            "|---:|---:|",
        ]
        for academy_id, count in sorted(
            report.clicks_by_academy.items(), key=lambda kv: (-kv[1], kv[0])
        ):
            lines.append(f"| {academy_id} | {count} |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
