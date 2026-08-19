import { PageHero } from "./PageHero";
import {
  HERO_BADGE,
  HERO_HEADLINE,
  HERO_HEADLINE_LINE2,
  HERO_REASSURANCE,
  HERO_SUPPORT,
} from "./landingFacts";

/** 메인 히어로. 기능 하나를 팔지 않는다 — 아래 SituationSection의 카드 두 장이
 *  실제 선택지라서 여기엔 주 CTA 버튼을 두지 않는다. */
export function HeroSection() {
  return (
    <PageHero
      logo
      badge={HERO_BADGE}
      headline={HERO_HEADLINE}
      headlineLine2={HERO_HEADLINE_LINE2}
      support={HERO_SUPPORT}
      reassurance={HERO_REASSURANCE}
    />
  );
}
