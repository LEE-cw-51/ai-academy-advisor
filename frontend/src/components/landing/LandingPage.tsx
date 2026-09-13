import { ButtonLink } from "@/components/ui";
import { TRUST_NOTE } from "@/components/app/exploreCopy";
import { GroundworkSection } from "./GroundworkSection";
import { PageHero } from "./PageHero";
import { SiteChrome } from "./SiteChrome";
import { SituationSection } from "./SituationSection";
import {
  HERO_BADGE,
  HERO_REASSURANCE,
  HOME_CTA_HREF,
  HOME_CTA_LABEL,
  HOME_HEADLINE,
  HOME_HEADLINE_MOBILE_LINES,
  HOME_SUPPORT,
} from "./landingFacts";

/** 홈 히어로 (`/` 전용). 2026-09-13 첫 MVP 확정으로 메인은 상황 분기 페이지가 아니라
 *  `상황 입력 → 후보·상담 질문` 도구(`/app`)로 보내는 페이지가 됐다. 그래서 CTA 없는
 *  공용 HeroSection(`/check`·`/checklists`)을 쓰지 않고 주 CTA를 여기 둔다.
 *  신뢰 문구는 `/app`의 TRUST_NOTE를 그대로 쓴다 — 착지한 뒤 같은 말을 다시 만나게.
 *  좁은 폭에서 버튼은 max-w-xs까지 꽉 채운다. */
function HomeHero() {
  return (
    <PageHero
      logo
      badge={HERO_BADGE}
      headline={HOME_HEADLINE}
      headlineMobileLines={HOME_HEADLINE_MOBILE_LINES}
      support={HOME_SUPPORT}
      reassurance={HERO_REASSURANCE}
    >
      <div className="flex flex-col items-center">
        <ButtonLink
          href={HOME_CTA_HREF}
          className="w-full max-w-xs !px-6 !py-3 text-base sm:w-auto"
        >
          {HOME_CTA_LABEL}
        </ButtonLink>
        <p className="mx-auto mt-3 max-w-md break-keep text-xs leading-relaxed text-ink-muted">
          {TRUST_NOTE}
        </p>
      </div>
    </PageHero>
  );
}

/** 메인은 2026-09-13부터 주 CTA(`/app` 후보·상담 질문 정리) 하나로 시작한다.
 *  상황 카드 두 장(SituationSection)은 다른 목적의 보조 퍼널로 그 아래에 둔다.
 *  StickyCtaBar는 두지 않는다 — 하단 고정은 카카오 채널 바(StickyKakaoBar, SiteChrome)가
 *  계속 맡고, 주 CTA는 히어로 하나로 충분하다. */
export function LandingPage() {
  return (
    <SiteChrome>
      <main className="flex-1">
        <HomeHero />
        <SituationSection />
        <GroundworkSection />
      </main>
    </SiteChrome>
  );
}
