import type { HTMLAttributes, ReactNode } from "react";

export interface DisclaimerProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export function Disclaimer({
  children,
  className = "",
  ...rest
}: DisclaimerProps) {
  return (
    <div
      className={[
        "rounded-btn border border-warn/30 bg-warn-bg px-3 py-2 text-xs font-medium text-warn",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      role="note"
      {...rest}
    >
      {children}
    </div>
  );
}
