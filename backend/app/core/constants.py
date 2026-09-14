from enum import StrEnum


class SchoolLevel(StrEnum):
    """대상 학교급 (초/중/고)."""

    ELEMENTARY = "elementary"  # 초등부
    MIDDLE = "middle"  # 중등부
    HIGH = "high"  # 고등부


class ClassType(StrEnum):
    """수업 형태 (소수정예/그룹수업/1:1)."""

    SMALL_GROUP = "small_group"  # 소수정예
    GROUP = "group"  # 그룹수업
    ONE_ON_ONE = "one_on_one"  # 1:1


class CurriculumType(StrEnum):
    """커리큘럼 (선행/내신/수능)."""

    SEONHAENG = "seonhaeng"  # 선행
    NAESIN = "naesin"  # 내신
    SUNEUNG = "suneung"  # 수능


class ClickEvent(StrEnum):
    """클릭 이벤트.

    전화/홈페이지/길찾기/상세는 학원 후보의 외부 행동이고, kakao_channel은 카카오 채널
    추가 클릭이다. 페이지뷰는 넣지 않는다.

    2026-09-14 `/check`·`/checklists` 퇴역(`/app`으로 리다이렉트)과 함께 두 페이지와
    홈 상황 카드 전용 퍼널 이벤트 9종(mini_check_* 4종, home_check_clicked,
    checklist_kakao_clicked, home_explore_selected, explore_check_clicked,
    check_explore_clicked)을 걷어냈다. click_logs.event는 enum이 아닌 문자열 컬럼이라
    과거 행은 그대로 남는다 — 이 enum은 새 요청 검증에만 쓴다.
    (docs/decisions/2026-09-14-retire-check-and-checklists.md)
    """

    PHONE = "phone"  # 전화 클릭
    WEBSITE = "website"  # 홈페이지 클릭
    DIRECTIONS = "directions"  # 길찾기 클릭
    DETAIL = "detail"  # 상세보기 클릭
    KAKAO_CHANNEL = "kakao_channel"  # 카카오 채널 추가 클릭
