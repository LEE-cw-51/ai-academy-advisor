"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchAcademies } from "@/lib/api";
import type { AcademySummary, AiRecommendationItem } from "@/lib/types";
import { ChatPanel } from "./ChatPanel";
import { MapPanel } from "./MapPanel";

export function AppShell() {
  const [listAcademies, setListAcademies] = useState<AcademySummary[]>([]);
  const [recItems, setRecItems] = useState<AiRecommendationItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [listError, setListError] = useState("");

  useEffect(() => {
    let cancelled = false;
    fetchAcademies({ limit: 50 })
      .then((res) => {
        if (cancelled) return;
        setListAcademies(res.items);
        setListError("");
      })
      .catch(() => {
        if (cancelled) return;
        setListError(
          "학원 목록을 불러오지 못했어요. API(NEXT_PUBLIC_API_URL)를 확인해 주세요.",
        );
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const mapAcademies = useMemo(() => {
    if (recItems.length > 0) {
      return recItems.map((item) => item.academy);
    }
    return listAcademies;
  }, [recItems, listAcademies]);

  const onResults = useCallback((items: AiRecommendationItem[]) => {
    setRecItems(items);
  }, []);

  const onSelect = useCallback((id: number | null) => {
    setSelectedId(id);
  }, []);

  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <header className="border-b border-border bg-surface/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-3 sm:px-6">
          <span className="text-lg font-black text-ink">학원콕</span>
          <span className="hidden text-sm text-ink-subtle sm:inline">
            AI 추천 · 하남 미사
          </span>
        </div>
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
          <MapPanel
            academies={mapAcademies}
            selectedId={selectedId}
            onSelect={(id) => setSelectedId(id)}
          />
        </section>
      </div>
    </div>
  );
}
