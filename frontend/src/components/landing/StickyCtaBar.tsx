"use client";

import { useEffect, useState, type RefObject } from "react";
import { Button } from "@/components/ui";
import { CTA_REASSURANCE, WAITLIST_CTA_LABEL } from "./landingFacts";

interface StickyCtaBarProps {
  sentinelRef: RefObject<HTMLElement | null>;
  suppressed: boolean;
  onRequestWaitlist: () => void;
}

/** 모바일 전용 하단 고정 CTA. WaitlistModal을 연다 — KakaoChannelLink 계측을 우회하지 않는다. */
export function StickyCtaBar({
  sentinelRef,
  suppressed,
  onRequestWaitlist,
}: StickyCtaBarProps) {
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
      <Button
        fullWidth
        className="!py-3 text-[15px] leading-snug"
        onClick={onRequestWaitlist}
        tabIndex={shown ? undefined : -1}
      >
        {WAITLIST_CTA_LABEL}
      </Button>
      <p className="pb-3 pt-2 text-center text-xs leading-relaxed text-ink-muted">
        {CTA_REASSURANCE}
      </p>
    </div>
  );
}
