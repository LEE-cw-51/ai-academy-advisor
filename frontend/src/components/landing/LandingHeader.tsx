import Image from "next/image";
import Link from "next/link";
import { HEADER_STATUS_NOTICE } from "./landingFacts";

/** 로고 옆에 운영 전·판매 없음 고지를 둔다. 배지 형태는 쓰지 않는다 —
 *  2026-08-16이 헤더에서 뺀 것은 스크롤 내내 따라다니는 배지였다. */
export function LandingHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-surface/80 backdrop-blur">
      <div className="mx-auto flex max-w-5xl items-center gap-3 px-4 py-3 sm:px-6">
        <Link href="/" aria-label="학원콕 홈" className="shrink-0">
          <Image
            src="/logo.png"
            alt="학원콕"
            width={1254}
            height={1254}
            priority
            className="h-9 w-9 sm:h-10 sm:w-10"
          />
        </Link>
        <p className="break-keep text-xs leading-snug text-ink-muted">
          {HEADER_STATUS_NOTICE}
        </p>
      </div>
    </header>
  );
}
