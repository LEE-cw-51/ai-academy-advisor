"use client";

import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Badge, Button, Card } from "@/components/ui";
import { fetchAllAcademies, trackEventSafe } from "@/lib/api";
import type { AcademySummary } from "@/lib/types";
import { AcademyDetailModal } from "./AcademyDetailModal";
import { AppExploreHeader } from "./AppExploreHeader";
import { MapPanel } from "./MapPanel";
import {
  BACK_TO_CONDITIONS_LABEL,
  MAP_HEADING_SEARCH,
  SEARCH_ERROR,
  SEARCH_HELPER,
  SEARCH_LABEL,
  SEARCH_MODE_LABEL,
  SEARCH_PLACEHOLDER,
  searchNoResults,
  searchResultCount,
  subjectBadges,
} from "./exploreCopy";

function AcademySearchContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const urlQ = (searchParams.get("q") ?? "").trim();

  const [searchInput, setSearchInput] = useState(urlQ);
  const [results, setResults] = useState<AcademySummary[]>([]);
  const [activeQuery, setActiveQuery] = useState("");
  const [searchTotal, setSearchTotal] = useState<number | null>(null);
  const [searching, setSearching] = useState(false);
  const [listError, setListError] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detailId, setDetailId] = useState<number | null>(null);

  // 검색 요청 일련번호. 최신 요청만 상태에 반영한다 — 연속 검색 두 개가
  // 순서를 뒤바꿔 도착하는 것을 막는다.
  const searchSeq = useRef(0);

  // 키워드 검색만 GET /academies?q= 를 친다. 빈 q로 전체 목록을 올리지 않는다.
  const runSearch = useCallback(async (raw: string) => {
    const q = raw.trim();
    const seq = ++searchSeq.current;
    if (!q) {
      setResults([]);
      setActiveQuery("");
      setSearchTotal(null);
      setListError("");
      setSearching(false);
      return;
    }
    setResults([]);
    setActiveQuery("");
    setSearchTotal(null);
    setListError("");
    setSelectedId(null);
    setSearching(true);
    try {
      const res = await fetchAllAcademies({ q });
      if (seq !== searchSeq.current) return;
      setResults(res.items);
      setActiveQuery(q);
      setSearchTotal(res.total);
      setListError("");
      setSelectedId((prev) =>
        prev !== null && !res.items.some((a) => a.id === prev) ? null : prev,
      );
    } catch {
      if (seq !== searchSeq.current) return;
      setResults([]);
      setActiveQuery("");
      setSearchTotal(null);
      setSelectedId(null);
      setListError(SEARCH_ERROR);
    } finally {
      if (seq === searchSeq.current) setSearching(false);
    }
  }, []);

  // ?q= 가 이미 있으면 그 값으로 한 번 조회. 빈 q로는 요청하지 않는다.
  useEffect(() => {
    setSearchInput(urlQ);
    void runSearch(urlQ);
  }, [urlQ, runSearch]);

  const onSearchSubmit = useCallback(
    (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      const q = searchInput.trim();
      if (!q) return;
      // 주소에 ?q= 를 남긴다. 같은 q 면 URL 이 안 바뀌어 effect 가 안 도므로 직접 조회.
      if (q === urlQ) {
        void runSearch(q);
        return;
      }
      router.push(`/app/search?q=${encodeURIComponent(q)}`);
    },
    [searchInput, urlQ, router, runSearch],
  );

  const onSelect = useCallback((id: number | null) => {
    setSelectedId(id);
  }, []);

  const onOpenDetail = useCallback((id: number) => {
    setSelectedId(id);
    setDetailId(id);
    void trackEventSafe(id, "detail");
  }, []);

  const closeDetail = useCallback(() => setDetailId(null), []);

  const hasResults = results.length > 0;

  return (
    <div className="flex min-h-dvh flex-col bg-canvas">
      <AppExploreHeader />

      {listError ? (
        <div
          role="alert"
          aria-live="assertive"
          className="border-b border-warn/30 bg-warn-bg px-4 py-2 text-center text-sm text-warn"
        >
          {listError}
        </div>
      ) : null}

      <main
        className={[
          "mx-auto grid w-full max-w-6xl flex-1 gap-6 p-4 sm:p-6",
          hasResults
            ? "lg:h-[calc(100dvh-7.5rem)] lg:min-h-0 lg:grid-cols-2 lg:gap-8 lg:overflow-hidden"
            : "lg:max-w-xl",
        ].join(" ")}
      >
        {/* /app 과 같이: 왼쪽=입력·목록, 오른쪽=지도. 결과 전엔 폼만(단열).
            min-h-[420px] 를 폼 칸에 두지 않는다 — 모바일에서 폼·지도 사이 빈 칸이 생긴다. */}
        <section
          aria-labelledby="academy-search-heading"
          className={[
            "flex min-h-0 flex-col gap-4",
            hasResults ? "lg:min-h-0 lg:overflow-hidden" : "",
          ]
            .filter(Boolean)
            .join(" ")}
        >
          <div className="space-y-2">
            <div className="flex flex-col gap-1 sm:flex-row sm:flex-wrap sm:items-start sm:justify-between sm:gap-x-3">
              <h1
                id="academy-search-heading"
                className="w-full break-keep text-2xl font-semibold leading-snug text-ink sm:min-w-0 sm:flex-1 sm:text-3xl"
              >
                {SEARCH_MODE_LABEL}
              </h1>
              <Link
                href="/app"
                className="inline-flex min-h-11 shrink-0 items-center self-start text-sm font-semibold text-ink-muted underline-offset-2 hover:text-ink hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink"
              >
                {BACK_TO_CONDITIONS_LABEL}
              </Link>
            </div>
            <p className="text-xs text-ink-subtle">{SEARCH_HELPER}</p>
          </div>

          <form onSubmit={onSearchSubmit} className="flex gap-2">
            <input
              type="search"
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder={SEARCH_PLACEHOLDER}
              aria-label={SEARCH_LABEL}
              autoComplete="off"
              className="min-h-11 min-w-0 flex-1 rounded-full border border-border bg-surface px-4 text-sm text-ink placeholder:text-ink-subtle focus:border-ink/40 focus:outline-none focus:ring-2 focus:ring-ink/15 disabled:opacity-60"
            />
            <Button
              type="submit"
              variant="secondary"
              disabled={searching}
              aria-live="polite"
              className="shrink-0 rounded-full px-5"
            >
              {searching ? "검색 중…" : SEARCH_LABEL}
            </Button>
          </form>

          {activeQuery ? (
            <p className="break-words text-xs text-ink-subtle">
              {searchTotal === 0
                ? searchNoResults(activeQuery)
                : searchResultCount(searchTotal ?? results.length)}
            </p>
          ) : null}

          {hasResults ? (
            <ul className="min-h-0 flex-1 space-y-2 overflow-y-auto pb-1">
              {results.map((a) => (
                <li key={a.id}>
                  <Card
                    padding="sm"
                    className={[
                      "cursor-pointer transition-shadow hover:shadow-soft",
                      selectedId === a.id ? "ring-2 ring-brand" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    onActivate={() => onOpenDetail(a.id)}
                  >
                    <div className="flex flex-wrap items-center gap-1.5">
                      <p className="font-medium text-ink">{a.name}</p>
                      {subjectBadges(a.subjects, a.subject_detail).map((s) => (
                        <Badge key={s}>{s}</Badge>
                      ))}
                    </div>
                    {a.address ? (
                      <p className="mt-0.5 text-xs text-ink-subtle">{a.address}</p>
                    ) : null}
                    {a.phone ? (
                      <p className="mt-0.5 text-xs text-ink-subtle">{a.phone}</p>
                    ) : null}
                  </Card>
                </li>
              ))}
            </ul>
          ) : null}
        </section>

        {hasResults ? (
          <section
            aria-label={MAP_HEADING_SEARCH}
            className="flex min-h-[320px] flex-col gap-3 rounded-card bg-surface p-4 shadow-soft sm:min-h-[420px] sm:p-5 lg:sticky lg:top-0 lg:min-h-0 lg:overflow-hidden"
          >
            <div className="flex min-h-0 flex-1 flex-col">
              <MapPanel
                academies={results}
                heading={MAP_HEADING_SEARCH}
                selectedId={selectedId}
                onSelect={onSelect}
                onOpenDetail={onOpenDetail}
                hideList
              />
            </div>
          </section>
        ) : null}
      </main>

      <AcademyDetailModal
        academyId={detailId}
        onClose={closeDetail}
        onTrack={(academyId, event) => void trackEventSafe(academyId, event)}
      />
    </div>
  );
}

/** `/app/search` — 이름·주소·전화로 아는 학원을 찾는다. */
export function AcademySearchPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-dvh flex-col bg-canvas">
          <AppExploreHeader />
          <main className="mx-auto w-full max-w-xl flex-1 p-4 sm:p-6">
            <h1 className="break-keep text-2xl font-semibold text-ink sm:text-3xl">
              {SEARCH_MODE_LABEL}
            </h1>
          </main>
        </div>
      }
    >
      <AcademySearchContent />
    </Suspense>
  );
}
