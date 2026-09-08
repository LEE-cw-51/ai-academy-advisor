"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui";
import { fetchAllAcademies, trackEvent } from "@/lib/api";
import type {
  AcademySummary,
  AiRecommendationItem,
  ClickEventType,
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
  MAP_EMPTY_HINT,
  MAP_HEADING_CANDIDATES,
  MAP_HEADING_IDLE,
  MAP_HEADING_SEARCH,
  SEARCH_CLEAR_LABEL,
  SEARCH_ERROR,
  SEARCH_HELPER,
  SEARCH_LABEL,
  SEARCH_OVERRIDES_CANDIDATES,
  SEARCH_PLACEHOLDER,
  searchNoResults,
  searchResultCount,
} from "./exploreCopy";

// 지도가 지금 무엇을 보여 주는지. 한 흐름(상황 입력 → 질문·후보 → 후보 핀)이
// 기본이고, 키워드 검색은 아는 학원을 이름·주소·전화로 찾는 보조다.
// idle: 제출 전(또는 검색·후보 없음) — 마커 없이 빈 지도.
type MapMode = "idle" | "candidates" | "search";

const MAP_HEADINGS: Record<MapMode, string> = {
  idle: MAP_HEADING_IDLE,
  candidates: MAP_HEADING_CANDIDATES,
  search: MAP_HEADING_SEARCH,
};

// 컴포넌트 state 를 안 쓰므로 모듈 스코프에 둔다 — useCallback 의존성에서 자유롭다.
async function handleTrack(academyId: number, event: ClickEventType) {
  try {
    await trackEvent({ academy_id: academyId, event });
  } catch {
    // tracking should not block UX
  }
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
  const [detailId, setDetailId] = useState<number | null>(null);
  // 상황 입력을 한 번이라도 제출하면 2열(질문·후보 | 지도)로 전환한다.
  const [hasExplored, setHasExplored] = useState(false);

  // 검색 요청 일련번호. 최신 요청만 상태에 반영한다 — 검색 해제(searchSeq 증가)
  // 뒤에 도착한 응답이 방금 지운 검색 결과를 되살리거나, 연속 검색 두 개가
  // 순서를 뒤바꿔 도착하는 것을 막는다.
  const searchSeq = useRef(0);

  // 키워드 검색만 GET /academies?q= 를 친다. 빈 q로 전체 목록을 올리지 않는다.
  const runSearch = useCallback(async (raw: string) => {
    const q = raw.trim();
    const seq = ++searchSeq.current;
    if (!q) {
      setListAcademies([]);
      setActiveQuery("");
      setSearchTotal(null);
      setListError("");
      setSelectedId(null);
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
  }, []);

  const hasCandidates = recItems.length > 0;
  const mapMode: MapMode = activeQuery
    ? "search"
    : hasCandidates
      ? "candidates"
      : "idle";

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
    void handleTrack(id, "detail");
  }, []);

  const closeDetail = useCallback(() => setDetailId(null), []);

  const onSearchSubmit = useCallback(
    (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      void runSearch(searchInput);
    },
    [runSearch, searchInput],
  );

  const onSearchClear = useCallback(() => {
    // 진행 중인 검색 응답을 무효화한다 — 해제 후 도착해도 상태를 덮지 않는다.
    searchSeq.current += 1;
    setSearching(false);
    setSearchInput("");
    setListAcademies([]);
    setActiveQuery("");
    setSearchTotal(null);
    setListError("");
    if (recItems.length > 0) {
      setSelectedId((prev) => {
        if (prev !== null && recItems.some((item) => item.academy.id === prev)) {
          return prev;
        }
        return recItems[0]?.academy.id ?? null;
      });
      return;
    }
    setSelectedId(null);
  }, [recItems]);

  const dualColumn = hasExplored || hasCandidates || Boolean(activeQuery);

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

      {/* DOM 순서 = 모바일 순서: 상황 입력 → 질문·후보 → 지도·검색.
          제출 전에는 폼이 주인공(단열), 제출·검색 후에만 2열. */}
      <div
        className={[
          "mx-auto grid w-full max-w-6xl flex-1 gap-4 p-4 sm:p-6",
          dualColumn ? "lg:grid-cols-2 lg:gap-6" : "lg:max-w-2xl",
        ].join(" ")}
      >
        <section
          className={[
            "rounded-card border border-border-soft bg-surface p-4 shadow-card sm:p-5",
            dualColumn ? "min-h-[420px]" : "",
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
        <section
          className={[
            "rounded-card border border-border-soft bg-surface p-4 shadow-card sm:p-5",
            dualColumn ? "min-h-[420px]" : "min-h-[280px]",
          ].join(" ")}
        >
          <MapPanel
            academies={mapAcademies}
            heading={MAP_HEADINGS[mapMode]}
            emptyHint={mapMode === "idle" ? MAP_EMPTY_HINT : undefined}
            selectedId={selectedId}
            onSelect={onSelect}
            onOpenDetail={onOpenDetail}
          >
            <form onSubmit={onSearchSubmit} className="flex gap-2">
              <input
                type="search"
                value={searchInput}
                onChange={(event) => setSearchInput(event.target.value)}
                placeholder={SEARCH_PLACEHOLDER}
                aria-label={SEARCH_LABEL}
                className="min-w-0 flex-1 rounded-full border border-border bg-surface px-4 py-1.5 text-sm text-ink placeholder:text-ink-subtle focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/30 disabled:opacity-60"
              />
              <button
                type="submit"
                disabled={searching}
                className="rounded-full bg-surface-subtle px-4 py-1.5 text-sm font-bold text-ink transition-colors hover:bg-brand hover:text-ink-strong disabled:cursor-not-allowed disabled:opacity-40"
              >
                {SEARCH_LABEL}
              </button>
            </form>
            <p className="text-xs text-ink-subtle">{SEARCH_HELPER}</p>
            {activeQuery ? (
              <p className="flex flex-wrap items-center gap-2 text-xs text-ink-subtle">
                <span>
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
                  className="underline underline-offset-2"
                >
                  {hasCandidates ? BACK_TO_CANDIDATES_LABEL : SEARCH_CLEAR_LABEL}
                </button>
              </p>
            ) : null}
          </MapPanel>
        </section>
      </div>

      <AcademyDetailModal
        academyId={detailId}
        onClose={closeDetail}
        onTrack={(academyId, event) => void handleTrack(academyId, event)}
      />
    </div>
  );
}
