"use client";

import { useEffect, useState, type RefObject } from "react";
import { CheckCtaLink } from "./CheckCtaLink";
import { HOME_CHECK_CTA_LABEL, STICKY_CHECK_REASSURANCE } from "./landingFacts";

interface StickyCtaBarProps {
  sentinelRef: RefObject<HTMLElement | null>;
  suppressed: boolean;
}

/** 모바일 전용 하단 고정 CTA. `/check`로 이동한다.
 *  WaitlistModal이 열려 있으면 suppressed로 숨겨 모달 뒤에서 탭되지 않게 한다. */
export function StickyCtaBar({ sentinelRef, suppressed }: StickyCtaBarProps) {
  const [visible, setVisible] = useState(false);
  const shown = visible && !suppressed;

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setVisible(!entry.isIntersecting && entry.boundingClientRect.top < 0);
      },
      { threshold: 0 },
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [sentinelRef]);

  return (
    <div
      inert={!shown}
      aria-hidden={!shown}
      className={[
        "fixed inset-x-0 bottom-0 z-40 border-t border-border bg-surface/95 px-4 pb-[env(safe-area-inset-bottom)] pt-3 shadow-card backdrop-blur transition-transform duration-200 sm:hidden",
        shown ? "translate-y-0" : "pointer-events-none translate-y-full",
      ].join(" ")}
    >
      <CheckCtaLink
        fullWidth
        className="!py-3 text-[15px] leading-snug"
        tabIndex={shown ? undefined : -1}
      >
        {HOME_CHECK_CTA_LABEL}
      </CheckCtaLink>
      <p className="pb-3 pt-2 text-center text-xs leading-relaxed text-ink-muted">
        {STICKY_CHECK_REASSURANCE}
      </p>
    </div>
  );
}
