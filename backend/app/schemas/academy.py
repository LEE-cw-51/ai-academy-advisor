from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.constants import ClassType, CurriculumType, SchoolLevel

_STRING_FIELDS = (
    "registration_number",
    "name",
    "address",
    "phone",
    "website_url",
    "blog_url",
    "instagram_url",
    "operating_hours",
    "tagline",
    "source_note",
)


class AcademyRecord(BaseModel):
    """정본 데이터 파일(data/academies/*.json) 1건의 스키마.

    키는 DB 컬럼과 1:1로 대응한다. null = 미확인, false = 확인됨-없음.
    """

    model_config = ConfigDict(extra="forbid")

    registration_number: str | None = Field(default=None, max_length=50)
    name: str = Field(min_length=1, max_length=100)
    address: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=20)
    website_url: str | None = Field(default=None, max_length=300)
    blog_url: str | None = Field(default=None, max_length=300)
    instagram_url: str | None = Field(default=None, max_length=300)
    subjects: list[str] | None = None
    level_elementary: bool | None = None
    level_middle: bool | None = None
    level_high: bool | None = None
    class_small_group: bool | None = None
    class_group: bool | None = None
    class_one_on_one: bool | None = None
    curriculum_seonhaeng: bool | None = None
    curriculum_naesin: bool | None = None
    curriculum_suneung: bool | None = None
    shuttle_available: bool | None = None
    operating_hours: str | None = None
    established_year: int | None = Field(default=None, ge=1950, le=2100)
    teacher_count: int | None = Field(default=None, ge=0)
    classroom_count: int | None = Field(default=None, ge=0)
    tagline: str | None = Field(default=None, max_length=200)
    latitude: float | None = None
    longitude: float | None = None
    source_note: str | None = None
    last_verified_at: date | None = None

    @field_validator(*_STRING_FIELDS, mode="before")
    @classmethod
    def _strip_and_nullify_empty(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        return value

    @field_validator("subjects")
    @classmethod
    def _clean_subjects(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned = [item.strip() for item in value]
        if any(item == "" for item in cleaned):
            raise ValueError("subjects에 빈 문자열이 있습니다")
        return cleaned


class AcademySummary(BaseModel):
    """목록 응답용 요약 (필터 판단에 필요한 사실 + 신뢰 신호 포함)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: str | None
    phone: str | None
    tagline: str | None
    subjects: list[str] | None
    level_elementary: bool | None
    level_middle: bool | None
    level_high: bool | None
    class_small_group: bool | None
    class_group: bool | None
    class_one_on_one: bool | None
    curriculum_seonhaeng: bool | None
    curriculum_naesin: bool | None
    curriculum_suneung: bool | None
    shuttle_available: bool | None
    last_verified_at: date | None


class AcademyDetail(AcademySummary):
    registration_number: str | None
    website_url: str | None
    blog_url: str | None
    instagram_url: str | None
    operating_hours: str | None
    established_year: int | None
    teacher_count: int | None
    classroom_count: int | None
    latitude: float | None
    longitude: float | None
    source_note: str | None


class AcademyListResponse(BaseModel):
    items: list[AcademySummary]
    total: int
    limit: int
    offset: int


class AcademyListParams(BaseModel):
    """GET /academies 쿼리 파라미터."""

    level: SchoolLevel | None = None
    class_type: ClassType | None = None
    curriculum: CurriculumType | None = None
    shuttle: bool | None = None
    q: str | None = Field(default=None, min_length=1, max_length=100)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
