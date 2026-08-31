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

/** 메인 히어로. 기능 하나를 팔지 않는다 — 아래 SituationSection의 카드 두 장이
 *  실제 선택지라서 여기엔 주 CTA 버튼을 두지 않는다.
 *  `/`·`/check`·`/checklists` 세 페이지가 같은 히어로를 재사용하므로, 페이지별로
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
