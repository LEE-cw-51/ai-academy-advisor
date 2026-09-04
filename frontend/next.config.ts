import type { NextConfig } from "next";

// 백엔드는 별도 Vercel Python Function 프로젝트로 배포된다(Railway 이탈,
// docs/decision-log.md 2026-09-04). 브라우저는 항상 같은 오리진의
// /api/backend/*만 호출하고, Next.js 서버가 서버사이드로 실제 백엔드에
// 프록시한다 — 프로덕션에서 CORS 설정 자체가 필요 없어진다.
// BACKEND_ORIGIN은 NEXT_PUBLIC_이 아닌 서버 전용 env(Vercel 프로젝트 설정에서
// 지정). 로컬 dev는 지정하지 않으면 로컬 백엔드를 그대로 가리킨다.
const BACKEND_ORIGIN = process.env.BACKEND_ORIGIN || "http://localhost:8000";

const nextConfig: NextConfig = {
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
