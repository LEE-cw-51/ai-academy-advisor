"use client";

import Link from "next/link";
import { useRef, type ReactNode } from "react";
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
 *  상황 카드(SituationCard)와 페이지 간 교차 CTA(`/checklists`↔`/check`)가 함께 쓴다.
 *  `CheckCtaLink`(홈 주 CTA였던 전용 컴포넌트)는 별개로 남아 있다 —
 *  그 파일의 modifier-click 테스트를 건드리지 않기 위해서다. */
export function TrackedLink({
  event,
  href,
  onClick,
  className,
  children,
}: TrackedLinkProps) {
  const trackedRef = useRef(false);

  function handleClick() {
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
