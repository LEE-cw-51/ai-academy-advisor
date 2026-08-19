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

/** 가상 추천 카드(ServicePreviewSection)와 출시 알림 섹션(WaitlistSection)을
 *  2026-08-19에 이 한 섹션으로 합쳤다. 가상 추천 카드는 상황 선택이라는 메인의
 *  첫 과업과 무관하고, 속성 필드가 0%인 정본에서 오해를 살 위험이 커 삭제했다.
 *  여기 남기는 것은 지금 확인 가능한 사실(410곳)과 준비 중인 것(맞춤 추천)뿐이다.
 *  카카오 CTA는 하단 고정 바(StickyKakaoBar)와 같은 목적이지만, 근거 설명 직후의
 *  자연스러운 전환이라 둔다 — 이벤트는 모달 안 링크에만 붙어 이중 집계가 없다. */
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
