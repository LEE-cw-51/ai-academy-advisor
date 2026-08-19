import { Badge } from "@/components/ui";
import { TrackedLink } from "./TrackedLink";
import type { ClickEventType } from "@/lib/types";

interface SituationCardProps {
  label: string;
  title: string;
  body: string;
  ctaLabel: string;
  href: string;
  event: ClickEventType;
}

/** 메인의 상황 분기 카드. 카드 전체가 링크다 — 제목·설명 어디를 눌러도 이동한다. */
export function SituationCard({
  label,
  title,
  body,
  ctaLabel,
  href,
  event,
}: SituationCardProps) {
  return (
    <TrackedLink
      href={href}
      event={event}
      className="group flex min-h-44 flex-col gap-3 rounded-card border border-border-soft bg-surface p-6 text-left shadow-card transition-colors hover:border-brand focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
    >
      <Badge tone="neutral" className="w-fit">
        {label}
      </Badge>
      <h3 className="text-lg font-bold text-ink">{title}</h3>
      <p className="break-keep text-sm leading-relaxed text-ink-muted">
        {body}
      </p>
      <span className="mt-auto inline-flex items-center gap-1 pt-2 text-sm font-semibold text-brand-dark group-hover:text-ink">
        {ctaLabel}
        <span aria-hidden>→</span>
      </span>
    </TrackedLink>
  );
}
