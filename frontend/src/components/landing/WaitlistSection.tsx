import { Button } from "@/components/ui";

interface WaitlistSectionProps {
  onRequestWaitlist: () => void;
}

export function WaitlistSection({ onRequestWaitlist }: WaitlistSectionProps) {
  return (
    <section className="mx-auto max-w-5xl px-4 py-14 sm:px-6">
      <div className="rounded-card border border-border-soft bg-ink px-6 py-10 text-center shadow-card sm:px-10">
        <h2 className="text-xl font-bold text-surface sm:text-2xl">
          출시하면 가장 먼저 알려드릴게요.
        </h2>
        <p className="mt-2 text-sm text-surface/80">
          지금 하실 수 있는 건 무료 출시 알림 신청뿐이에요. 카카오톡 채널을
          추가해 두시면 정식 출시하는 날 알림을 보내드립니다.
        </p>
        <div className="mt-6 flex flex-col items-center gap-3">
          <Button className="!px-6 !py-3 text-base" onClick={onRequestWaitlist}>
            카카오톡으로 무료 출시 알림 받기
          </Button>
          {/* HeroSection·StickyCtaBar와 같은 문구를 쓴다 (WaitlistModal의 3개 항목). */}
          <p className="text-xs text-surface/70">
            무료 · 개인정보 입력 없음 · 언제든 차단 가능
          </p>
        </div>
      </div>
    </section>
  );
}
