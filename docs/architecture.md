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
- **providers/**: AI provider 포트+어댑터 (교체 가능성의 핵심, 아래 참고)

## providers/ — 포트 + 어댑터 (교체 가능성)

AI 구성요소(LLM·임베딩·벡터 스토어)는 벤더/모델 교체가 잦으므로 구체 구현이 아니라
**포트(Protocol)** 에만 의존한다.

- **base.py**: `EmbeddingProvider` / `LLMProvider` / `VectorStore` Protocol (서비스와의 계약)
- **stub.py**: 결정적 기본 구현 (실제 호출·키 없이 동작, 테스트/개발용)
- **factory.py**: config(`llm_provider`/`embedding_provider`/`vector_store`)로 구현 선택,
  `@lru_cache`. 새 어댑터(openai/bge-m3/pgvector)는 이 파일과 config만 수정해 교체한다.

서비스 계층은 `factory.get_*()`로 포트를 주입받아 사용한다.

## 향후 AI 기능 확장 고려사항
- `services/` 하위에 `recommendation_service.py`(존재), `ai_service.py` 등을 추가하며 확장
- 실제 RAG(Phase 4b)는 **LlamaIndex 기반 `RagEngine`을 하나의 포트로 감싸** providers/에 추가 —
  엔진 자체도 교체 가능하게 유지. 실제 어댑터도 같은 포트 뒤에 붙인다.
- 프롬프트 템플릿은 `prompts/` 디렉터리에서 관리하여 코드와 분리

## 배포
- Docker Compose로 `backend` + `db(postgres)` 구성
- 환경변수는 `.env` 파일로 관리 (`.env.example` 참고)
