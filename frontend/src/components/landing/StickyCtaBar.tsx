"use client";

import { useEffect, useState, type RefObject } from "react";
import { CheckCtaLink } from "./CheckCtaLink";
import { CHECK_CTA_HINT, CHECK_CTA_LABEL } from "./landingFacts";

interface StickyCtaBarProps {
  sentinelRef: RefObject<HTMLElement | null>;
  suppressed: boolean;
}

/** 모바일 전용 하단 고정 CTA. `/check`로 이동한다.
 *  2026-08-19에 `/`에서는 걷어냈다 — 메인이 상황 분기 페이지가 되며 단일 행동이
 *  없어져 하단 고정 CTA가 가리킬 곳이 없다. 컴포넌트는 지우지 않는다 —
 *  `/check` 자체 화면 안에서 스크롤이 긴 경우 재사용할 여지를 남긴다.
 *  KakaoChannelModal이 열려 있으면 suppressed로 숨겨 모달 뒤에서 탭되지 않게 한다. */
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
        {CHECK_CTA_LABEL}
      </CheckCtaLink>
      <p className="pb-3 pt-2 text-center text-xs leading-relaxed text-ink-muted">
        {CHECK_CTA_HINT}
      </p>
    </div>
  );
}
