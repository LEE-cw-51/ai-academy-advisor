import { ButtonLink } from "@/components/ui";
import { TRUST_NOTE } from "@/components/app/exploreCopy";
import { OutputProofSection } from "./OutputProofSection";
import { PageHero } from "./PageHero";
import { SiteChrome } from "./SiteChrome";
import {
  HEADER_STATUS_NOTICE,
  HERO_BADGE,
  HERO_REASSURANCE,
  HOME_CTA_HREF,
  HOME_CTA_LABEL,
  HOME_HEADLINE,
  HOME_HEADLINE_MOBILE_LINES,
  HOME_SUPPORT,
} from "./landingFacts";

/** 홈 히어로 (`/` 전용). 2026-09-13 첫 MVP 확정으로 메인은 상황 분기 페이지가 아니라
 *  `상황 입력 → 후보·상담 질문` 도구(`/app`)로 보내는 페이지가 됐다. 주 CTA는 여기 둔다.
 *  히어로 신뢰 문구는 HERO_REASSURANCE 하나만. TRUST_NOTE는 결과물 칸 아래에 두어
 *  같은 말을 두 줄로 겹치지 않는다 (2026-09-25). 좁은 폭에서 버튼은 max-w-xs까지 꽉 채운다. */
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
      <div className="flex flex-col items-start">
        <ButtonLink
          href={HOME_CTA_HREF}
          className="w-full max-w-xs !px-6 !py-3 text-base sm:w-auto"
        >
          {HOME_CTA_LABEL}
        </ButtonLink>
      </div>
    </PageHero>
  );
}

/** 메인은 주 CTA(`/app`) 히어로 + 바로 아래 결과물 한 칸.
 *  출시 전·중개 없음 고지와 TRUST_NOTE는 히어로와 경쟁하지 않게 아래에 둔다.
 *  근거 구간·법적 푸터·노란 카카오 고정 바는 2026-09-25에 홈에서 뺐다 — 문의·방침·
 *  카카오 진입은 `/privacy`의 SiteChrome(footer·kakaoBar)이 맡는다.
 *  StickyCtaBar는 두지 않는다 — 주 CTA는 히어로 하나로 충분하다. */
export function LandingPage() {
  return (
    <SiteChrome>
      <main className="flex-1">
        <HomeHero />
        <OutputProofSection />
        <div className="mx-auto max-w-5xl space-y-2 px-4 pb-12 sm:px-6">
          <p className="max-w-md break-keep text-xs leading-relaxed text-ink-muted">
            {TRUST_NOTE}
          </p>
          <p className="max-w-xl break-keep text-xs leading-relaxed text-ink-subtle">
            {HEADER_STATUS_NOTICE}
          </p>
        </div>
      </main>
    </SiteChrome>
  );
}
