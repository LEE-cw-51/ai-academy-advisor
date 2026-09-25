import Image from "next/image";
import type { ReactNode } from "react";
import { Badge } from "@/components/ui";

function HeadlineLines({ lines }: { lines: readonly string[] }) {
  return (
    <>
      {lines.map((line, index) => (
        <span key={line}>
          {index > 0 ? <br /> : null}
          {line}
        </span>
      ))}
    </>
  );
}

interface PageHeroProps {
  /** 히어로 큰 로고. 헤더에 이미 작은 로고가 있으므로 페이지가 원할 때만 켠다. */
  logo?: boolean;
  badge: string;
  headline: string;
  /** sm 미만에서만 쓰는 h1 줄바꿈. 없으면 headline 한 줄로 렌더한다. */
  headlineMobileLines?: readonly string[];
  support: string;
  /** 즉시 효익 한 줄. */
  reassurance?: string;
  /** 주 CTA 또는 첫 콘텐츠. `/`는 `/app`으로 가는 주 CTA와 신뢰 문구. */
  children?: ReactNode;
}

/** 공개 히어로 순서: 상황 라벨 → h1 → 설명 한 문단 → children.
 *  2026-09-14 `/check`·`/checklists` 퇴역 뒤로는 `/`(HomeHero)만 쓴다. 두 줄 제목
 *  prop(`headlineLine2`)은 그 두 페이지의 공용 히어로 전용이라 함께 걷어냈다. */
export function PageHero({
  logo = false,
  badge,
  headline,
  headlineMobileLines,
  support,
  reassurance,
  children,
}: PageHeroProps) {
  return (
    <section className="hero-wash mx-auto max-w-5xl px-4 pb-8 pt-6 text-left sm:px-6 sm:pb-10 sm:pt-12">
      {logo ? (
        // logo-mark.png는 원본 logo.png(정사각 캔버스, 헤더가 계속 쓴다)에서
        // 투명 여백을 잘라낸 버전이다 — 실제 글자가 표시 영역을 꽉 채우게 한다.
        <Image
          src="/logo-mark.png"
          alt="학원콕"
          width={1061}
          height={675}
          priority
          className="hero-fade-up h-14 w-auto sm:h-20"
        />
      ) : null}
      <Badge
        tone="neutral"
        className={`hero-fade-up ${logo ? "mt-5" : "mt-0"}`}
      >
        {badge}
      </Badge>
      <h1 className="hero-fade-up hero-fade-up-delay-1 mt-4 max-w-2xl break-keep text-2xl font-semibold leading-snug tracking-tight text-ink sm:mt-5 sm:text-4xl">
        {headlineMobileLines ? (
          <>
            <span className="sm:hidden">
              <HeadlineLines lines={headlineMobileLines} />
            </span>
            <span className="hidden sm:inline">{headline}</span>
          </>
        ) : (
          headline
        )}
      </h1>
      <p className="hero-fade-up hero-fade-up-delay-2 mt-3 max-w-[40rem] break-keep text-base leading-relaxed text-ink-muted">
        {support}
      </p>
      {reassurance ? (
        <p className="hero-fade-up hero-fade-up-delay-2 mt-2 text-xs text-ink-muted">
          {reassurance}
        </p>
      ) : null}
      {children ? (
        <div className="hero-fade-up hero-fade-up-delay-3 mt-5">
          {children}
        </div>
      ) : null}
    </section>
  );
}
