"use client";

import { useRef, type ReactNode } from "react";
import { trackEvent } from "@/lib/api";
import { KAKAO_CHANNEL_URL } from "@/lib/contact";

interface KakaoChannelLinkProps {
  className?: string;
  children: ReactNode;
}

/** 카카오 채널 추가 링크. 클릭을 POST /events(kakao_channel)로 계측한다 —
 *  랜딩이 POST /waitlist를 호출하지 않게 되면서 이 이벤트가 대기자 KPI를 대신한다.
 *  계측이 링크 안에 있으므로 모달 CTA든 푸터 링크든 누락되지 않는다. */
export function KakaoChannelLink({ className, children }: KakaoChannelLinkProps) {
  const trackedRef = useRef(false);

  function handleClick() {
    if (trackedRef.current) return;
    trackedRef.current = true;
    trackEvent({ event: "kakao_channel" }).catch(() => {
      // 추적 실패가 사용자 흐름을 막지 않는다 (ChatPanel.handleTrack과 동일)
    });
  }

  return (
    <a
      href={KAKAO_CHANNEL_URL}
      target="_blank"
      rel="noopener noreferrer"
      className={className}
      onClick={handleClick}
    >
      {children}
    </a>
  );
}
