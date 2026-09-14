import type { NextConfig } from "next";
import path from "path";

// 브라우저는 항상 같은 오리진의 /api/backend/*만 호출한다 — CORS가 필요 없다.
//
// Vercel: 저장소 루트 vercel.json의 Services가 이 경로를 같은 프로젝트의 backend
// 서비스(FastAPI)로 보낸다(docs/decisions/2026-09-14-single-vercel-project-services.md).
// 그 최상위 rewrite가 Next.js보다 먼저 요청을 받으므로 여기서는 프록시가 필요 없다.
// 백엔드가 별도 프로젝트였을 때(2026-09-04~) 쓰던 BACKEND_ORIGIN 필수 가드는 걷어냈다.
//
// 프록시는 BACKEND_ORIGIN이 있을 때만 등록한다. 로컬·CI는 기본 localhost:8000을 쓴다.
// Vercel 배포(Production·Preview)에서 BACKEND_ORIGIN을 남겨 두면 옛 2-프로젝트 구조로도
// 동작한다 — 대시보드 전환 전에 이 코드가 먼저 배포되거나, 전환을 롤백할 때를 위한 것이다.
// `vercel dev`는 VERCEL_ENV=development를 넣는데, 이것까지 배포로 치면 로컬 프록시가
// 사라져 /api/backend/*가 Next 404가 된다 — 그래서 production·preview만 배포로 본다.
// trailing slash는 destination에 `//academies` 같은 이중 슬래시를 만들어 FastAPI
// 라우팅이 매치하지 못하므로 제거한다(frontend/src/lib/api.ts의 NEXT_PUBLIC_API_URL
// 정규화와 동일 규칙).
const vercelEnv = process.env.VERCEL_ENV;
const onVercel = vercelEnv === "production" || vercelEnv === "preview";
const backendOrigin =
  process.env.BACKEND_ORIGIN?.trim() || (onVercel ? "" : "http://localhost:8000");
const BACKEND_ORIGIN = backendOrigin.replace(/\/+$/, "");

const nextConfig: NextConfig = {
  // 저장소 루트에 다른 lockfile(예: 상위 폴더의 package-lock.json)이 있을 때
  // Next.js가 워크스페이스 루트를 잘못 추론하는 경고를 없앤다 — 빌드 동작은
  // 바뀌지 않는다.
  outputFileTracingRoot: path.join(__dirname, ".."),
  async rewrites() {
    if (!BACKEND_ORIGIN) return [];
    return [
      {
        source: "/api/backend/:path*",
        destination: `${BACKEND_ORIGIN}/:path*`,
      },
    ];
  },
  // `/check`(1분 학원 점검)·`/checklists`(상담 전 질문)는 2026-09-14에 퇴역했다 —
  // `/app`이 상황 입력 → 후보 → 상담 질문을 한 흐름으로 맡는다
  // (docs/decisions/2026-09-14-retire-check-and-checklists.md). 카카오 웰컴 메시지·
  // 광고 초안의 옛 링크가 404가 되지 않게 `/app`으로 보낸다. 쿼리(utm)는 Next가
  // 그대로 넘긴다. 307(permanent: false) — 308은 브라우저가 캐시해 되돌리기 어렵다.
  async redirects() {
    return [
      { source: "/check", destination: "/app", permanent: false },
      { source: "/checklists", destination: "/app", permanent: false },
    ];
  },
};

export default nextConfig;
