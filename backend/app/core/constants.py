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


SUBJECT_MATH = "수학"
