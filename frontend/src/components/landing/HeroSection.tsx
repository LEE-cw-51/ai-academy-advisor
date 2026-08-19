import type { RefObject } from "react";
import Image from "next/image";
import { Badge, Button } from "@/components/ui";
import { CheckCtaLink } from "./CheckCtaLink";
import {
  HOME_CHECK_CTA_LABEL,
  HOME_CHECK_REASSURANCE,
  MISA_ACADEMY_COUNT,
  WAITLIST_CTA_LABEL,
} from "./landingFacts";

interface HeroSectionProps {
  onRequestWaitlist: () => void;
  /** 히어로 CTA 직후. 화면 위로 나가면 StickyCtaBar가 뜬다. */
  ctaSentinelRef: RefObject<HTMLDivElement | null>;
}

export function HeroSection({ onRequestWaitlist, ctaSentinelRef }: HeroSectionProps) {
  return (
    <section className="hero-wash mx-auto max-w-5xl px-4 pb-10 pt-8 text-center sm:px-6 sm:pt-16">
      <Image
        src="/logo.png"
        alt="학원콕 — 우리 아이에게 맞는 학원을 찾다."
        width={1254}
        height={1254}
        priority
        className="hero-fade-up mx-auto h-16 w-16 sm:h-20 sm:w-20"
      />
      <h1 className="hero-fade-up hero-fade-up-delay-1 mx-auto mt-5 max-w-2xl break-keep text-3xl font-black leading-tight text-ink sm:text-4xl">
        하남 미사 학원 {MISA_ACADEMY_COUNT}곳,
        <br />
        우리 아이에게 맞는 곳부터
      </h1>
      <Badge tone="warn" className="hero-fade-up hero-fade-up-delay-2 mt-4">
        정식 출시 준비 중 · 하남 미사
      </Badge>
      <p className="hero-fade-up hero-fade-up-delay-2 mx-auto mt-4 max-w-md break-keep text-sm text-ink-muted">
        맘카페·블로그를 뒤져도 우리 아이에게 맞는 곳인지는 확신이 서지 않죠.
      </p>
      <div className="hero-fade-up hero-fade-up-delay-3 mt-6 flex flex-col items-center justify-center gap-3">
        <CheckCtaLink className="!px-6 !py-3 text-base">
          {HOME_CHECK_CTA_LABEL}
        </CheckCtaLink>
        <p className="text-xs text-ink-muted">{HOME_CHECK_REASSURANCE}</p>
        <Button
          variant="secondary"
          className="!px-6 !py-3 text-base"
          onClick={onRequestWaitlist}
        >
          {WAITLIST_CTA_LABEL}
        </Button>
      </div>
      <div ref={ctaSentinelRef} className="h-px w-full" aria-hidden />
      <div className="mx-auto mt-8 max-w-md text-left">
        <p className="break-keep border-l-2 border-brand pl-4 text-sm font-semibold text-ink">
          학년·과목·아이 성향에 맞는 곳을, 근거와 함께 추려드릴 준비를 하고 있어요.
        </p>
      </div>
      <p className="mx-auto mt-5 max-w-xl break-keep text-xs text-ink-muted">
        {MISA_ACADEMY_COUNT}곳 = 경기도 공공데이터 기준 미사 지역 등록 학원·교습소
      </p>
    </section>
  );
}
