from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.academies import router as academies_router
from app.api.consultation import router as consultation_router
from app.api.engagement import router as engagement_router
from app.api.recommendations import router as recommendations_router
from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import setup_logging

settings = get_settings()

setup_logging()

# 브라우저는 같은 오리진의 /api/backend/*로 호출한다. Vercel Services(루트 vercel.json)는
# 이 접두사를 붙인 원래 경로를 그대로 넘긴다 — 서비스 routes의 request.path 변환은
# 2026-09-15 시험 배포에서 적용되지 않았다. 그래서 root_path로 접두사를 떼고 라우팅한다.
# Starlette는 root_path로 시작하지 않는 경로를 그대로 매칭하므로, 접두사 없는 요청
# (로컬 uvicorn·next dev 프록시·옛 백엔드 프로젝트·테스트)도 계속 동작한다.
PUBLIC_PATH_PREFIX = "/api/backend"

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    root_path=PUBLIC_PATH_PREFIX,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    # 쿠키/인증 헤더를 쓰지 않으므로 False. True로 두면 allow_origins=["*"] 조합을
    # 브라우저가 거부하고, 자격증명 요청 자체가 필요 없다.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(academies_router)
app.include_router(recommendations_router)
app.include_router(engagement_router)
app.include_router(consultation_router)
