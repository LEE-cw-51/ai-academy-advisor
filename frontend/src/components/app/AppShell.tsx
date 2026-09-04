"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui";
import { fetchAllAcademies } from "@/lib/api";
import type { AcademySummary, AiRecommendationItem } from "@/lib/types";
import { ChatPanel } from "./ChatPanel";
import { MapPanel } from "./MapPanel";
import {
  APP_BADGE,
  APP_HEADER_NOTE,
  APP_NO_BROKERAGE,
  APP_TITLE,
  SEARCH_CLEAR_LABEL,
  SEARCH_ERROR,
  SEARCH_LABEL,
  SEARCH_NO_RESULTS,
  SEARCH_PLACEHOLDER,
  searchResultCount,
} from "./exploreCopy";

const LIST_ERROR =
  "학원 목록을 불러오지 못했어요. API(NEXT_PUBLIC_API_URL)를 확인해 주세요.";

export function AppShell() {
  const [listAcademies, setListAcademies] = useState<AcademySummary[]>([]);
  const [recItems, setRecItems] = useState<AiRecommendationItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [listError, setListError] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [activeQuery, setActiveQuery] = useState("");
  const [searchTotal, setSearchTotal] = useState<number | null>(null);
  const [searching, setSearching] = useState(false);

  // 초기 로드와 키워드 검색이 같은 경로를 쓴다 — GET /academies(?q=).
  // 최신 응답이 이긴다(늦게 온 이전 요청이 덮어써도 다음 검색으로 복구 가능한 MVP 동작).
  const runSearch = useCallback(async (raw: string) => {
    const q = raw.trim();
    setSearching(true);
    try {
      const res = await fetchAllAcademies(q ? { q } : undefined);
      setListAcademies(res.items);
      setActiveQuery(q);
      setSearchTotal(q ? res.total : null);
      setListError("");
      // 선택된 학원이 검색 결과에서 사라지면 지도 선택을 해제한다.
      setSelectedId((prev) =>
        prev !== null && !res.items.some((a) => a.id === prev) ? null : prev,
      );
    } catch {
      setListError(q ? SEARCH_ERROR : LIST_ERROR);
    } finally {
      setSearching(false);
    }
  }, []);

  useEffect(() => {
    void runSearch("");
  }, [runSearch]);

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

  const onSelect = useCallback((id: number | null) => {
    setSelectedId(id);
  }, []);

  const onSearchSubmit = useCallback(
    (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      void runSearch(searchInput);
    },
    [runSearch, searchInput],
  );

  const onSearchClear = useCallback(() => {
    setSearchInput("");
    void runSearch("");
  }, [runSearch]);

  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <header className="border-b border-border bg-surface/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-3 sm:px-6">
          <span className="text-lg font-black text-ink">{APP_TITLE}</span>
          <Badge tone="brand">{APP_BADGE}</Badge>
          <span className="hidden text-sm text-ink-subtle sm:inline">
            {APP_HEADER_NOTE}
          </span>
          <Link
            href="/privacy"
            className="ml-auto text-xs text-ink-subtle underline underline-offset-2"
          >
            개인정보처리방침
          </Link>
        </div>
        <p className="mx-auto max-w-6xl px-4 pb-2 text-xs text-ink-subtle sm:px-6">
          {APP_NO_BROKERAGE}
        </p>
      </header>

      {listError ? (
        <div className="border-b border-warn/30 bg-warn-bg px-4 py-2 text-center text-sm text-warn">
          {listError}
        </div>
      ) : null}

      <div className="mx-auto grid w-full max-w-6xl flex-1 gap-4 p-4 sm:p-6 lg:grid-cols-2 lg:gap-6">
        <section className="min-h-[420px] rounded-card border border-border-soft bg-surface p-4 shadow-card sm:p-5">
          <ChatPanel
            onResults={onResults}
            onSelectAcademy={onSelect}
            selectedAcademyId={selectedId}
          />
        </section>
        <section className="min-h-[420px] rounded-card border border-border-soft bg-surface p-4 shadow-card sm:p-5">
          <form onSubmit={onSearchSubmit} className="mb-3 flex gap-2">
            <input
              type="search"
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder={SEARCH_PLACEHOLDER}
              aria-label={SEARCH_LABEL}
              className="min-w-0 flex-1 rounded-full border border-border bg-surface px-4 py-2 text-sm text-ink placeholder:text-ink-subtle focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/30 disabled:opacity-60"
            />
            <button
              type="submit"
              disabled={searching}
              className="rounded-full bg-surface-subtle px-4 py-2 text-sm font-bold text-ink transition-colors hover:bg-brand hover:text-ink-strong disabled:cursor-not-allowed disabled:opacity-40"
            >
              {SEARCH_LABEL}
            </button>
          </form>
          {activeQuery ? (
            <p className="mb-2 flex flex-wrap items-center gap-2 text-xs text-ink-subtle">
              <span>
                {searchTotal === 0
                  ? SEARCH_NO_RESULTS
                  : searchResultCount(searchTotal ?? listAcademies.length)}
              </span>
              <button
                type="button"
                onClick={onSearchClear}
                className="underline underline-offset-2"
              >
                {SEARCH_CLEAR_LABEL}
              </button>
            </p>
          ) : null}
          <MapPanel
            academies={mapAcademies}
            selectedId={selectedId}
            onSelect={onSelect}
          />
        </section>
      </div>
    </div>
  );
}
