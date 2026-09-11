import type { HTMLAttributes, KeyboardEvent, ReactNode } from "react";

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  padding?: "sm" | "md" | "lg";
  /**
   * 카드 전체를 컨트롤로 만든다 — 마우스 클릭과 Enter/Space 를 같이 받는다.
   * 카드 클릭이 선택·이동 같은 동작을 하면 `onClick` 대신 이걸 쓴다. `onClick` 만
   * 주면 키보드로는 닿을 수 없는 장식용 div 로 남는다(랜딩·체크 페이지의 Card).
   */
  onActivate?: () => void;
}

const paddingClass = {
  sm: "p-3",
  md: "p-4",
  lg: "p-6",
};

export function Card({
  children,
  className = "",
  padding = "md",
  onActivate,
  ...rest
}: CardProps) {
  const activatable = onActivate
    ? {
        role: "button",
        tabIndex: 0,
        onClick: onActivate,
        onKeyDown: (event: KeyboardEvent<HTMLDivElement>) => {
          // 카드 안의 버튼·링크에서 올라온 키 이벤트는 무시한다 —
          // 아니면 중첩 버튼에서 Enter 를 눌렀을 때 버튼과 카드가 둘 다 발화한다.
          if (event.target !== event.currentTarget) return;
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            onActivate();
          }
        },
      }
    : {};

  return (
    <div
      className={[
        "rounded-card border border-border-soft bg-surface shadow-card",
        paddingClass[padding],
        onActivate
          ? "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
          : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...activatable}
      {...rest}
    >
      {children}
    </div>
  );
}
