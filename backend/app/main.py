from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.academies import router as academies_router
from app.api.engagement import router as engagement_router
from app.api.recommendations import router as recommendations_router
from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import setup_logging

settings = get_settings()

setup_logging()

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(academies_router)
app.include_router(recommendations_router)
app.include_router(engagement_router)
