"use client";

import { useRef, type MouseEvent, type ReactNode } from "react";
import { ButtonLink } from "@/components/ui";
import { trackEvent } from "@/lib/api";

interface CheckCtaLinkProps {
  children: ReactNode;
  className?: string;
  tabIndex?: number;
  fullWidth?: boolean;
}

/** 홈 → `/check` 진입 링크. 클릭을 POST /events `home_check_clicked`로 계측한다.
 *  히어로와 스티키 바가 같은 컴포넌트를 써서 계측이 빠지지 않게 한다.
 *  `mini_check_home_clicked`(점검→홈)와 반대 방향이므로 그 이벤트를 재사용하지 않는다.
 *  수정 클릭(새 탭)은 latch하지 않아, 같은 페이지에서 이어서 일반 클릭해도 계측된다. */
export function CheckCtaLink({
  children,
  className,
  tabIndex,
  fullWidth,
}: CheckCtaLinkProps) {
  const trackedRef = useRef(false);

  function handleClick(event: MouseEvent<HTMLAnchorElement>) {
    const modified =
      event.metaKey || event.ctrlKey || event.shiftKey || event.altKey;
    if (modified) {
      trackEvent({ event: "home_check_clicked" }).catch(() => {
        // 추적 실패가 사용자 흐름을 막지 않는다 (KakaoChannelLink와 동일)
      });
      return;
    }
    if (trackedRef.current) return;
    trackedRef.current = true;
    trackEvent({ event: "home_check_clicked" }).catch(() => {
      // 추적 실패가 사용자 흐름을 막지 않는다 (KakaoChannelLink와 동일)
    });
  }

  return (
    <ButtonLink
      href="/check"
      className={className}
      fullWidth={fullWidth}
      tabIndex={tabIndex}
      onClick={handleClick}
    >
      {children}
    </ButtonLink>
  );
}
