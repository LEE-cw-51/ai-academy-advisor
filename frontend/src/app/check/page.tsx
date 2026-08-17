import type { Metadata } from "next";
import { MiniAcademyCheck } from "@/components/check/MiniAcademyCheck";
import { LandingFooter } from "@/components/landing/LandingFooter";
import { LandingHeader } from "@/components/landing/LandingHeader";
import { CHECK_INTRO_HEADLINE } from "@/components/landing/landingFacts";

export const metadata: Metadata = {
  title: "1분 학원 점검 | 학원콕",
  description:
    "지금 다니는 아이의 학원을 점검해 보세요. 3가지 질문으로 1분 만에 확인하고, 체크리스트와 출시 소식을 받아 보세요.",
};

export default function CheckPage() {
  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <LandingHeader />
      <main className="mx-auto w-full max-w-lg flex-1 px-4 py-8 sm:px-6 sm:py-12">
        <h1 className="break-keep text-2xl font-black leading-tight text-ink sm:text-3xl">
          {CHECK_INTRO_HEADLINE}
        </h1>
        <p className="mt-2 break-keep text-sm text-ink-muted">
          학원을 좋거나 나쁘다고 나누지 않습니다. 지금 확인할 점만 짧게 짚어
          드려요.
        </p>
        <div className="mt-8">
          <MiniAcademyCheck />
        </div>
      </main>
      <LandingFooter />
    </div>
  );
}
