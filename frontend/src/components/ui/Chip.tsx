import type { ButtonHTMLAttributes, ReactNode } from "react";

export interface ChipProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  selected?: boolean;
  /** Soft selected look (e.g. fixed region chip) */
  soft?: boolean;
  children: ReactNode;
}

export function Chip({
  selected = false,
  soft = false,
  className = "",
  children,
  type = "button",
  disabled,
  ...rest
}: ChipProps) {
  const selectedClass = soft
    ? "border-transparent bg-warn-bg font-semibold text-warn"
    : "border-brand bg-brand font-semibold text-ink-strong";

  return (
    <button
      type={type}
      aria-pressed={selected}
      disabled={disabled}
      className={[
        "inline-flex shrink-0 items-center justify-center rounded-full border px-3.5 py-1.5 text-sm transition-colors",
        "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand",
        disabled && !selected ? "cursor-not-allowed opacity-50" : "",
        disabled && selected ? "cursor-default" : "",
        selected
          ? selectedClass
          : "border-border bg-surface font-medium text-ink-muted hover:border-brand/60 hover:text-ink",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...rest}
    >
      {children}
    </button>
  );
}
