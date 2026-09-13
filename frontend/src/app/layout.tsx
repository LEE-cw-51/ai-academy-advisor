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
 *  메인이 `/app`(후보·상담 질문 정리) 주 CTA로 시작하게 되며(2026-09-13) 제목은
 *  "선택 가이드"가 아니라 "알아보기"로 맞춘다. 설명은 주 과업과 보조 퍼널을 함께 말한다. */
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
      <body className={`${notoSansKr.variable} font-sans antialiased`}>
        {children}
      </body>
    </html>
  );
}
