import type { ReactNode } from "react";
import { LandingFooter } from "./LandingFooter";
import { LandingHeader } from "./LandingHeader";
import { StickyKakaoBar } from "./StickyKakaoBar";

interface SiteChromeProps {
  children: ReactNode;
}

/** `/`·`/check`·`/checklists`·`/privacy`가 공유하는 크롬.
 *  하단 고정 바가 `fixed`라 본문·법적 푸터가 가려지지 않게 패딩을 둔다.
 *  StickyKakaoBar는 pt-3 + CTA(!py-3) + 내부 pb-3 + safe-area. 375px에서
 *  라벨이 두 줄이면 바 ≈69–72px(+safe-area). 예전 5.5rem(88px)는 여유
 *  ~16px뿐이라 스크롤 끝·포커스 시 법적 링크가 바에 가려졌다.
 *  8rem(128px)+safe-area ≈ 바 + ≥44px 터치/포커스 여유.
 *  `/app`은 안내형 추천 셸이라 여기 넣지 않는다. */
export function SiteChrome({ children }: SiteChromeProps) {
  return (
    <div className="flex min-h-screen flex-col bg-canvas pb-[calc(8rem+env(safe-area-inset-bottom))]">
      <LandingHeader />
      {children}
      <LandingFooter />
      <StickyKakaoBar />
    </div>
  );
}
