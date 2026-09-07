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
프록시하므로 **CORS 설정이 필요 없다**(2026-09-04, `docs/decision-log.md`). 프록시를
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

1. [Vercel](https://vercel.com)에서 이 GitHub 리포를 Import합니다.
2. **Root Directory**: `frontend`. 백엔드는 별도 Vercel 프로젝트(Root Directory
   `backend`)로 배포한다 — 2026-09-04 Railway 이탈, `docs/decision-log.md`. CLI로
   재배포할 때는 **저장소 루트**에서 실행한다(`frontend/`만 올리면 Root
   Directory 설정과 어긋나 실패한다).
3. Framework: **Next.js** (자동 감지)
4. **Environment Variables** (Production **및 Preview**):

| 변수 | 예시 |
|------|------|
| `BACKEND_ORIGIN` | `https://ai-academy-advisor-backend.vercel.app` (백엔드 프로젝트 프로덕션 URL; Preview에도 동일 값 허용) |
| `NEXT_PUBLIC_NAVER_MAP_CLIENT_ID` | (선택) 네이버 지도 클라이언트 ID |

`VERCEL_ENV`가 `production` 또는 `preview`이면 `BACKEND_ORIGIN`이 필수다
(`next.config.ts`가 없으면 빌드를 실패시킨다). CI·로컬은 `VERCEL_ENV`가 없어
기본 `http://localhost:8000`을 쓴다.

`NEXT_PUBLIC_API_URL`은 프록시를 우회해 백엔드를 직접 호출할 때만 설정한다(기본은
비워 두어 `/api/backend` same-origin 프록시를 쓴다).

Production URL (2026-09-07 컷오버): `https://ai-academy-advisor-ten.vercel.app`

`BACKEND_ORIGIN`은 `next.config.ts`의 `rewrites()`에서 **빌드 시점**에 값이 고정된다
— 값을 바꾸면 재배포해야 반영된다. `NEXT_PUBLIC_*` 변수도 마찬가지로 빌드 시 번들에
포함되므로 변경 후 Vercel에서 재배포가 필요하다.
