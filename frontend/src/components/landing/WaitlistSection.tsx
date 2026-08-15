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
            무료 출시 알림 신청하기
          </Button>
          <p className="text-xs text-surface/70">
            수강 신청이나 결제가 아니고, 비용도 들지 않습니다.
          </p>
        </div>
      </div>
    </section>
  );
}
