"use client";

import { useCallback, useState, type ReactNode } from "react";
import { KakaoChannelModal } from "./KakaoChannelModal";
import type { KakaoTrackEvent } from "./KakaoChannelLink";

interface KakaoChannelCtaProps {
  children: ReactNode;
  className?: string;
  /** 실제 외부 이동에 붙는 이벤트. 점검 결과 경로만 checklist_kakao_clicked. */
  event?: KakaoTrackEvent;
}

/** 카카오 채널로 나가는 모든 입구가 공유하는 CTA — 누르면 바로 카카오로 가지 않고
 *  먼저 `KakaoChannelModal`을 띄워 "채널을 추가하면 상담 때 참고할 질문을 보내드린다"는
 *  보상과 무료·개인정보 미입력·차단 가능 고지를 보여준다.
 *  이 컴포넌트가 생기기 전에는 메인(`/`)만 모달을 거쳤고 `/checklists`·`/check` 결과·푸터는
 *  바로 외부로 나갔다 — 같은 약속을 같은 방식으로 하기 위해 한 곳으로 모았다.
 *  모달 상태를 각 호출부가 아니라 여기서 들고 있어 페이지마다 배선을 반복하지 않는다. */
export function KakaoChannelCta({
  children,
  className,
  event,
}: KakaoChannelCtaProps) {
  const [open, setOpen] = useState(false);

  const openModal = useCallback(() => setOpen(true), []);
  const closeModal = useCallback(() => setOpen(false), []);

  return (
    <>
      <button type="button" className={className} onClick={openModal}>
        {children}
      </button>
      <KakaoChannelModal open={open} onClose={closeModal} event={event} />
    </>
  );
}
