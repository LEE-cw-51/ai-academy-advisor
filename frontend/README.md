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
| `NEXT_PUBLIC_API_URL` | 백엔드 base URL (trailing slash 없음) |
| `NEXT_PUBLIC_NAVER_MAP_CLIENT_ID` | 네이버 지도 JS API 키 (없으면 지도 플레이스홀더) |

백엔드 `CORS_ORIGINS`에 프론트 오리진(`http://localhost:3000`, Vercel Production URL 등)이
포함돼 있어야 합니다. 값은 **JSON 배열** 형식입니다.

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
2. **Root Directory**: `frontend`
3. Framework: **Next.js** (자동 감지)
4. **Environment Variables** (Production):

| 변수 | 예시 |
|------|------|
| `NEXT_PUBLIC_API_URL` | `https://ai-academy-advisor-production.up.railway.app` |
| `NEXT_PUBLIC_NAVER_MAP_CLIENT_ID` | (선택) 네이버 지도 클라이언트 ID |

Production URL (Hobby 팀, 2026-09-02): `https://ai-academy-advisor.vercel.app`

5. 배포 후 Railway `CORS_ORIGINS`에 Vercel Production URL을 JSON 배열로 추가합니다.

```bash
echo '["https://your-project.vercel.app","http://localhost:3000"]' | railway variable set CORS_ORIGINS --stdin
```

`NEXT_PUBLIC_*` 변수는 **빌드 시** 번들에 포함됩니다. 변경 후 Vercel에서 재배포가 필요합니다.
