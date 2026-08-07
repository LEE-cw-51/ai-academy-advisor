import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "secondary" | "kakao" | "ghost";

const variantClass: Record<Variant, string> = {
  primary:
    "bg-brand text-ink-strong hover:bg-brand-dark shadow-soft disabled:opacity-60",
  secondary:
    "bg-surface text-ink border border-border hover:bg-surface-muted disabled:opacity-60",
  kakao: "bg-kakao text-ink-strong hover:brightness-95 disabled:opacity-60",
  ghost: "bg-transparent text-ink-muted hover:bg-surface-muted disabled:opacity-60",
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  children: ReactNode;
  fullWidth?: boolean;
}

export function Button({
  variant = "primary",
  className = "",
  fullWidth,
  children,
  type = "button",
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      className={[
        "inline-flex items-center justify-center gap-2 rounded-btn px-4 py-2.5 text-sm font-semibold transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand",
        variantClass[variant],
        fullWidth ? "w-full" : "",
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
