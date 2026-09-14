"""배포 구성(Vercel 프로젝트 하나 · Services)이 어긋나지 않는지 검사한다.

2026-09-14: 프론트·백엔드를 Vercel 프로젝트 하나에 Services로 배포한다
(docs/decisions/2026-09-14-single-vercel-project-services.md). pytest도 `npm run build`도
루트 vercel.json을 읽지 않으므로, 라우팅 순서나 경로 변환이 깨져도 CI는 초록이다 —
배포되고 나서야 `/app`의 모든 API 호출이 404로 드러난다. 그 계약을 여기서 지킨다.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VERCEL_JSON = REPO_ROOT / "vercel.json"
BACKEND_VERCEL_JSON = REPO_ROOT / "backend" / "vercel.json"
PYPROJECT = REPO_ROOT / "backend" / "pyproject.toml"
NEXT_CONFIG = REPO_ROOT / "frontend" / "next.config.ts"
API_TS = REPO_ROOT / "frontend" / "src" / "lib" / "api.ts"


def _config() -> dict:
    return json.loads(VERCEL_JSON.read_text(encoding="utf-8"))


def test_root_vercel_json_defines_frontend_and_backend_services():
    services = _config()["services"]
    assert set(services) == {"frontend", "backend"}
    assert services["frontend"]["root"] == "frontend/"
    assert services["backend"]["root"] == "backend/"


def test_backend_service_entrypoint_matches_pyproject():
    backend = _config()["services"]["backend"]
    assert backend["entrypoint"] == "app.main:app"
    assert 'entrypoint = "app.main:app"' in PYPROJECT.read_text(encoding="utf-8")


def test_backend_function_budget_stays_at_30_seconds():
    """ai_recommendation_service의 28s 요청 deadline이 이 하드캡을 전제로 한다."""
    config = _config()
    function = config["services"]["backend"]["functions"]["app/main.py"]
    assert function["maxDuration"] == 30
    assert "alembic/versions/**" in function["excludeFiles"]
    # Services 모드에서는 functions가 최상위에 올 수 없고, 옛 백엔드 전용 설정도 없어야 한다.
    assert "functions" not in config
    assert not BACKEND_VERCEL_JSON.exists()


def test_backend_route_is_matched_before_the_frontend_catch_all():
    """최상위 rewrite는 순서대로 평가되고 서비스로 들어가면 되돌아오지 않는다 —
    catch-all이 앞에 오면 /api/backend/* 가 Next.js로 가서 404가 된다."""
    rewrites = [
        (rule["source"], rule["destination"]["service"]) for rule in _config()["rewrites"]
    ]
    assert rewrites == [("/api/backend/(.*)", "backend"), ("/(.*)", "frontend")]


def test_backend_service_strips_the_public_prefix():
    """서비스는 원래 경로를 받는다 — 앞부분을 떼지 않으면 FastAPI가
    /api/backend/academies 라우트를 찾다 404를 낸다."""
    routes = _config()["services"]["backend"]["routes"]
    assert routes == [
        {
            "src": "/api/backend/(.*)",
            "transforms": [{"type": "request.path", "op": "set", "args": "/$1"}],
        }
    ]


def test_browser_calls_the_prefix_the_services_route_owns():
    api = API_TS.read_text(encoding="utf-8")
    assert 'const DEFAULT_API_URL = "/api/backend";' in api


def test_next_config_proxies_only_when_a_backend_origin_exists():
    """Vercel에서는 Services가 /api/backend/*를 받으므로 BACKEND_ORIGIN 필수 가드가 없다.
    로컬은 localhost:8000으로 프록시하고, Vercel에 BACKEND_ORIGIN을 남기면 옛 2-프로젝트
    방식으로도 동작한다(전환 전 배포·롤백용)."""
    config = NEXT_CONFIG.read_text(encoding="utf-8")
    assert "throw new Error" not in config
    assert 'source: "/api/backend/:path*"' in config
    assert "if (!BACKEND_ORIGIN) return [];" in config
    assert '(onVercel ? "" : "http://localhost:8000")' in config
    # `vercel dev`의 VERCEL_ENV=development는 배포가 아니다 — 로컬 프록시를 지운 적이 있다.
    assert 'const onVercel = vercelEnv === "production" || vercelEnv === "preview";' in config
