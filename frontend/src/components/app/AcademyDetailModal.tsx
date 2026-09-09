"use client";

import { useEffect, useState } from "react";
import { Badge, Button, Modal } from "@/components/ui";
import { fetchAcademyDetail } from "@/lib/api";
import { naverDirectionsUrl } from "@/lib/maps";
import type { AcademyDetail, ClickEventType } from "@/lib/types";
import {
  ASK_AT_CONSULTATION_HEADING,
  ASK_AT_CONSULTATION_ITEMS,
  UNCONFIRMED_VALUE,
  UNVERIFIED_FIELDS_LABEL,
} from "./exploreCopy";

interface AcademyDetailModalProps {
  academyId: number | null;
  onClose: () => void;
  onTrack?: (academyId: number, event: ClickEventType) => void;
}

export function AcademyDetailModal({
  academyId,
  onClose,
  onTrack,
}: AcademyDetailModalProps) {
  const [detail, setDetail] = useState<AcademyDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (academyId == null) {
      setDetail(null);
      setError("");
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError("");
    fetchAcademyDetail(academyId, { signal: controller.signal })
      .then((res) => {
        setDetail(res);
        setLoading(false);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(
          err instanceof Error && err.message
            ? err.message
            : "학원 정보를 불러오지 못했어요.",
        );
        setLoading(false);
      });
    return () => controller.abort();
  }, [academyId]);

  const links: { label: string; url: string }[] = detail
    ? [
        { label: "홈페이지", url: detail.website_url },
        { label: "블로그", url: detail.blog_url },
        { label: "인스타그램", url: detail.instagram_url },
      ].filter((l): l is { label: string; url: string } => Boolean(l.url))
    : [];

  const coords =
    detail && detail.latitude != null && detail.longitude != null
      ? { lat: detail.latitude, lng: detail.longitude }
      : null;

  // <dl> 행과 "아직 확인하지 못한 항목" 줄이 **같은 배열**에서 나온다. 라벨·null 판정을
  // 두 벌로 들고 있으면 한쪽만 고쳤을 때 값이 있는 학원과 없는 학원을 서로 다른
  // 이름으로 부르게 된다 — 사실 표시 화면이라 그 드리프트가 특히 나쁘다.
  //
  // groupWhenEmpty: 아직 거의 채워지지 않은 운영 정보. 비면 행마다 "미확인"을
  // 반복하는 대신 아래 한 줄로 묶는다. 값이 들어오면 자동으로 행으로 올라간다.
  // 주소·전화는 플래그가 없어 비면 행만 사라진다(묶음 줄에 넣지 않는다).
  const factRows = detail
    ? [
        { label: "주소", value: detail.address },
        { label: "전화", value: detail.phone },
        {
          label: "운영 시간",
          value: detail.operating_hours,
          groupWhenEmpty: true,
        },
        {
          label: "월 수강료",
          value:
            detail.tuition_monthly_fee != null
              ? `${detail.tuition_monthly_fee.toLocaleString("ko-KR")}원`
              : null,
          groupWhenEmpty: true,
        },
        {
          label: "강사 수",
          value:
            detail.teacher_count != null ? `${detail.teacher_count}명` : null,
          groupWhenEmpty: true,
        },
        {
          label: "셔틀",
          value:
            detail.shuttle_available == null
              ? null
              : detail.shuttle_available
                ? "운행"
                : "미운행",
          groupWhenEmpty: true,
        },
      ]
    : [];

  const unverifiedFields = factRows
    .filter((field) => field.groupWhenEmpty && field.value == null)
    .map((field) => field.label);

  return (
    <Modal
      open={academyId != null}
      onClose={onClose}
      title={detail?.name ?? "학원 정보"}
      footer={
        detail ? (
          <div className="flex flex-wrap gap-2">
            {detail.phone ? (
              <Button
                variant="secondary"
                onClick={() => {
                  onTrack?.(detail.id, "phone");
                  window.open(`tel:${detail.phone}`, "_self");
                }}
              >
                전화하기
              </Button>
            ) : null}
            {coords ? (
              <Button
                onClick={() => {
                  onTrack?.(detail.id, "directions");
                  window.open(
                    naverDirectionsUrl(coords.lat, coords.lng, detail.name),
                    "_blank",
                    "noopener,noreferrer",
                  );
                }}
              >
                길찾기
              </Button>
            ) : null}
          </div>
        ) : null
      }
    >
      {loading ? <p className="text-ink-subtle">불러오는 중…</p> : null}
      {error ? <p className="text-warn">{error}</p> : null}
      {detail ? (
        <div className="space-y-3">
          {detail.tagline ? (
            <p className="text-ink">{detail.tagline}</p>
          ) : null}

          {detail.subjects?.length ? (
            <div className="flex flex-wrap gap-1.5">
              {detail.subjects.map((s) => (
                <Badge key={s} tone="brand">
                  {s}
                </Badge>
              ))}
            </div>
          ) : null}

          <dl className="space-y-1.5">
            {factRows.map((row) => (
              <DetailRow key={row.label} label={row.label} value={row.value} />
            ))}
            {/* 확인일만 값이 없어도 행으로 남긴다 — "언제 확인한 정보인가"는
                비어 있다는 사실 자체가 사용자에게 필요한 정보다. */}
            <DetailRow
              label="정보 확인일"
              value={detail.last_verified_at}
              showEmpty
            />
          </dl>
          {unverifiedFields.length ? (
            <p className="text-xs text-ink-subtle">
              {UNVERIFIED_FIELDS_LABEL}: {unverifiedFields.join(", ")}
            </p>
          ) : null}
          <div className="rounded-btn bg-surface-muted px-3 py-2">
            <p className="text-xs font-semibold text-ink-muted">
              {ASK_AT_CONSULTATION_HEADING}
            </p>
            <ul className="mt-1 list-disc space-y-0.5 pl-4 text-xs text-ink-muted">
              {ASK_AT_CONSULTATION_ITEMS.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </div>

          {links.length ? (
            <div className="flex flex-wrap gap-3 pt-1">
              {links.map(({ label, url }) => (
                <a
                  key={label}
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm font-medium text-brand-dark underline underline-offset-2"
                  onClick={() => onTrack?.(detail.id, "website")}
                >
                  {label}
                </a>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
    </Modal>
  );
}

function DetailRow({
  label,
  value,
  showEmpty = false,
}: {
  label: string;
  value: string | null;
  showEmpty?: boolean;
}) {
  if (!value && !showEmpty) return null;
  return (
    <div className="flex gap-3">
      <dt className="w-20 shrink-0 text-ink-subtle">{label}</dt>
      <dd className="min-w-0 flex-1 text-ink">{value ?? UNCONFIRMED_VALUE}</dd>
    </div>
  );
}
