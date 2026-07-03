# API 문서

## 현재 구현된 엔드포인트

### GET /
서비스 상태 메시지를 반환한다.

```json
{ "message": "AI Academy Advisor API is running" }
```

### GET /health
헬스체크 엔드포인트.

```json
{ "status": "ok" }
```

### GET /version
현재 API 버전을 반환한다.

```json
{ "version": "0.1.0" }
```

## 향후 추가 예정 엔드포인트
- `GET /academies` — 학원 목록 조회
- `GET /academies/{id}` — 학원 상세 조회
- `POST /recommendations` — 조건 기반 학원 추천
