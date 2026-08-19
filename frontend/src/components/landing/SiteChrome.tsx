import type { ReactNode } from "react";
import { LandingFooter } from "./LandingFooter";
import { LandingHeader } from "./LandingHeader";
import { StickyKakaoBar } from "./StickyKakaoBar";

interface SiteChromeProps {
  children: ReactNode;
}

/** `/`·`/check`·`/checklists`·`/privacy`가 공유하는 크롬.
 *  하단 고정 바가 `fixed`라 본문·법적 푸터가 가려지지 않게 패딩을 둔다.
 *  5.5rem(88px) = 바 높이(44px) + 44px 여유. 바 라벨이 한 줄일 때 기준이고,
 *  라벨이 두 줄이 되면 바가 ~72px가 되니 여전히 덮는다. `/app`은 안내형 추천 셸이라 여기 넣지 않는다. */
export function SiteChrome({ children }: SiteChromeProps) {
  return (
    <div className="flex min-h-screen flex-col bg-canvas pb-[calc(5.5rem+env(safe-area-inset-bottom))]">
      <LandingHeader />
      {children}
      <LandingFooter />
      <StickyKakaoBar />
    </div>
  );
}
