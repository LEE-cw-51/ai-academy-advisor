import type { ReactNode } from "react";
import { Badge, Button, Card } from "@/components/ui";
import { naverDirectionsUrl } from "@/lib/maps";
import type { AiRecommendationItem, ClickEventType } from "@/lib/types";
import {
  CANDIDATE_BADGE,
  CONFLICTS_HEADING,
  MATCHED_CONDITIONS_LABEL,
  REVIEW_EVIDENCE_HEADING,
  UNCONFIRMED_VALUE,
  VERIFIED_AT_LABEL,
  WHY_CANDIDATE_HEADING,
  conditionLabel,
} from "./exploreCopy";

interface RecommendationCardProps {
  item: AiRecommendationItem;
  selected?: boolean;
  onSelect?: () => void;
  onShowDetail?: () => void;
  onTrack?: (event: ClickEventType) => void;
}

/**
 * 후보 카드 — 사실 먼저, AI 이유는 그다음 (docs/decision-log.md 2026-09-08).
 * 이름 → 과목 배지(있을 때만) → 주소·전화 → 확인일 → 왜 이 후보인지.
 * `score`는 응답 내 상대값이라 표시하지 않는다. `unknown_conditions`도 나열하지
 * 않는다 — 컬럼 대부분이 아직 null이라 미확인 목록이 사실보다 길어진다. 확인된
 * 조건만 보여 주고, 물어볼 것은 왼쪽 상담 질문과 상세 모달에 둔다.
 */
export function RecommendationCard({
  item,
  selected,
  onSelect,
  onShowDetail,
  onTrack,
}: RecommendationCardProps) {
  const { academy, reason, evidence_reviews, matched_conditions, conflicts } =
    item;
  const coords =
    academy.latitude != null && academy.longitude != null
      ? { lat: academy.latitude, lng: academy.longitude }
      : null;
  const review = evidence_reviews[0];
  const subjects = academy.subjects ?? [];

  return (
    <Card
      padding="sm"
      className={[
        "cursor-pointer transition-shadow hover:shadow-soft",
        selected ? "ring-2 ring-brand" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      onActivate={() => onSelect?.()}
    >
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <Badge tone="brand">{CANDIDATE_BADGE}</Badge>
        <h3 className="font-semibold text-ink">{academy.name}</h3>
        {subjects.map((s) => (
          <Badge key={s}>{s}</Badge>
        ))}
      </div>

      <div className="space-y-0.5 text-xs text-ink-subtle">
        {academy.address ? <p>{academy.address}</p> : null}
        {academy.phone ? <p>{academy.phone}</p> : null}
        <p>
          {VERIFIED_AT_LABEL}: {academy.last_verified_at ?? UNCONFIRMED_VALUE}
        </p>
      </div>

      <CardSection title={WHY_CANDIDATE_HEADING}>
        <p className="text-sm text-ink-muted">{reason}</p>
        {matched_conditions.length > 0 ? (
          <p className="mt-1 text-xs text-ink-subtle">
            {MATCHED_CONDITIONS_LABEL}:{" "}
            {matched_conditions.map(conditionLabel).join(", ")}
          </p>
        ) : null}
      </CardSection>

      {conflicts.length > 0 ? (
        <CardSection title={CONFLICTS_HEADING}>
          <p className="text-xs text-ink-subtle">
            {conflicts.map(conditionLabel).join(", ")}
          </p>
        </CardSection>
      ) : null}

      {review ? (
        <CardSection title={REVIEW_EVIDENCE_HEADING}>
          <p className="line-clamp-2 text-xs text-ink-subtle">
            “{review.content}”
          </p>
          {review.source ? (
            <p className="mt-0.5 text-xs text-ink-subtle">출처: {review.source}</p>
          ) : null}
        </CardSection>
      ) : null}

      <div className="mt-3 flex flex-wrap gap-2">
        {academy.phone ? (
          <Button
            variant="secondary"
            className="!px-2.5 !py-1.5 text-xs"
            onClick={(e) => {
              e.stopPropagation();
              onTrack?.("phone");
              window.open(`tel:${academy.phone}`, "_self");
            }}
          >
            전화
          </Button>
        ) : null}
        <Button
          variant="secondary"
          className="!px-2.5 !py-1.5 text-xs"
          onClick={(e) => {
            e.stopPropagation();
            // detail 계측은 AppShell.onOpenDetail 한 곳에서 한다 (지도 목록과 공통 합류점).
            onShowDetail?.();
          }}
        >
          상세
        </Button>
        {coords ? (
          <Button
            variant="ghost"
            className="!px-2.5 !py-1.5 text-xs"
            onClick={(e) => {
              e.stopPropagation();
              onTrack?.("directions");
              onSelect?.();
              window.open(
                naverDirectionsUrl(coords.lat, coords.lng, academy.name),
                "_blank",
                "noopener,noreferrer",
              );
            }}
          >
            길찾기
          </Button>
        ) : null}
      </div>
    </Card>
  );
}

function CardSection({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="mt-2 rounded-btn bg-surface-muted px-3 py-2">
      <p className="text-xs font-semibold text-ink-muted">{title}</p>
      <div className="mt-1">{children}</div>
    </div>
  );
}
