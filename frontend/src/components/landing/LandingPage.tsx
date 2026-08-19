import { GroundworkSection } from "./GroundworkSection";
import { HeroSection } from "./HeroSection";
import { PlannedFeaturesSection } from "./PlannedFeaturesSection";
import { ServicePreviewSection } from "./ServicePreviewSection";
import { SiteChrome } from "./SiteChrome";
import { SituationSection } from "./SituationSection";

/** 메인은 기능 하나를 파는 페이지가 아니라 학부모가 자기 상황을 고르는 분기 페이지다
 *  (2026-08-19 3페이지 퍼널 재구성). 그래서 StickyCtaBar를 두지 않는다 —
 *  단일 행동이 없어 하단 고정 CTA가 가리킬 곳이 없다.
 *  하단 고정은 카카오 출시 알림(StickyKakaoBar, SiteChrome)이다. */
export function LandingPage() {
  return (
    <SiteChrome>
      <main className="flex-1">
        <HeroSection />
        <SituationSection />
        <PlannedFeaturesSection />
        <ServicePreviewSection />
        <GroundworkSection />
      </main>
    </SiteChrome>
  );
}
