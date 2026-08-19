import Image from "next/image";
import type { ReactNode } from "react";
import { Badge } from "@/components/ui";

interface PageHeroProps {
  /** `/`·`/check` 인트로에서 true. 헤더에 이미 작은 로고가 있어 `/checklists`는 반복하지 않는다. */
  logo?: boolean;
  badge: string;
  headline: string;
  headlineLine2?: string;
  support: string;
  /** 즉시 효익 한 줄. `/`만 쓴다 — `/check`·`/checklists`는 각자 CTA 옆에 이미 같은 문구가 있다. */
  reassurance?: string;
  /** 주 CTA 또는 첫 콘텐츠. 페이지마다 다음에 오는 것이 다르다 —
   *  `/`는 SituationSection 카드, `/check`·`/checklists`는 버튼. */
  children?: ReactNode;
}

/** 세 공개 페이지(`/`, `/check`, `/checklists`)가 공유하는 히어로 순서:
 *  상황 라벨 → h1(2줄 지원) → 설명 한 문단 → children. */
export function PageHero({
  logo = false,
  badge,
  headline,
  headlineLine2,
  support,
  reassurance,
  children,
}: PageHeroProps) {
  return (
    <section className="hero-wash mx-auto max-w-5xl px-4 pb-10 pt-8 text-center sm:px-6 sm:pt-16">
      {logo ? (
        // logo-mark.png는 원본 logo.png(정사각 캔버스, 헤더가 계속 쓴다)에서
        // 투명 여백을 잘라낸 버전이다 — 실제 글자가 표시 영역을 꽉 채우게 한다.
        <Image
          src="/logo-mark.png"
          alt="학원콕 — 우리 아이에게 맞는 학원을 찾다."
          width={1061}
          height={675}
          priority
          className="hero-fade-up mx-auto h-28 w-auto sm:h-32"
        />
      ) : null}
      <Badge
        tone="neutral"
        className={`hero-fade-up ${logo ? "mt-5" : "mt-0"}`}
      >
        {badge}
      </Badge>
      <h1 className="hero-fade-up hero-fade-up-delay-1 mx-auto mt-4 max-w-2xl break-keep text-3xl font-black leading-tight text-ink sm:text-4xl">
        {headline}
        {headlineLine2 ? (
          <>
            <br />
            {headlineLine2}
          </>
        ) : null}
      </h1>
      <p className="hero-fade-up hero-fade-up-delay-2 mx-auto mt-4 max-w-md break-keep text-sm leading-relaxed text-ink-muted">
        {support}
      </p>
      {reassurance ? (
        <p className="hero-fade-up hero-fade-up-delay-2 mt-2 text-xs text-ink-muted">
          {reassurance}
        </p>
      ) : null}
      {children ? (
        <div className="hero-fade-up hero-fade-up-delay-3 mt-6">
          {children}
        </div>
      ) : null}
    </section>
  );
}
