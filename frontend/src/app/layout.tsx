import type { Metadata } from "next";
import { Noto_Sans_KR } from "next/font/google";
import "./globals.css";

const notoSansKr = Noto_Sans_KR({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "900"],
  variable: "--font-noto-sans-kr",
  display: "swap",
});

export const metadata: Metadata = {
  title: "학원콕 | 하남 미사 AI 학원 추천 (정식 출시 준비 중)",
  description:
    "학원콕은 아직 정식 출시 전입니다. 지금은 무료 출시 알림 신청만 받고 있으며, 맞춤 추천·비교·상담 연결은 출시 후 제공될 예정입니다.",
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
