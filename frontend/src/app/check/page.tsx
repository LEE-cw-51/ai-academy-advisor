import type { Metadata } from "next";
import { MiniAcademyCheck } from "@/components/check/MiniAcademyCheck";
import { LandingFooter } from "@/components/landing/LandingFooter";
import { LandingHeader } from "@/components/landing/LandingHeader";
import {
  CHECK_INTRO_HEADLINE,
  CHECK_INTRO_HEADLINE_LINE2,
} from "@/components/landing/landingFacts";

export const metadata: Metadata = {
  title: "1분 학원 점검 | 학원콕",
  description: `${CHECK_INTRO_HEADLINE} ${CHECK_INTRO_HEADLINE_LINE2} 3가지 질문으로 확인하고, 체크리스트와 출시 소식을 받아 보세요.`,
};

export default function CheckPage() {
  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <LandingHeader />
      <main className="mx-auto w-full max-w-lg flex-1 px-4 py-8 sm:px-6 sm:py-12">
        <MiniAcademyCheck />
      </main>
      <LandingFooter />
    </div>
  );
}
