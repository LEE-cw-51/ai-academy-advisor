import type { HTMLAttributes, ReactNode } from "react";

type Tone = "brand" | "neutral" | "success" | "warn" | "rank";

const toneClass: Record<Tone, string> = {
  // brand 톤도 주황을 쓰지 않는다 — 주황은 CTA·선택 상태에만 (2026-09-25).
  // API 호환을 위해 tone 이름은 유지하고 면은 neutral과 같게 둔다.
  brand: "bg-surface-subtle text-ink",
  neutral: "bg-surface-subtle text-ink-muted",
  success: "bg-success-bg text-success",
  warn: "bg-warn-bg text-warn",
  rank: "bg-ink text-surface",
};

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: Tone;
  children: ReactNode;
}

export function Badge({
  tone = "neutral",
  className = "",
  children,
  ...rest
}: BadgeProps) {
  return (
    <span
      className={[
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold",
        toneClass[tone],
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...rest}
    >
      {children}
    </span>
  );
}
