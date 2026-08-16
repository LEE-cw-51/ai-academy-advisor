"use client";

import { useEffect, useState, type RefObject } from "react";
import { Button } from "@/components/ui";

interface StickyCtaBarProps {
  /** 히어로 CTA 바로 아래에 놓인 감시용 엘리먼트. 이게 화면 위로 벗어나면 바가 뜬다. */
  sentinelRef: RefObject<HTMLElement | null>;
  onRequestWaitlist: () => void;
}

/** 모바일 전용 하단 고정 CTA.
 *
 *  상단 고정 CTA는 일부러 두지 않는다 — 스티키가 있으면 상단 CTA가 더하는 효과가
 *  거의 없어서(스티키 단독 +11% / 둘 다 +12%) 화면만 좁아진다.
 *
 *  버튼은 WaitlistModal을 여는 기존 흐름을 그대로 쓴다. 여기서 카카오 링크를 새로
 *  만들면 KakaoChannelLink의 kakao_channel 계측을 우회하게 되므로 만들지 않는다. */
export function StickyCtaBar({ sentinelRef, onRequestWaitlist }: StickyCtaBarProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        // 감시 지점이 뷰포트 "위로" 지나갔을 때만 보여준다.
        // 아래쪽에 있어서 안 보이는 초기 상태에서는 뜨지 않아야 한다.
        setVisible(!entry.isIntersecting && entry.boundingClientRect.top < 0);
      },
      { threshold: 0 },
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [sentinelRef]);

  return (
    <div
      aria-hidden={!visible}
      className={[
        "fixed inset-x-0 bottom-0 z-40 border-t border-border bg-surface/95 px-4 pb-[env(safe-area-inset-bottom)] pt-3 shadow-card backdrop-blur transition-transform duration-200 sm:hidden",
        visible ? "translate-y-0" : "translate-y-full",
      ].join(" ")}
    >
      <Button
        fullWidth
        className="!py-3 text-base"
        onClick={onRequestWaitlist}
        tabIndex={visible ? undefined : -1}
      >
        카카오톡으로 무료 출시 알림 받기
      </Button>
      <p className="pb-3 pt-2 text-center text-xs text-ink-subtle">
        무료 · 개인정보 입력 없음 · 언제든 차단 가능
      </p>
    </div>
  );
}
