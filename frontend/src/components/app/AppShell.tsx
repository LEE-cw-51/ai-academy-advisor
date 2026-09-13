"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui";
import { fetchAllAcademies, trackEventSafe } from "@/lib/api";
import type {
  AcademySummary,
  AiRecommendationItem,
} from "@/lib/types";
import { AcademyDetailModal } from "./AcademyDetailModal";
import { ChatPanel } from "./ChatPanel";
import { MapPanel } from "./MapPanel";
import {
  APP_BADGE,
  APP_HEADER_NOTE,
  APP_NO_BROKERAGE,
  APP_TITLE,
  BACK_TO_CANDIDATES_LABEL,
  MAP_EMPTY_CANDIDATES,
  MAP_HEADING_CANDIDATES,
  MAP_HEADING_SEARCH,
  SEARCH_CLEAR_LABEL,
  SEARCH_ERROR,
  SEARCH_HELPER,
  SEARCH_LABEL,
  SEARCH_MODE_HIDE_LABEL,
  SEARCH_MODE_LABEL,
  SEARCH_OVERRIDES_CANDIDATES,
  SEARCH_PLACEHOLDER,
  searchNoResults,
  searchResultCount,
} from "./exploreCopy";

// 지도가 지금 무엇을 보여 주는지. 한 흐름(상황 입력 → 후보·질문 → 후보 핀)이
// 기본이고, 키워드 검색은 아는 학원을 이름·주소·전화로 찾는 보조다.
// 제출 전·검색 전에는 지도를 그리지 않는다(입력이 주인공). 제출 뒤(로딩·후보 0건
// 포함)는 candidates, 검색어가 살아 있으면 search.
type MapMode = "candidates" | "search";

const MAP_HEADINGS: Record<MapMode, string> = {
  candidates: MAP_HEADING_CANDIDATES,
  search: MAP_HEADING_SEARCH,
};

// 검색을 끄면 후보 핀을 되돌린다. 기존 선택이 후보에 남아 있으면 유지,
// 없으면 첫 후보, 후보가 없으면 null. 빈 검색과 '후보로 돌아가기'가 같은 규칙을 쓴다.
function nextCandidateSelectedId(
  recItems: AiRecommendationItem[],
  prev: number | null,
): number | null {
  if (recItems.length === 0) {
    return null;
  }
  if (prev !== null && recItems.some((item) => item.academy.id === prev)) {
    return prev;
  }
  return recItems[0]?.academy.id ?? null;
}

