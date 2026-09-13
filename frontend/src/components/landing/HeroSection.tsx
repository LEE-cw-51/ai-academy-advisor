import { PageHero } from "./PageHero";
import {
  HERO_BADGE,
  HERO_HEADLINE,
  HERO_HEADLINE_LINE2,
  HERO_HEADLINE_MOBILE_LINES,
  HERO_REASSURANCE,
  HERO_SUPPORT,
} from "./landingFacts";

interface HeroSectionProps {
  /** `/checklists`는 헤더에 이미 작은 로고가 있어 반복하지 않는다 (PageHero 참고). */
  logo?: boolean;
  /** `/check`·`/checklists`는 각자 CTA 옆에 이미 같은 " · " 배지 문구가 있어 억제한다. */
  reassurance?: boolean;
}

/** `/check`·`/checklists`가 공유하는 히어로. `/`는 2026-09-13부터 LandingPage 안의
 *  HomeHero(`/app` 주 CTA)를 쓴다. 두 페이지가 같은 히어로를 재사용하므로, 페이지별로
 *  다른 logo·reassurance 조합만 prop으로 받는다. */
export function HeroSection({ logo = true, reassurance = true }: HeroSectionProps = {}) {
  return (
    <PageHero
      logo={logo}
      badge={HERO_BADGE}
      headline={HERO_HEADLINE}
      headlineLine2={HERO_HEADLINE_LINE2}
      headlineMobileLines={HERO_HEADLINE_MOBILE_LINES}
      support={HERO_SUPPORT}
      reassurance={reassurance ? HERO_REASSURANCE : undefined}
    />
  );
}
