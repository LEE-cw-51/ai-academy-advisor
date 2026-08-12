"use client";

import { useRef, useState } from "react";
import { Button, Input, Modal } from "@/components/ui";
import { joinWaitlist } from "@/lib/api";
import { ApiError } from "@/lib/types";

interface WaitlistModalProps {
  open: boolean;
  onClose: () => void;
}

export function WaitlistModal({ open, onClose }: WaitlistModalProps) {
  const [email, setEmail] = useState("");
  const [kakao, setKakao] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const openRef = useRef(open);
  openRef.current = open;
  const submitGenRef = useRef(0);

  function reset() {
    setEmail("");
    setKakao("");
    setError("");
    setDone(false);
    setLoading(false);
  }

  function handleClose() {
    submitGenRef.current += 1;
    reset();
    onClose();
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmedEmail = email.trim();
    const trimmedKakao = kakao.trim();
    if (!trimmedEmail && !trimmedKakao) {
      setError("이메일 또는 카카오톡 아이디 중 하나는 입력해 주세요.");
      return;
    }
    const submitGen = ++submitGenRef.current;
    setLoading(true);
    setError("");
    try {
      await joinWaitlist({
        email: trimmedEmail || undefined,
        kakao: trimmedKakao || undefined,
      });
      if (submitGen !== submitGenRef.current || !openRef.current) return;
      setDone(true);
    } catch (err) {
      if (submitGen !== submitGenRef.current || !openRef.current) return;
      setError(
        err instanceof ApiError
          ? err.message
          : "신청에 실패했어요. 잠시 후 다시 시도해 주세요.",
      );
    } finally {
      if (submitGen === submitGenRef.current) {
        setLoading(false);
      }
    }
  }

  return (
    <Modal
      open={open}
      onClose={handleClose}
      title={done ? "신청 완료" : "출시 알림을 받으시겠어요?"}
    >
      {done ? (
        <div className="space-y-4">
          <p>
            신청이 접수됐어요. 정식 출시 소식과 무료 이용 안내를 가장 먼저
            보내드릴게요.
          </p>
          <Button fullWidth onClick={handleClose}>
            닫기
          </Button>
        </div>
      ) : (
        <form className="space-y-4" onSubmit={handleSubmit}>
          <p>
            무료로 추천을 체험하실 수 있어요. 이메일 또는 카카오톡 아이디 중
            하나만 남겨 주시면 출시 소식을 가장 먼저 알려드립니다.
          </p>
          <Input
            label="이메일"
            name="email"
            type="email"
            placeholder="you@example.com"
            value={email}
            disabled={loading}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Input
            label="카카오톡 아이디"
            name="kakao"
            placeholder="카카오톡 아이디 (선택)"
            value={kakao}
            disabled={loading}
            onChange={(e) => setKakao(e.target.value)}
          />
          {error ? <p className="text-xs text-warn">{error}</p> : null}
          <div className="flex gap-2">
            <Button variant="secondary" onClick={handleClose}>
              아니요
            </Button>
            <Button type="submit" fullWidth disabled={loading}>
              {loading ? "신청 중…" : "출시 알림 신청하기"}
            </Button>
          </div>
        </form>
      )}
    </Modal>
  );
}