export function AppShell() {
  const [listAcademies, setListAcademies] = useState<AcademySummary[]>([]);
  const [recItems, setRecItems] = useState<AiRecommendationItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [listError, setListError] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [activeQuery, setActiveQuery] = useState("");
  const [searchTotal, setSearchTotal] = useState<number | null>(null);
  const [searching, setSearching] = useState(false);
  // 학원 찾기는 접힌 보조 도구다. 토글로 열거나 검색어가 살아 있는 동안만 보인다.
  const [searchOpen, setSearchOpen] = useState(false);
  const [detailId, setDetailId] = useState<number | null>(null);
  // 상황 입력을 한 번이라도 제출하면 2열(후보·질문 | 지도)로 전환한다.
  const [hasExplored, setHasExplored] = useState(false);

  // 검색 요청 일련번호. 최신 요청만 상태에 반영한다 — 검색 해제(searchSeq 증가)
  // 뒤에 도착한 응답이 방금 지운 검색 결과를 되살리거나, 연속 검색 두 개가
  // 순서를 뒤바꿔 도착하는 것을 막는다.
  const searchSeq = useRef(0);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // 토글로 검색창을 열면 포커스를 입력으로 옮긴다. 데이터 fetch 는 없다.
  useEffect(() => {
    if (searchOpen) searchInputRef.current?.focus();
  }, [searchOpen]);

  // 키워드 검색만 GET /academies?q= 를 친다. 빈 q로 전체 목록을 올리지 않는다.
  const runSearch = useCallback(async (raw: string) => {
    const q = raw.trim();
    const seq = ++searchSeq.current;
    if (!q) {
      setListAcademies([]);
      setActiveQuery("");
      setSearchTotal(null);
      setListError("");
      setSelectedId((prev) => nextCandidateSelectedId(recItems, prev));
      setSearching(false);
      return;
    }
    setSearching(true);
    try {
      const res = await fetchAllAcademies({ q });
      if (seq !== searchSeq.current) return;
      setListAcademies(res.items);
      setActiveQuery(q);
      setSearchTotal(res.total);
      setListError("");
      // 선택된 학원이 검색 결과에서 사라지면 지도 선택을 해제한다.
      setSelectedId((prev) =>
        prev !== null && !res.items.some((a) => a.id === prev) ? null : prev,
      );
    } catch {
      if (seq !== searchSeq.current) return;
      setListError(SEARCH_ERROR);
    } finally {
      if (seq === searchSeq.current) setSearching(false);
    }
  }, [recItems]);

  const hasCandidates = recItems.length > 0;
  const mapMode: MapMode = activeQuery ? "search" : "candidates";
  const searchVisible = searchOpen || Boolean(activeQuery);

  const mapAcademies = useMemo(() => {
    // 키워드 검색이 활성일 땐 검색 결과가 지도를 차지한다.
    // 검색을 해제하면 AI 후보(recItems)가 있으면 그쪽으로 돌아간다.
    if (!activeQuery && recItems.length > 0) {
      return recItems.map((item) => item.academy);
    }
    return listAcademies;
  }, [activeQuery, recItems, listAcademies]);

  const onResults = useCallback((items: AiRecommendationItem[]) => {
    setRecItems(items);
  }, []);

  const onExplored = useCallback(() => {
    setHasExplored(true);
  }, []);

  const onSelect = useCallback((id: number | null) => {
    setSelectedId(id);
  }, []);

  // 상세 모달로 오는 경로는 둘(후보 카드 상세 버튼 · 지도 목록 카드)이고 둘 다 여기를
  // 지난다. detail 계측을 여기 두면 두 경로가 같은 수를 남긴다 — 호출부마다 붙이면
  // 한쪽을 빠뜨려 퍼널이 과소 집계된다.
  const onOpenDetail = useCallback((id: number) => {
    setSelectedId(id);
    setDetailId(id);
    void trackEventSafe(id, "detail");
  }, []);

  const closeDetail = useCallback(() => setDetailId(null), []);

  const onSearchClear = useCallback(() => {
    // 진행 중인 검색 응답을 무효화한다 — 해제 후 도착해도 상태를 덮지 않는다.
    searchSeq.current += 1;
    setSearching(false);
    setSearchInput("");
    setListAcademies([]);
    setActiveQuery("");
    setSearchTotal(null);
    setListError("");
    setSearchOpen(false);
    setSelectedId((prev) => nextCandidateSelectedId(recItems, prev));
  }, [recItems]);

  const onSearchSubmit = useCallback(
    (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      if (!searchInput.trim()) {
        onSearchClear();
        return;
      }
      void runSearch(searchInput);
    },
    [runSearch, searchInput, onSearchClear],
  );

  // 검색 결과가 지도를 덮고 있을 때 '닫기'는 후보로 돌아가기와 같다 — 접기만 하면
  // 검색 결과는 지도에 남은 채 토글만 닫힌 상태가 된다.
  const onSearchToggle = useCallback(() => {
    if (searchOpen && activeQuery) {
      onSearchClear();
      return;
    }
    setSearchOpen((open) => !open);
  }, [searchOpen, activeQuery, onSearchClear]);

  const dualColumn = hasExplored || Boolean(activeQuery);

  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <header className="border-b border-border bg-surface/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-3 sm:px-6">
          <Link
            href="/"
            aria-label="학원콕 홈"
            className="text-lg font-black text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
          >
            {APP_TITLE}
          </Link>
          <Badge tone="brand">{APP_BADGE}</Badge>
          <span className="hidden text-sm text-ink-subtle sm:inline">
            {APP_HEADER_NOTE}
          </span>
          <Link
            href="/privacy"
            className="ml-auto inline-flex min-h-11 items-center text-xs text-ink-subtle underline underline-offset-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
          >
            개인정보처리방침
          </Link>
        </div>
        <p className="mx-auto max-w-6xl px-4 pb-2 text-xs text-ink-subtle sm:px-6">
          {APP_NO_BROKERAGE}
        </p>
      </header>

      {listError ? (
        <div
          role="alert"
          aria-live="assertive"
          className="border-b border-warn/30 bg-warn-bg px-4 py-2 text-center text-sm text-warn"
        >
          {listError}
        </div>
      ) : null}

      {/* DOM 순서 = 모바일 순서: 상황 입력 → 후보·질문 → 학원 찾기·지도.
          제출 전에는 폼이 주인공(단열)이고 지도는 그리지 않는다. 제출·검색 후에만 2열.
          lg+ 2열에서는 그리드를 뷰포트에 맞춰 높이 제한해 왼쪽만 스크롤하고
          오른쪽 지도는 계속 보이게 한다. */}
      <main
        className={[
          "mx-auto grid w-full max-w-6xl flex-1 gap-4 p-4 sm:p-6",
          dualColumn
            ? "lg:h-[calc(100dvh-7.5rem)] lg:min-h-0 lg:grid-cols-2 lg:gap-6 lg:overflow-hidden"
            : "lg:max-w-2xl",
        ].join(" ")}
      >
        <section
          aria-labelledby="explore-heading"
          className={[
            "flex min-h-0 flex-col rounded-card border border-border-soft bg-surface p-4 shadow-card sm:p-5",
            dualColumn ? "min-h-[420px] lg:min-h-0 lg:overflow-hidden" : "",
          ]
            .filter(Boolean)
            .join(" ")}
        >
          <ChatPanel
            onResults={onResults}
            onExplored={onExplored}
            onSelectAcademy={onSelect}
            selectedAcademyId={selectedId}
            onOpenDetail={onOpenDetail}
          />
        </section>

        {/* 보조 패널: 아는 학원 찾기(접힘) + 제출·검색 뒤에만 그리는 지도.
            제출 전·검색 닫힘 상태에선 카드 없이 토글 한 줄만 둔다. */}
        <section
          aria-label={SEARCH_MODE_LABEL}
          className={[
            "flex min-h-0 flex-col gap-3",
            dualColumn || searchVisible
              ? "rounded-card border border-border-soft bg-surface p-4 shadow-card sm:p-5"
              : "",
            dualColumn ? "min-h-[420px] lg:min-h-0 lg:overflow-hidden" : "",
          ]
            .filter(Boolean)
            .join(" ")}
        >
          <h2 className="sr-only">{SEARCH_MODE_LABEL}</h2>
          <button
            type="button"
            aria-expanded={searchOpen}
            aria-controls="academy-search"
            onClick={onSearchToggle}
            className="inline-flex min-h-11 items-center self-start text-sm font-semibold text-ink-muted underline-offset-2 hover:text-ink hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
          >
            {searchOpen ? SEARCH_MODE_HIDE_LABEL : SEARCH_MODE_LABEL}
          </button>

          {searchVisible ? (
            <div id="academy-search" className="space-y-2">
              <form onSubmit={onSearchSubmit} className="flex gap-2">
                <input
                  ref={searchInputRef}
                  type="search"
                  value={searchInput}
                  onChange={(event) => setSearchInput(event.target.value)}
                  placeholder={SEARCH_PLACEHOLDER}
                  aria-label={SEARCH_LABEL}
                  autoComplete="off"
                  className="min-h-11 min-w-0 flex-1 rounded-full border border-border bg-surface px-4 text-sm text-ink placeholder:text-ink-subtle focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/30 disabled:opacity-60"
                />
                <button
                  type="submit"
                  disabled={searching}
                  className="min-h-11 rounded-full bg-surface-subtle px-4 text-sm font-bold text-ink transition-colors hover:bg-brand hover:text-ink-strong focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {SEARCH_LABEL}
                </button>
              </form>
              <p className="text-xs text-ink-subtle">{SEARCH_HELPER}</p>
              {activeQuery ? (
                <p className="flex flex-wrap items-center gap-2 text-xs text-ink-subtle">
                  <span className="break-words">
                    {searchTotal === 0
                      ? searchNoResults(activeQuery)
                      : searchResultCount(searchTotal ?? listAcademies.length)}
                  </span>
                  {hasCandidates ? (
                    <span>{SEARCH_OVERRIDES_CANDIDATES}</span>
                  ) : null}
                  <button
                    type="button"
                    onClick={onSearchClear}
                    className="inline-flex min-h-11 items-center underline underline-offset-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
                  >
                    {hasCandidates ? BACK_TO_CANDIDATES_LABEL : SEARCH_CLEAR_LABEL}
                  </button>
                </p>
              ) : null}
            </div>
          ) : null}

          {hasExplored || activeQuery ? (
            <div className="flex min-h-0 flex-1 flex-col">
              <MapPanel
                academies={mapAcademies}
                heading={MAP_HEADINGS[mapMode]}
                emptyHint={mapMode === "candidates" ? MAP_EMPTY_CANDIDATES : undefined}
                selectedId={selectedId}
                onSelect={onSelect}
                onOpenDetail={onOpenDetail}
                hideList={mapMode === "candidates"}
              />
            </div>
          ) : null}
        </section>
      </main>

      <AcademyDetailModal
        academyId={detailId}
        onClose={closeDetail}
        onTrack={(academyId, event) => void trackEventSafe(academyId, event)}
      />
    </div>
  );
}
