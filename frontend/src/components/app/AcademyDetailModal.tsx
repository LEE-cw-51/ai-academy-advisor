"use client";

import { useEffect, useState } from "react";
import { Badge, Button, Modal } from "@/components/ui";
import { fetchAcademyDetail } from "@/lib/api";
import { naverDirectionsUrl } from "@/lib/maps";
import type { AcademyDetail, ClickEventType } from "@/lib/types";

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
            <DetailRow label="주소" value={detail.address} />
            <DetailRow label="전화" value={detail.phone} />
            <DetailRow label="운영 시간" value={detail.operating_hours} />
            <DetailRow
              label="월 수강료"
              value={
                detail.tuition_monthly_fee != null
                  ? `${detail.tuition_monthly_fee.toLocaleString("ko-KR")}원`
                  : null
              }
            />
            <DetailRow
              label="강사 수"
              value={
                detail.teacher_count != null ? `${detail.teacher_count}명` : null
              }
            />
            <DetailRow
              label="셔틀"
              value={
                detail.shuttle_available == null
                  ? null
                  : detail.shuttle_available
                    ? "운행"
                    : "미운행"
              }
            />
            <DetailRow label="정보 확인일" value={detail.last_verified_at} />
          </dl>

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

          {detail.source_note ? (
            <p className="pt-1 text-xs text-ink-subtle">{detail.source_note}</p>
          ) : null}
        </div>
      ) : null}
    </Modal>
  );
}

function DetailRow({
  label,
  value,
}: {
  label: string;
  value: string | null;
}) {
  if (!value) return null;
  return (
    <div className="flex gap-3">
      <dt className="w-20 shrink-0 text-ink-subtle">{label}</dt>
      <dd className="min-w-0 flex-1 text-ink">{value}</dd>
    </div>
  );
}
