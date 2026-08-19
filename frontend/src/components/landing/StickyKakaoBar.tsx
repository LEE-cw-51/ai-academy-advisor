"use client";

import { buttonClassName } from "@/components/ui";
import { KakaoChannelCta } from "./KakaoChannelCta";
import { FOOTER_KAKAO_CTA_LABEL } from "./landingFacts";

/** 소개 페이지 전 폭·전 뷰포트 하단 고정 바. 문서 끝 법적 푸터를 sticky로
 *  올리면 페이지 상단에서는 안 보이므로 `fixed`다.
 *  StickyCtaBar(`/check` 이동, 모바일 전용)와 역할이 달라 재사용하지 않는다. */
export function StickyKakaoBar() {
  return (
    <div className="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-surface/95 px-4 pb-[env(safe-area-inset-bottom)] pt-3 shadow-card backdrop-blur">
      <div className="mx-auto max-w-5xl pb-3">
        <KakaoChannelCta
          className={buttonClassName({
            variant: "kakao",
            fullWidth: true,
            className: "!py-3 text-base",
          })}
        >
          {FOOTER_KAKAO_CTA_LABEL}
        </KakaoChannelCta>
      </div>
    </div>
  );
}
