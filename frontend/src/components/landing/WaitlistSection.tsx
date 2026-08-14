import { Button } from "@/components/ui";

interface WaitlistSectionProps {
  onRequestWaitlist: () => void;
}

export function WaitlistSection({ onRequestWaitlist }: WaitlistSectionProps) {
  return (
    <section className="mx-auto max-w-5xl px-4 py-14 sm:px-6">
      <div className="rounded-card border border-border-soft bg-ink px-6 py-10 text-center shadow-card sm:px-10">
        <h2 className="text-xl font-bold text-surface sm:text-2xl">
          무료로 먼저 이용해보세요.
        </h2>
        <p className="mt-2 text-sm text-surface/80">
          출시 소식도 가장 먼저 알려드립니다.
        </p>
        <div className="mt-6 flex justify-center">
          <Button className="!px-6 !py-3 text-base" onClick={onRequestWaitlist}>
            출시 알림 신청하기
          </Button>
        </div>
      </div>
    </section>
  );
}
