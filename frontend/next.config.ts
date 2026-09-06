import type { NextConfig } from "next";
import path from "path";

// 백엔드는 별도 Vercel Python Function 프로젝트로 배포된다(Railway 이탈,
// docs/decision-log.md 2026-09-04). 브라우저는 항상 같은 오리진의
// /api/backend/*만 호출하고, Next.js 서버가 서버사이드로 실제 백엔드에
// 프록시한다 — 프로덕션에서 CORS 설정 자체가 필요 없어진다.
// BACKEND_ORIGIN은 NEXT_PUBLIC_이 아닌 서버 전용 env(Vercel 프로젝트 설정에서
// 지정). 로컬 dev는 지정하지 않으면 로컬 백엔드를 그대로 가리킨다.
//
// 프로덕션 빌드(`VERCEL_ENV=production`)에서 BACKEND_ORIGIN이 비어 있으면 이
// rewrites가 조용히 localhost:8000으로 떨어져 배포된 앱의 모든 API 호출이
// 깨진다 — 빌드 자체를 실패시켜 배포 시점에 바로 드러나게 한다. trailing
// slash는 destination에 `//academies` 같은 이중 슬래시를 만들어 FastAPI
// 라우팅이 매치하지 못하므로 여기서 제거한다(frontend/src/lib/api.ts의
// NEXT_PUBLIC_API_URL 정규화와 동일 규칙).
if (process.env.VERCEL_ENV === "production" && !process.env.BACKEND_ORIGIN) {
  throw new Error(
    "BACKEND_ORIGIN이 설정되지 않았습니다 — 프로덕션 빌드는 실제 백엔드 오리진이 " +
      "필요합니다 (Vercel 프로젝트 설정 > Environment Variables).",
  );
}
const BACKEND_ORIGIN = (process.env.BACKEND_ORIGIN || "http://localhost:8000").replace(
  /\/+$/,
  "",
);

const nextConfig: NextConfig = {
  // 저장소 루트에 다른 lockfile(예: 상위 폴더의 package-lock.json)이 있을 때
  // Next.js가 워크스페이스 루트를 잘못 추론하는 경고를 없앤다 — 빌드 동작은
  // 바뀌지 않는다.
  outputFileTracingRoot: path.join(__dirname, ".."),
  async rewrites() {
    return [
      {
        source: "/api/backend/:path*",
        destination: `${BACKEND_ORIGIN}/:path*`,
      },
    ];
  },
};

export default nextConfig;
