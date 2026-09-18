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
 * 후보 카드 — 첫 화면은 이름·배지·이유·확인일·다음 행동만
 * (docs/decision-log.md 2026-09-13). 이름 → 과목 배지(있을 때만) → 주소(있을 때만)
 * → 왜 이 후보인지 → 정보 확인일 → 전화·상세·길찾기.
 *
 * 확인된 조건·조건과 다른 점·리뷰 스니펫은 "근거 더 보기" 토글 뒤에 둔다 — 투명성
 * 필드는 계속 보여 주되 첫 시선을 차지하지 않게. 그 안에서도 등록 정보와 맞는 조건과
 * 학원 이름에서 추정한 신호(`subject_name`)는 다른 줄이다 — 사실과 런타임 탐색 신호를
 * 학부모가 구분할 수 있어야 한다 (Phase 5c 1개월차). `score`는 응답 내 상대값이라
 * 표시하지 않는다. `unknown_conditions`도 나열하지 않는다 — 컬럼 대부분이 아직
 * null이라 미확인 목록이 사실보다 길어진다(상세 모달이 한 줄로 묶어 보여 준다).
 * 전화번호는 글자로 찍지 않는다 — 전화 버튼이 열고, 상세 모달이 보여 준다.
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
  // 모르는 백엔드 키는 conditionLabel 이 빈 문자열로 숨긴다. 라벨이 하나도 안 남으면
  // "확인된 조건:" 뒤가 비므로, 토글·행 표시는 원본 배열이 아니라 라벨 기준으로 판단한다.
  const matchedLabels = matched_conditions.map(conditionLabel).filter(Boolean);
  // 같은 배열을 신호 사전으로 한 번 더 읽는다 — 두 사전은 키가 겹치지 않는다.
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
        "overflow-hidden rounded-card border border-border-soft bg-surface shadow-card",
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

        {academy.address ? (
          <p className="text-xs text-ink-subtle">{academy.address}</p>
        ) : null}

        <CardSection title={WHY_CANDIDATE_HEADING}>
          <p className="line-clamp-3 break-words text-sm text-ink-muted">
            {reason}
          </p>
        </CardSection>

        <p className="mt-2 text-xs text-ink-subtle">
          {VERIFIED_AT_LABEL}: {academy.last_verified_at ?? UNCONFIRMED_VALUE}
        </p>
      </Card>

      {hasEvidence ? (
        // role=button 카드 밖에 둔다 — 카드 안에 넣으면 컨트롤이 중첩된다.
        <div className="border-t border-border-soft px-3">
          <button
            type="button"
            aria-expanded={evidenceOpen}
            aria-controls={evidenceId}
            onClick={(e) => {
              e.stopPropagation();
              setEvidenceOpen((o) => !o);
            }}
            className="inline-flex min-h-11 items-center text-xs font-semibold text-ink-muted transition-colors hover:text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
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
              // 등록 정보와 맞는 조건 아래, 별도 줄. 같은 문장에 섞지 않는다.
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
            // detail 계측은 AppShell.onOpenDetail 한 곳에서 한다 (지도 목록과 공통 합류점).
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
