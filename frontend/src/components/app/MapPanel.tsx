"use client";

import { useEffect, useRef, useState } from "react";
import { Badge, Card } from "@/components/ui";
import type { AcademySummary } from "@/lib/types";

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
  selectedId: number | null;
  onSelect: (id: number) => void;
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

export function MapPanel({ academies, selectedId, onSelect }: MapPanelProps) {
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

  return (
    <div className="flex h-full min-h-0 flex-col gap-3">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-lg font-bold text-ink">지도 · 학원</h2>
        <Badge>{academies.length}곳</Badge>
      </div>

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
          </div>
        ) : null}
      </div>

      <ul className="max-h-48 space-y-2 overflow-y-auto sm:max-h-56">
        {academies.length === 0 ? (
          <li className="text-sm text-ink-subtle">표시할 학원이 없습니다.</li>
        ) : (
          academies.map((a) => (
            <li key={a.id}>
              <Card
                padding="sm"
                className={[
                  "cursor-pointer transition-shadow hover:shadow-soft",
                  selectedId === a.id ? "ring-2 ring-brand" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                onClick={() => onSelect(a.id)}
              >
                <p className="font-medium text-ink">{a.name}</p>
                {a.address ? (
                  <p className="mt-0.5 text-xs text-ink-subtle">{a.address}</p>
                ) : null}
              </Card>
            </li>
          ))
        )}
      </ul>
    </div>
  );
}
