"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { Badge, Card } from "@/components/ui";
import type { AcademySummary } from "@/lib/types";
import { MAP_EMPTY_LIST } from "./exploreCopy";

type NaverMapInstance = {
  setCenter: (latLng: unknown) => void;
  destroy: () => void;
};

type NaverMarkerInstance = {
  setMap: (map: unknown | null) => void;
};

declare global {
  interface Window {
    naver?: {
      maps: {
        Map: new (
          el: HTMLElement,
          opts: {
            center: unknown;
            zoom: number;
          },
        ) => NaverMapInstance;
        LatLng: new (lat: number, lng: number) => unknown;
        Marker: new (opts: {
          position: unknown;
          map: unknown;
          title?: string;
        }) => NaverMarkerInstance;
        Event: {
          addListener: (
            target: unknown,
            event: string,
            handler: () => void,
          ) => void;
        };
      };
    };
  }
}

const HANAM_CENTER = { lat: 37.56015, lng: 127.1866 };

interface MapPanelProps {
  academies: AcademySummary[];
  /** 지도가 지금 무엇을 보여 주는지 — 대기 / 후보 위치 / 검색 결과. */
  heading: string;
  /** 목록이 비었을 때 지도·리스트에 보여 줄 안내 (제출 전 빈 지도 등). */
  emptyHint?: string;
  selectedId: number | null;
  onSelect: (id: number) => void;
  onOpenDetail: (id: number) => void;
  /** 헤딩과 지도 사이에 들어가는 보조 도구(키워드 검색 등). */
  children?: ReactNode;
}

const SCRIPT_TIMEOUT_MS = 10_000;

function loadNaverScript(clientId: string): Promise<void> {
  const existing = document.getElementById("naver-maps-script");
  if (existing && window.naver?.maps) {
    return Promise.resolve();
  }
  return new Promise((resolve, reject) => {
    // 이미 load/error가 발화한 뒤에 리스너를 붙이면 영원히 대기하게 되므로
    // 어느 경로로든 반드시 결론이 나도록 타임아웃을 함께 건다.
    const timer = window.setTimeout(() => {
      if (window.naver?.maps) {
        resolve();
      } else {
        reject(new Error("Naver Maps script timed out"));
      }
    }, SCRIPT_TIMEOUT_MS);

    const done = (fn: () => void) => () => {
      window.clearTimeout(timer);
      fn();
    };
    const onLoad = done(resolve);
    const onError = done(() =>
      reject(new Error("Naver Maps script failed")),
    );

    if (existing) {
      existing.addEventListener("load", onLoad);
      existing.addEventListener("error", onError);
      return;
    }
    const script = document.createElement("script");
    script.id = "naver-maps-script";
    script.src = `https://oapi.map.naver.com/openapi/v3/maps.js?ncpKeyId=${encodeURIComponent(clientId)}`;
    script.async = true;
    script.onload = onLoad;
    script.onerror = onError;
    document.head.appendChild(script);
  });
}

