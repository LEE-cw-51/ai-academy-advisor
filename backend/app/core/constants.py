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
    """클릭·랜딩 퍼널 이벤트.

    전화/홈페이지 등은 학원 상세의 외부 행동이고, mini_check_* /
    home_check_clicked / home_explore_selected / explore_check_clicked /
    check_explore_clicked / checklist_kakao_clicked 는 랜딩·점검 퍼널이다.
    페이지뷰는 넣지 않는다.

    2026-08-19 공개 퍼널을 3페이지 상황 분기(`/`·`/checklists`·`/check`)로 재구성하며
    home_stage_* 3종(홈 3시점 카드)을 걷어내고 대신 두 상황·페이지 간 이동을 기록한다:
    home_explore_selected(홈 → 알아보는 중), explore_check_clicked(알아보는 중 → 점검),
    check_explore_clicked(점검 결과 → 알아보는 중). home_check_clicked는
    "다니는 중" 카드가 그대로 이어받아 지표 연속성을 지킨다.
    """

    PHONE = "phone"  # 전화 클릭
    WEBSITE = "website"  # 홈페이지 클릭
    DIRECTIONS = "directions"  # 길찾기 클릭
    DETAIL = "detail"  # 상세보기 클릭
    KAKAO_CHANNEL = "kakao_channel"  # 카카오 채널 추가 클릭 (유기 유입)
    MINI_CHECK_STARTED = "mini_check_started"
    MINI_CHECK_COMPLETED = "mini_check_completed"
    MINI_CHECK_RESULT_VIEWED = "mini_check_result_viewed"
    MINI_CHECK_HOME_CLICKED = "mini_check_home_clicked"
    HOME_CHECK_CLICKED = "home_check_clicked"  # 홈 '다니는 중' 카드 → /check
    CHECKLIST_KAKAO_CLICKED = "checklist_kakao_clicked"
    HOME_EXPLORE_SELECTED = "home_explore_selected"  # 홈 '알아보는 중' 카드 → /checklists
    EXPLORE_CHECK_CLICKED = "explore_check_clicked"  # /checklists → /check
    CHECK_EXPLORE_CLICKED = "check_explore_clicked"  # /check 결과 → /checklists
