import type { Metadata } from "next";
import "./globals.css";
import { META_DESCRIPTION } from "@/components/landing/landingFacts";

/** `/` 전용 기본값. `/privacy`처럼 자체 metadata가 있는 page.tsx가 덮어쓴다.
 *  메인이 `/app`(후보·상담 질문 정리) 주 CTA로 시작하게 되며(2026-09-13) 제목은
 *  "선택 가이드"가 아니라 "알아보기"로 맞춘다. 설명은 `/app`이 받는 두 상황(알아보는 중·
 *  다니는 중)을 함께 말한다 — 보조 퍼널(`/check`·`/checklists`)은 2026-09-14에 퇴역했다.
 *  글꼴은 Pretendard(CDN). Noto Sans KR은 2026-09-25 시각 언어에서 교체했다. */
export const metadata: Metadata = {
  title: "하남 미사 학원 알아보기 | 학원콕",
  description: META_DESCRIPTION,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <head>
        <link
          rel="stylesheet"
          href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css"
        />
      </head>
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
