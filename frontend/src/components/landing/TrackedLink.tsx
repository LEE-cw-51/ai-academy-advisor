"use client";

import Link from "next/link";
import { useRef, type MouseEvent, type ReactNode } from "react";
import { trackEvent } from "@/lib/api";
import type { ClickEventType } from "@/lib/types";

interface TrackedLinkProps {
  event: ClickEventType;
  /** 내부 경로. null이면 버튼으로 렌더하고 `onClick`(예: 카카오 모달 열기)만 실행한다. */
  href: string | null;
  onClick?: () => void;
  className?: string;
  children: ReactNode;
}

/** `KakaoChannelLink`와 같은 계측 패턴의 일반화 버전 — 링크 안에서 계측해
 *  호출부에서 누락되지 않게 하고, 실패해도 사용자 흐름을 막지 않는다.
 *  상황 카드(SituationCard)와 페이지 간 교차 CTA(`/checklists`↔`/check`)가 함께 쓴다. */
export function TrackedLink({
  event,
  href,
  onClick,
  className,
  children,
}: TrackedLinkProps) {
  const trackedRef = useRef(false);

  function handleClick(
    clickEvent: MouseEvent<HTMLButtonElement | HTMLAnchorElement>,
  ) {
    // 수정 클릭(⌘/Ctrl 등, 새 탭)은 latch하지 않는다 — 그래야 같은 페이지에서
    // 이어서 일반 클릭해도 계측이 빠지지 않는다.
    const modified =
      clickEvent.metaKey ||
      clickEvent.ctrlKey ||
      clickEvent.shiftKey ||
      clickEvent.altKey;
    if (modified) {
      trackEvent({ event }).catch(() => {
        // 추적 실패가 사용자 흐름을 막지 않는다 (KakaoChannelLink와 동일)
      });
      onClick?.();
      return;
    }
    if (!trackedRef.current) {
      trackedRef.current = true;
      trackEvent({ event }).catch(() => {
        // 추적 실패가 사용자 흐름을 막지 않는다 (KakaoChannelLink와 동일)
      });
    }
    onClick?.();
  }

  if (href === null) {
    return (
      <button type="button" className={className} onClick={handleClick}>
        {children}
      </button>
    );
  }

  return (
    <Link href={href} className={className} onClick={handleClick}>
      {children}
    </Link>
  );
}
