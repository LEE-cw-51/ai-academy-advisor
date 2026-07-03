from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()


@router.get("/")
def read_root() -> dict:
    settings = get_settings()
    return {"message": f"{settings.app_name} API is running"}


@router.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@router.get("/version")
def get_version() -> dict:
    settings = get_settings()
    return {"version": settings.app_version}