export function MapPanel({
  academies,
  heading,
  emptyHint,
  selectedId,
  onSelect,
  onOpenDetail,
  children,
}: MapPanelProps) {
  const clientId = process.env.NEXT_PUBLIC_NAVER_MAP_CLIENT_ID?.trim() ?? "";
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<NaverMapInstance | null>(null);
  const markersRef = useRef<{ id: number; marker: NaverMarkerInstance }[]>([]);
  const [mapReady, setMapReady] = useState(false);
  const [mapError, setMapError] = useState(false);

  // 마커 클릭 핸들러가 onSelect 변경 때문에 마커를 재생성하지 않도록 ref로 잡아둔다.
  const onSelectRef = useRef(onSelect);
  useEffect(() => {
    onSelectRef.current = onSelect;
  }, [onSelect]);

  useEffect(() => {
    if (!clientId || !mapRef.current) {
      setMapReady(false);
      return;
    }

    let cancelled = false;

    loadNaverScript(clientId)
      .then(() => {
        if (cancelled || !mapRef.current) return;
        // 스크립트는 200으로 떨어져도 인증 실패면 naver.maps가 없다.
        // 여기서 빠져나가면 "지도 준비 중…"에 영원히 멈추므로 에러로 처리한다.
        if (!window.naver?.maps) {
          setMapError(true);
          setMapReady(false);
          return;
        }
        const center = new window.naver.maps.LatLng(
          HANAM_CENTER.lat,
          HANAM_CENTER.lng,
        );
        mapInstance.current = new window.naver.maps.Map(mapRef.current, {
          center,
          zoom: 14,
        });
        setMapReady(true);
        setMapError(false);
      })
      .catch(() => {
        if (!cancelled) {
          setMapError(true);
          setMapReady(false);
        }
      });

    return () => {
      cancelled = true;
      markersRef.current.forEach((m) => m.marker.setMap(null));
      markersRef.current = [];
      // destroy 없이 ref만 비우면 StrictMode 이중 마운트에서 같은 DOM 노드에
      // Map이 두 번 붙는다.
      mapInstance.current?.destroy();
      mapInstance.current = null;
      setMapReady(false);
    };
  }, [clientId]);

  // 마커는 목록이 바뀔 때만 다시 만든다. selectedId를 여기 넣으면 선택할 때마다
  // 전체 마커가 재생성된다.
  useEffect(() => {
    if (!mapReady || !window.naver?.maps || !mapInstance.current) return;
    const maps = window.naver.maps;
    const map = mapInstance.current;

    for (const academy of academies) {
      if (academy.latitude == null || academy.longitude == null) continue;
      const marker = new maps.Marker({
        position: new maps.LatLng(academy.latitude, academy.longitude),
        map,
        title: academy.name,
      });
      maps.Event.addListener(marker, "click", () => {
        onSelectRef.current(academy.id);
      });
      markersRef.current.push({ id: academy.id, marker });
    }

    return () => {
      markersRef.current.forEach((m) => m.marker.setMap(null));
      markersRef.current = [];
    };
  }, [academies, mapReady]);

  useEffect(() => {
    if (!mapReady || !window.naver?.maps || !mapInstance.current) return;
    const selected = academies.find((a) => a.id === selectedId);
    if (selected?.latitude == null || selected.longitude == null) return;
    mapInstance.current.setCenter(
      new window.naver.maps.LatLng(selected.latitude, selected.longitude),
    );
  }, [academies, selectedId, mapReady]);

  const showPlaceholder = !clientId || mapError || !mapReady;
  const isEmpty = academies.length === 0;
  const emptyMessage = emptyHint ?? MAP_EMPTY_LIST;

  return (
    <div className="flex h-full min-h-0 flex-col gap-3">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-lg font-bold text-ink">{heading}</h2>
        {!isEmpty ? <Badge>{academies.length}곳</Badge> : null}
      </div>

      {children ? <div className="space-y-2">{children}</div> : null}

      <div className="relative min-h-[220px] flex-1 overflow-hidden rounded-card border border-border-soft bg-surface-subtle">
        {clientId ? (
          <div ref={mapRef} className="absolute inset-0 h-full w-full" />
        ) : null}
        {showPlaceholder ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-surface-subtle/90 p-4 text-center">
            <p className="text-sm font-medium text-ink-muted">
              {clientId
                ? mapError
                  ? "지도를 불러오지 못했어요"
                  : "지도 준비 중…"
                : "지도 플레이스홀더"}
            </p>
            <p className="max-w-xs text-xs text-ink-subtle">
              {clientId
                ? "Naver Maps 스크립트 로드를 확인해 주세요."
                : "NEXT_PUBLIC_NAVER_MAP_CLIENT_ID를 설정하면 네이버 지도가 표시됩니다."}
            </p>
            {isEmpty && emptyHint ? (
              <p className="max-w-xs text-xs text-ink-subtle">{emptyHint}</p>
            ) : null}
          </div>
        ) : isEmpty && emptyHint ? (
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center p-4 text-center">
            <p className="max-w-xs rounded-card bg-surface/85 px-3 py-2 text-sm text-ink-muted shadow-soft">
              {emptyHint}
            </p>
          </div>
        ) : null}
      </div>

      {isEmpty ? (
        <p className="text-sm text-ink-subtle">{emptyMessage}</p>
      ) : (
        <ul className="max-h-48 space-y-2 overflow-y-auto sm:max-h-56">
          {academies.map((a) => (
            <li key={a.id}>
              <Card
                padding="sm"
                className={[
                  "cursor-pointer transition-shadow hover:shadow-soft",
                  selectedId === a.id ? "ring-2 ring-brand" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                onClick={() => onOpenDetail(a.id)}
              >
                <div className="flex flex-wrap items-center gap-1.5">
                  <p className="font-medium text-ink">{a.name}</p>
                  {a.subjects?.map((s) => (
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
      )}
    </div>
  );
}
