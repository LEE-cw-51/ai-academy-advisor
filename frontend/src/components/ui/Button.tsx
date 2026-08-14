import type { AnchorHTMLAttributes, ButtonHTMLAttributes, ReactNode } from "react";
import Link from "next/link";

type Variant = "primary" | "secondary" | "kakao" | "ghost";

const variantClass: Record<Variant, string> = {
  primary:
    "bg-brand text-ink-strong hover:bg-brand-dark shadow-soft disabled:opacity-60",
  secondary:
    "bg-surface text-ink border border-border hover:bg-surface-muted disabled:opacity-60",
  kakao: "bg-kakao text-ink-strong hover:brightness-95 disabled:opacity-60",
  ghost: "bg-transparent text-ink-muted hover:bg-surface-muted disabled:opacity-60",
};

const baseClass =
  "inline-flex items-center justify-center gap-2 rounded-btn px-4 py-2.5 text-sm font-semibold transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand";

export function buttonClassName(options?: {
  variant?: Variant;
  fullWidth?: boolean;
  className?: string;
}): string {
  const { variant = "primary", fullWidth, className = "" } = options ?? {};
  return [baseClass, variantClass[variant], fullWidth ? "w-full" : "", className]
    .filter(Boolean)
    .join(" ");
}

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
      className={buttonClassName({ variant, fullWidth, className })}
      {...rest}
    >
      {children}
    </button>
  );
}

export interface ButtonLinkProps
  extends Omit<AnchorHTMLAttributes<HTMLAnchorElement>, "href"> {
  href: string;
  variant?: Variant;
  children: ReactNode;
  fullWidth?: boolean;
  className?: string;
}

/** `<a>`/`Link`용 버튼 스타일 — `<button>`을 중첩하지 않는다. */
export function ButtonLink({
  href,
  variant = "primary",
  fullWidth,
  className = "",
  children,
  ...rest
}: ButtonLinkProps) {
  return (
    <Link
      href={href}
      className={buttonClassName({ variant, fullWidth, className })}
      {...rest}
    >
      {children}
    </Link>
  );
}
