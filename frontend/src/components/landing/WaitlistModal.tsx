"use client";

import Link from "next/link";
import { Button, Modal, buttonClassName } from "@/components/ui";
import { KakaoChannelLink } from "./KakaoChannelLink";

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
          {/* 모달이 닫히면 Modal이 null을 반환해 링크가 언마운트되므로,
              다시 열 때 중복 발사 가드(trackedRef)가 새로 시작된다. */}
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
        보내드립니다.
      </p>
      <ul className="mt-3 list-disc space-y-1 pl-5">
        <li>신청은 무료이고, 결제 정보는 받지 않습니다.</li>
        <li>이 화면에서 이름·연락처를 따로 입력받지 않습니다.</li>
        <li>채널 차단·해제는 카카오톡에서 언제든지 하실 수 있어요.</li>
      </ul>
    </Modal>
  );
}
