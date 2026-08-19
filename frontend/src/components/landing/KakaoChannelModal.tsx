"use client";

import Link from "next/link";
import { Button, Modal, buttonClassName } from "@/components/ui";
import { KakaoChannelLink, type KakaoTrackEvent } from "./KakaoChannelLink";
import { KAKAO_WELCOME_HINT } from "./landingFacts";

interface KakaoChannelModalProps {
  open: boolean;
  onClose: () => void;
  /** 실제 외부 이동에 붙는 이벤트. 점검 결과 경로만 checklist_kakao_clicked. */
  event?: KakaoTrackEvent;
}

/** 외부 카카오 채널로 나가기 전 무료·개인정보 미입력·차단 가능 고지를 주는 유일한 지점.
 *  2026-08-19 이전에는 `WaitlistModal`(출시 알림 전용)이었다 —
 *  랜딩이 상황 분기로 바뀌며 카카오 CTA도 특정 보상(출시 알림·체크리스트 N종)을
 *  숫자로 약속하지 않고 "상담 때 물어볼 질문"으로 통일했다.
 *  계측은 모달 안의 실제 외부 링크에만 붙는다 — CTA를 눌러 모달을 연 것은
 *  아직 카카오로 간 것이 아니므로 전환으로 세지 않는다. */
export function KakaoChannelModal({
  open,
  onClose,
  event,
}: KakaoChannelModalProps) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      title="상담 질문, 카카오톡으로 받아보시겠어요?"
      footer={
        <>
          <KakaoChannelLink
            event={event}
            className={buttonClassName({
              variant: "kakao",
              fullWidth: true,
              className: "!py-3 text-base",
            })}
          >
            카카오톡 채널 추가하고 받기
          </KakaoChannelLink>
          <Button variant="secondary" fullWidth onClick={onClose}>
            아니요, 나중에
          </Button>
          <p className="text-center text-xs text-ink-subtle">
            채널 추가 과정의 개인정보 처리는 카카오의 정책을 따릅니다. 학원콕의{" "}
            <Link href="/privacy" className="underline underline-offset-2">
              개인정보처리방침
            </Link>
            도 확인해 보세요.
          </p>
        </>
      }
    >
      <p>
        카카오톡 채널을 추가하시면, 웰컴메시지로 학원을 알아보는 중·다니는 중
        각 상황에서 상담 때 물어보면 좋은 질문을 정리해 보내드립니다. 학원콕이
        정식 출시하는 날도 가장 먼저 알려드립니다.
      </p>
      <ul className="mt-3 list-disc space-y-1 pl-5">
        <li>신청은 무료이고, 결제 정보는 받지 않습니다.</li>
        <li>이 화면에서 이름·연락처를 따로 입력받지 않습니다.</li>
        <li>채널 차단·해제는 카카오톡에서 언제든지 하실 수 있어요.</li>
      </ul>
      <p className="mt-3 text-sm text-ink-subtle">
        {KAKAO_WELCOME_HINT}. 밤 8시 55분부터 다음날 오전 8시 사이에 추가하시면
        다음날 오전 8시에 받으실 수 있습니다.
      </p>
    </Modal>
  );
}
