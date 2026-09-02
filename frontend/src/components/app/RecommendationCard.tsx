import type { ReactNode } from "react";
import { Badge, Button, Card } from "@/components/ui";
import { naverDirectionsUrl } from "@/lib/maps";
import type { AiRecommendationItem, ClickEventType } from "@/lib/types";
import {
  ASK_AT_CONSULTATION_HEADING,
  ASK_AT_CONSULTATION_ITEMS,
  CANDIDATE_BADGE,
  CONFLICTS_HEADING,
  REVIEW_EVIDENCE_HEADING,
  UNCONFIRMED_HEADING,
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

export function RecommendationCard({
  item,
  selected,
  onSelect,
  onShowDetail,
  onTrack,
}: RecommendationCardProps) {
  const {
    academy,
    reason,
    evidence_reviews,
    matched_conditions,
    unknown_conditions,
    conflicts,
  } = item;
  const coords =
    academy.latitude != null && academy.longitude != null
      ? { lat: academy.latitude, lng: academy.longitude }
      : null;
  const review = evidence_reviews[0];

  return (
    <Card
      padding="sm"
      className={[
        "cursor-pointer transition-shadow hover:shadow-soft",
        selected ? "ring-2 ring-brand" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect?.();
        }
      }}
    >
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <Badge tone="brand">{CANDIDATE_BADGE}</Badge>
        <h3 className="font-semibold text-ink">{academy.name}</h3>
      </div>
      {academy.address ? (
        <p className="text-xs text-ink-subtle">{academy.address}</p>
      ) : null}
      <p className="mt-1 text-xs text-ink-subtle">
        {VERIFIED_AT_LABEL}: {academy.last_verified_at ?? UNCONFIRMED_VALUE}
      </p>

      <CardSection title={WHY_CANDIDATE_HEADING}>
        <p className="text-sm text-ink-muted">{reason}</p>
        {matched_conditions.length > 0 ? (
          <p className="mt-1 text-xs text-ink-subtle">
            확인된 조건: {matched_conditions.map(conditionLabel).join(", ")}
          </p>
        ) : null}
      </CardSection>

      {unknown_conditions.length > 0 ? (
        <CardSection title={UNCONFIRMED_HEADING}>
          <p className="text-xs text-ink-subtle">
            {unknown_conditions.map(conditionLabel).join(", ")}
          </p>
        </CardSection>
      ) : null}

      <CardSection title={ASK_AT_CONSULTATION_HEADING}>
        <ul className="list-disc space-y-0.5 pl-4 text-xs text-ink-muted">
          {ASK_AT_CONSULTATION_ITEMS.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
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
            onTrack?.("detail");
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
