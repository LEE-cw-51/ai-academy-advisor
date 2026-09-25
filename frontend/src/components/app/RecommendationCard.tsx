"use client";

import { useState, type ReactNode } from "react";
import { Badge, Button, Card } from "@/components/ui";
import { naverDirectionsUrl } from "@/lib/maps";
import type { AiRecommendationItem, ClickEventType } from "@/lib/types";
import {
  CONFLICTS_HEADING,
  EVIDENCE_TOGGLE_HIDE_LABEL,
  EVIDENCE_TOGGLE_LABEL,
  MATCHED_CONDITIONS_LABEL,
  NAME_SIGNAL_HELPER,
  NAME_SIGNAL_LABEL,
  REVIEW_EVIDENCE_HEADING,
  UNCONFIRMED_VALUE,
  VERIFIED_AT_LABEL,
  WHY_CANDIDATE_HEADING,
  conditionLabel,
  signalLabel,
  subjectBadges,
} from "./exploreCopy";

interface RecommendationCardProps {
  item: AiRecommendationItem;
  selected?: boolean;
  onSelect?: () => void;
  onShowDetail?: () => void;
  onTrack?: (event: ClickEventType) => void;
}

/**
 * 후보 카드 — 장소 상세 위계 (2026-09-25):
 * 이름·과목 → 이유 한 문장 → 주소·확인일 → 전화·상세·길찾기.
 * 근거 토글은 유지하되 첫 시선 밖(액션 아래). `score`는 표시하지 않는다.
 *
 * 선택 영역(Card onActivate)과 근거 토글·전화·상세·길찾기 버튼은 형제다 —
 * role=button 카드 안에 버튼을 넣지 않는다.
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
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const coords =
    academy.latitude != null && academy.longitude != null
      ? { lat: academy.latitude, lng: academy.longitude }
      : null;
  const review = evidence_reviews[0];
  const subjects = subjectBadges(academy.subjects, academy.subject_detail);
  const matchedLabels = matched_conditions.map(conditionLabel).filter(Boolean);
  const signalLabels = matched_conditions.map(signalLabel).filter(Boolean);
  const conflictLabels = conflicts.map(conditionLabel).filter(Boolean);
  const hasEvidence =
    matchedLabels.length > 0 ||
    signalLabels.length > 0 ||
    conflictLabels.length > 0 ||
    Boolean(review);
  const evidenceId = `candidate-evidence-${academy.id}`;

  return (
    <article
      className={[
        "overflow-hidden rounded-card bg-surface shadow-soft",
        selected ? "ring-2 ring-brand" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <Card
        padding="sm"
        className="cursor-pointer rounded-none border-0 shadow-none transition-colors hover:bg-surface-muted/50"
        onActivate={() => onSelect?.()}
      >
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <h3 className="font-semibold text-ink">{academy.name}</h3>
          {subjects.map((s) => (
            <Badge key={s}>{s}</Badge>
          ))}
        </div>

        <div className="mt-1">
          <p className="sr-only">{WHY_CANDIDATE_HEADING}</p>
          <p className="line-clamp-2 break-words text-sm leading-relaxed text-ink">
            {reason}
          </p>
        </div>

        <div className="mt-2 space-y-0.5 text-xs text-ink-subtle">
          {academy.address ? <p>{academy.address}</p> : null}
          <p>
            {VERIFIED_AT_LABEL}: {academy.last_verified_at ?? UNCONFIRMED_VALUE}
          </p>
        </div>
      </Card>

      <div className="flex flex-wrap gap-2 border-t border-border-soft px-3 py-2">
        {academy.phone ? (
          <Button
            variant="secondary"
            className="min-h-11 px-2.5 text-xs"
            onClick={() => {
              onTrack?.("phone");
              window.open(`tel:${academy.phone}`, "_self");
            }}
          >
            전화
          </Button>
        ) : null}
        <Button
          variant="secondary"
          className="min-h-11 px-2.5 text-xs"
          onClick={() => {
            onShowDetail?.();
          }}
        >
          상세
        </Button>
        {coords ? (
          <Button
            variant="ghost"
            className="min-h-11 px-2.5 text-xs"
            onClick={() => {
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

      {hasEvidence ? (
        <div className="border-t border-border-soft px-3">
          <button
            type="button"
            aria-expanded={evidenceOpen}
            aria-controls={evidenceId}
            onClick={(e) => {
              e.stopPropagation();
              setEvidenceOpen((o) => !o);
            }}
            className="inline-flex min-h-11 items-center text-xs font-semibold text-ink-muted transition-colors hover:text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink"
          >
            {evidenceOpen ? EVIDENCE_TOGGLE_HIDE_LABEL : EVIDENCE_TOGGLE_LABEL}
          </button>
          <div id={evidenceId} hidden={!evidenceOpen} className="pb-3">
            {matchedLabels.length > 0 ? (
              <p className="break-words text-xs text-ink-subtle">
                {MATCHED_CONDITIONS_LABEL}: {matchedLabels.join(", ")}
              </p>
            ) : null}

            {signalLabels.length > 0 ? (
              <p className="mt-1 break-words text-xs text-ink-subtle">
                {NAME_SIGNAL_LABEL}: {signalLabels.join(", ")}
                <span className="block">{NAME_SIGNAL_HELPER}</span>
              </p>
            ) : null}

            {conflictLabels.length > 0 ? (
              <CardSection title={CONFLICTS_HEADING}>
                <p className="break-words text-xs text-ink-subtle">
                  {conflictLabels.join(", ")}
                </p>
              </CardSection>
            ) : null}

            {review ? (
              <CardSection title={REVIEW_EVIDENCE_HEADING}>
                <p className="line-clamp-2 break-words text-xs text-ink-subtle">
                  “{review.content}”
                </p>
                {review.source ? (
                  <p className="mt-0.5 text-xs text-ink-subtle">
                    출처: {review.source}
                  </p>
                ) : null}
              </CardSection>
            ) : null}
          </div>
        </div>
      ) : null}
    </article>
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
