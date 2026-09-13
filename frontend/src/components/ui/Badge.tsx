import type { HTMLAttributes, ReactNode } from "react";

type Tone = "brand" | "neutral" | "success" | "warn" | "rank";

const toneClass: Record<Tone, string> = {
  // 텍스트는 ink — brand-dark(#d98c0e)는 밝은 배경에서 2.7:1 로 AA 미달 (2026-09-13 axe).
  brand: "bg-brand/15 text-ink",
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
