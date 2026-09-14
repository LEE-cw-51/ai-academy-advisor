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
| `BACKEND_ORIGIN` | (로컬 전용, 서버 전용 — `NEXT_PUBLIC_` 아님) `next dev`가 `/api/backend/*`를 프록시할 백엔드 URL. 기본 `http://localhost:8000`. Vercel에는 두지 않는다 |
| `NEXT_PUBLIC_API_URL` | 프록시를 우회해 백엔드를 직접 호출할 때만 설정 (기본은 `/api/backend` — same-origin) |
| `NEXT_PUBLIC_NAVER_MAP_CLIENT_ID` | 네이버 지도 JS API 키 (없으면 지도 플레이스홀더) |

브라우저는 항상 같은 오리진(`/api/backend/*`)만 호출하므로 **CORS 설정이 필요 없다**.
로컬에서는 `next.config.ts`의 `rewrites()`가 이 경로를 `BACKEND_ORIGIN`으로 프록시하고,
Vercel에서는 저장소 루트 `vercel.json`의 Services가 같은 프로젝트의 backend 서비스로 보낸다
(2026-09-14, `docs/decisions/2026-09-14-single-vercel-project-services.md`). 프록시를
우회해 `NEXT_PUBLIC_API_URL`로 백엔드를 직접 호출하는 경우에만 백엔드 `CORS_ORIGINS`가
다시 load-bearing이 된다 — 그 오리진을 JSON 배열로 추가해야 한다.

## 실행

```bash
npm install
npm run dev
```

- 개발: http://localhost:3000
- 프로덕션 빌드: `npm run build && npm start`
- 린트: `npm run lint`

## Vercel 배포

프론트는 백엔드와 같은 Vercel 프로젝트의 `frontend` 서비스로 배포된다 — 프로젝트 설정·
환경변수·전환 순서는 루트 [README.md](../README.md)의 배포 절과
`docs/decisions/2026-09-14-single-vercel-project-services.md`가 정본이다.

- 프로젝트 Framework Preset은 `Services`, Root Directory는 저장소 루트다. CLI도 저장소
  루트에서 실행한다.
- 프론트가 쓰는 변수는 `NEXT_PUBLIC_NAVER_MAP_CLIENT_ID`(선택) 하나다. `BACKEND_ORIGIN`은
  Vercel에 두지 않는다 — 두면 옛 2-프로젝트 방식으로 프록시한다(전환 롤백용).
- `NEXT_PUBLIC_API_URL`은 프록시를 우회해 백엔드를 직접 호출할 때만 설정한다(기본은
  비워 두어 `/api/backend` same-origin을 쓴다).
- `NEXT_PUBLIC_*` 변수는 빌드 시 번들에 포함되므로 값을 바꾸면 Vercel에서 재배포해야 한다.

Production URL (2026-09-07 컷오버): `https://ai-academy-advisor-ten.vercel.app`
