# 아키텍처

## 개요
MVP 단계에서는 단일 FastAPI 백엔드 + PostgreSQL 구조를 사용하며,
계층형(Layered) 아키텍처로 관심사를 분리한다.

## 계층 구조

```
API (routers)
  ↓
Service (비즈니스 로직)
  ↓
Repository (데이터 접근)
  ↓
DB (SQLAlchemy models / PostgreSQL)
```

- **api/**: HTTP 요청/응답 처리, 입력 검증(schemas 사용), 서비스 호출
- **services/**: 비즈니스 로직. 추후 추천 알고리즘, OpenAI 연동 로직이 위치
- **repositories/**: DB 접근 로직 캡슐화 (Service는 SQLAlchemy를 직접 다루지 않음)
- **models/**: SQLAlchemy ORM 모델
- **schemas/**: Pydantic 요청/응답 모델
- **core/**: 설정(config), 로깅 등 공통 인프라
- **dependencies/**: FastAPI Depends로 주입되는 공용 의존성 (DB 세션, 인증 등)
- **utils/**: 순수 유틸리티 함수

## 향후 AI 기능 확장 고려사항
- `services/` 하위에 `recommendation_service.py`, `ai_service.py` 등을 추가하는 방식으로 확장
- OpenAI 클라이언트는 `core/` 또는 별도 `ai/` 모듈로 분리하여 서비스 계층에서 주입받아 사용
- 프롬프트 템플릿은 `prompts/` 디렉터리에서 관리하여 코드와 분리

## 배포
- Docker Compose로 `backend` + `db(postgres)` 구성
- 환경변수는 `.env` 파일로 관리 (`.env.example` 참고)
