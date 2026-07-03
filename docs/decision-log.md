# 의사결정 로그

주요 기술적/제품적 의사결정과 그 이유를 기록한다.

## 2026-07-03 — 초기 기술 스택 결정
- **Backend**: FastAPI + SQLAlchemy + Alembic + PostgreSQL + uv + Pydantic Settings
  - 이유: 빠른 개발 속도, 타입 안정성, 향후 AI(OpenAI API) 연동 용이성
- **패키지 관리**: uv 채택
  - 이유: 빠른 의존성 해석/설치, 최신 Python 프로젝트 표준(pyproject.toml) 지원
- **아키텍처**: 계층형(Layered) 구조 (api/service/repository 분리)
  - 이유: MVP 단계에서도 유지보수성과 테스트 용이성 확보, 향후 AI 서비스 계층 추가가 쉬움
- **Frontend/AI**: MVP 단계에서는 구조만 고려하고 실제 구현은 보류
  - 이유: 백엔드 도메인/API 안정화가 우선
