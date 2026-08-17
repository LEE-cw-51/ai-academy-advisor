"use client";

import Link from "next/link";
import { Button, Modal, buttonClassName } from "@/components/ui";
import { KakaoChannelLink } from "./KakaoChannelLink";
import { KAKAO_WELCOME_HINT } from "./landingFacts";

interface WaitlistModalProps {
  open: boolean;
  onClose: () => void;
}

export function WaitlistModal({ open, onClose }: WaitlistModalProps) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      title="출시 알림을 받으시겠어요?"
      footer={
        <>
          <KakaoChannelLink
            className={buttonClassName({
              variant: "kakao",
              fullWidth: true,
              className: "!py-3 text-base",
            })}
          >
            카카오톡 채널 추가하고 알림 받기
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
        카카오톡 채널을 추가하시면, 학원콕이 정식 출시하는 날 가장 먼저 알림을
        보내드립니다. 웰컴메시지로 학원 점검 체크리스트 3종도 함께 드립니다.
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
