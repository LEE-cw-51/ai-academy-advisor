"use client";

import { useCallback, useMemo, useState } from "react";
import Link from "next/link";
import { trackEventSafe } from "@/lib/api";
import type { AiRecommendationItem } from "@/lib/types";
import { AcademyDetailModal } from "./AcademyDetailModal";
import { AppExploreHeader } from "./AppExploreHeader";
import { ChatPanel } from "./ChatPanel";
import { MapPanel } from "./MapPanel";
import {
  MAP_EMPTY_CANDIDATES,
  MAP_HEADING_CANDIDATES,
  SEARCH_MODE_LABEL,
} from "./exploreCopy";

export function AppShell() {
  const [recItems, setRecItems] = useState<AiRecommendationItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detailId, setDetailId] = useState<number | null>(null);
  // 상황 입력을 한 번이라도 제출하면 2열(후보·질문 | 지도)로 전환한다.
  const [hasExplored, setHasExplored] = useState(false);

  const mapAcademies = useMemo(
    () => recItems.map((item) => item.academy),
    [recItems],
  );

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

  // 학원 찾기는 /app/search 로 분리. 제목 옆(제출 후엔 조건 요약 줄)에 링크만 둔다.
  // SEARCH_MODE_LABEL 은 이 파일에 남겨 탐색 카피 테스트가 잡는다.
  const searchSlot = (
    <Link
      href="/app/search"
      className="inline-flex min-h-11 shrink-0 items-center self-end text-sm font-semibold text-ink-muted underline-offset-2 hover:text-ink hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink sm:self-start"
    >
      {SEARCH_MODE_LABEL}
    </Link>
  );

  return (
    <div className="flex min-h-dvh flex-col bg-canvas">
      <AppExploreHeader />

      {/* DOM 순서 = 모바일 순서: 상황 입력 → 상담 질문 → 후보 → 지도.
          제출 전에는 폼이 주인공(단열, 테두리 카드 없음). 제출 후에만 2열.
          lg+ 2열에서는 그리드를 뷰포트에 맞춰 높이 제한해 왼쪽만 스크롤하고
          오른쪽 지도는 옆에 고정한다. */}
      <main
        className={[
          "mx-auto grid w-full max-w-6xl flex-1 gap-6 p-4 sm:p-6",
          hasExplored
            ? "lg:h-[calc(100dvh-7.5rem)] lg:min-h-0 lg:grid-cols-2 lg:gap-8 lg:overflow-hidden"
            : "lg:max-w-xl",
        ].join(" ")}
      >
        <section
          aria-labelledby="explore-heading"
          className={[
            "flex min-h-0 flex-col",
            hasExplored ? "min-h-[420px] lg:min-h-0 lg:overflow-hidden" : "",
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
            searchSlot={searchSlot}
          />
        </section>

        {/* 지도는 조건 제출 뒤에만 — 후보 핀만 보여 준다. */}
        {hasExplored ? (
          <section
            aria-label={MAP_HEADING_CANDIDATES}
            className="flex min-h-[420px] flex-col gap-3 rounded-card bg-surface p-4 shadow-soft sm:p-5 lg:sticky lg:top-0 lg:min-h-0 lg:overflow-hidden"
          >
            <div className="flex min-h-0 flex-1 flex-col">
              <MapPanel
                academies={mapAcademies}
                heading={MAP_HEADING_CANDIDATES}
                emptyHint={MAP_EMPTY_CANDIDATES}
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
