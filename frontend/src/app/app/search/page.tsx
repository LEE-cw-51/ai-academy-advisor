import type { Metadata } from "next";
import { AcademySearchPage } from "@/components/app/AcademySearchPage";

export const metadata: Metadata = {
  title: "이미 알고 있는 학원 찾기 | 학원콕",
  robots: { index: false, follow: false },
};

export default function AppSearchRoutePage() {
  return <AcademySearchPage />;
}
