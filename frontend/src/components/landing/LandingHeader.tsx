import Image from "next/image";
import Link from "next/link";

/** 홈·방침이 공유하는 헤더. 로고만 둔다 — 출시 전·중개 없음 고지는 히어로와
 *  경쟁하지 않게 홈에서는 결과물 칸 아래로 내렸다 (2026-09-25). 문구 상수는
 *  landingFacts에 그대로 두고 LandingPage가 렌더한다. */
export function LandingHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-surface/80 backdrop-blur">
      <div className="mx-auto flex max-w-5xl items-center gap-3 px-4 py-3 sm:px-6">
        <Link
          href="/"
          aria-label="학원콕 홈"
          className="inline-flex h-11 w-11 shrink-0 items-center justify-center focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink"
        >
          <Image
            src="/logo.png"
            alt="학원콕"
            width={1254}
            height={1254}
            priority
            className="h-9 w-9 sm:h-10 sm:w-10"
          />
        </Link>
      </div>
    </header>
  );
}
