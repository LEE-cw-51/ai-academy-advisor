import { buttonClassName } from "@/components/ui";
import { KakaoChannelCta } from "./KakaoChannelCta";
import {
  CTA_REASSURANCE,
  GROUNDWORK_BODY,
  GROUNDWORK_HEADING,
  GROUNDWORK_SOURCE_NOTE,
  KAKAO_REWARD_LABEL,
  KAKAO_REWARD_NOTE,
} from "./landingFacts";

/** 메인 하단. 지금 확인 가능한 사실(MISA_ACADEMY_COUNT)과 후보 정리가 그 사실 위에서
 *  돌아간다는 것만 말한다 — "정식 출시 후 제공" 예고는 `/app`이 주 CTA가 되며 뺐다
 *  (2026-09-13, docs/decision-log.md). 카카오 CTA는 하단 고정 바(StickyKakaoBar)와 같은
 *  목적이지만, 근거 설명 직후의 자연스러운 전환이라 둔다 — 이벤트는 모달 안 링크에만
 *  붙어 이중 집계가 없다. `/app` 링크는 히어로 주 CTA 하나로 충분해 여기엔 두지 않는다. */
export function GroundworkSection() {
  return (
    <section className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <div className="mx-auto max-w-xl rounded-card border border-border-soft bg-surface-muted px-6 py-8 text-center">
        <h2 className="text-lg font-bold text-ink sm:text-xl">
          {GROUNDWORK_HEADING}
        </h2>
        <p className="mt-2 break-keep text-sm leading-relaxed text-ink-muted">
          {GROUNDWORK_BODY}
        </p>
        <p className="mt-1 break-keep text-xs text-ink-subtle">
          {GROUNDWORK_SOURCE_NOTE}
        </p>
        <div className="mt-5 flex flex-col items-center gap-2">
          <KakaoChannelCta
            className={buttonClassName({
              variant: "secondary",
              className: "!px-6 !py-3 text-base",
            })}
          >
            {KAKAO_REWARD_LABEL}
          </KakaoChannelCta>
          <p className="max-w-xs break-keep text-xs text-ink-muted">
            {KAKAO_REWARD_NOTE}
          </p>
          <p className="text-xs text-ink-muted">{CTA_REASSURANCE}</p>
        </div>
      </div>
    </section>
  );
}
