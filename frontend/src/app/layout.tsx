import type { Metadata } from "next";
import { Noto_Sans_KR } from "next/font/google";
import "./globals.css";
import { META_DESCRIPTION } from "@/components/landing/landingFacts";

const notoSansKr = Noto_Sans_KR({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "900"],
  variable: "--font-noto-sans-kr",
  display: "swap",
});

/** `/` 전용 기본값. `/check`·`/checklists`·`/privacy`는 각 page.tsx가 덮어쓴다.
 *  메인이 상황 분기 페이지가 되며(2026-08-19) 검색·공유 미리보기도 특정 도구 하나가
 *  아니라 두 상황을 함께 말한다. */
export const metadata: Metadata = {
  title: "하남 미사 학원 선택 가이드 | 학원콕",
  description: META_DESCRIPTION,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body className={`${notoSansKr.variable} font-sans antialiased`}>
        {children}
      </body>
    </html>
  );
}
