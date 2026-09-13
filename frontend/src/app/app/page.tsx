import type { Metadata } from "next";
import { AppShell } from "@/components/app/AppShell";

export const metadata: Metadata = {
  title: "확인해 볼 후보와 상담 질문 | 학원콕",
  robots: { index: false, follow: false },
};

export default function AppPage() {
  return <AppShell />;
}
