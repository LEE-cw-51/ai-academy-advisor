from sqlalchemy.orm import Session

from app.models.academy import Academy
from app.repositories import academy_repository
from app.schemas.academy import AcademyListParams


def list_academies(db: Session, params: AcademyListParams) -> tuple[list[Academy], int]:
    return academy_repository.list_academies(db, params)


def get_academy(db: Session, academy_id: int) -> Academy | None:
    return academy_repository.get_by_id(db, academy_id)
