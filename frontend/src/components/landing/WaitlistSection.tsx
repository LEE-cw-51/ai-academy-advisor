import { Button } from "@/components/ui";
import { CTA_REASSURANCE, WAITLIST_CTA_LABEL } from "./landingFacts";

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
        <p className="mt-2 break-keep text-sm text-surface/80">
          카카오톡 채널을 추가해 두시면 출시하는 날 알려드릴게요.
        </p>
        <div className="mt-6 flex flex-col items-center gap-3">
          <Button className="!px-6 !py-3 text-base" onClick={onRequestWaitlist}>
            {WAITLIST_CTA_LABEL}
          </Button>
          <p className="text-xs text-surface/80">{CTA_REASSURANCE}</p>
        </div>
      </div>
    </section>
  );
}
