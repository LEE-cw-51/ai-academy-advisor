import Link from "next/link";
import { Badge } from "@/components/ui";
import {
  APP_BADGE,
  APP_HEADER_NOTE,
  APP_NO_BROKERAGE,
  APP_TITLE,
} from "./exploreCopy";

/** `/app`·`/app/search` 공통 헤더 — 학원콕·하남 미사·중개 없음·개인정보. */
export function AppExploreHeader() {
  return (
    <header className="border-b border-border-soft bg-canvas/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-3 sm:px-6">
        <Link
          href="/"
          aria-label="학원콕 홈"
          className="text-lg font-semibold tracking-tight text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink"
        >
          {APP_TITLE}
        </Link>
        <Badge tone="neutral">{APP_BADGE}</Badge>
        <span className="hidden text-sm text-ink-subtle sm:inline">
          {APP_HEADER_NOTE}
        </span>
        <Link
          href="/privacy"
          className="ml-auto inline-flex min-h-11 items-center text-xs text-ink-subtle underline underline-offset-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink"
        >
          개인정보처리방침
        </Link>
      </div>
      <p className="mx-auto max-w-6xl px-4 pb-2 text-xs text-ink-subtle sm:px-6">
        {APP_NO_BROKERAGE}
      </p>
    </header>
  );
}
