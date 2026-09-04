# 학원콕 프론트엔드

하남 미사 학원 AI 추천 UI (Next.js 15 App Router). 조건 선택 → `POST /recommendations/ai` →
지도·목록에 결과 표시.

## 사전 조건

백엔드 API가 떠 있어야 합니다 (기본 `http://localhost:8000`).

```bash
cd backend
uv run uvicorn app.main:app --reload
```

## 설정

```bash
cp .env.local.example .env.local
```

| 변수 | 설명 |
|------|------|
| `BACKEND_ORIGIN` | (서버 전용, `NEXT_PUBLIC_` 아님) `next.config.ts`의 `rewrites()`가 `/api/backend/*`를 프록시할 실제 백엔드 URL. 기본 `http://localhost:8000` |
| `NEXT_PUBLIC_API_URL` | 프록시를 우회해 백엔드를 직접 호출할 때만 설정 (기본은 `/api/backend` — same-origin) |
| `NEXT_PUBLIC_NAVER_MAP_CLIENT_ID` | 네이버 지도 JS API 키 (없으면 지도 플레이스홀더) |

브라우저는 항상 같은 오리진(`/api/backend/*`)만 호출하고 Next.js 서버가 실제 백엔드로
프록시하므로 **CORS 설정이 필요 없다**(2026-09-04, `docs/decision-log.md`).

## 실행

```bash
npm install
npm run dev
```

- 개발: http://localhost:3000
- 프로덕션 빌드: `npm run build && npm start`
- 린트: `npm run lint`
