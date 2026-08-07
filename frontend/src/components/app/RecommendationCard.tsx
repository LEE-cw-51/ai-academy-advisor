import { Badge, Button, Card } from "@/components/ui";
import type { AiRecommendationItem, ClickEventType } from "@/lib/types";

interface RecommendationCardProps {
  item: AiRecommendationItem;
  rank: number;
  selected?: boolean;
  onSelect?: () => void;
  onTrack?: (event: ClickEventType) => void;
}

export function RecommendationCard({
  item,
  rank,
  selected,
  onSelect,
  onTrack,
}: RecommendationCardProps) {
  const { academy, reason, evidence_reviews } = item;

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
        <Badge tone="rank">{rank}순위</Badge>
        <Badge tone="brand">AI 추천</Badge>
        <h3 className="font-semibold text-ink">{academy.name}</h3>
      </div>
      {academy.address ? (
        <p className="text-xs text-ink-subtle">{academy.address}</p>
      ) : null}
      <p className="mt-2 text-sm text-ink-muted">{reason}</p>
      {evidence_reviews[0] ? (
        <p className="mt-2 line-clamp-2 text-xs text-ink-subtle">
          “{evidence_reviews[0].content}”
        </p>
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
            onSelect?.();
          }}
        >
          상세
        </Button>
        {academy.latitude != null && academy.longitude != null ? (
          <Button
            variant="ghost"
            className="!px-2.5 !py-1.5 text-xs"
            onClick={(e) => {
              e.stopPropagation();
              onTrack?.("directions");
            }}
          >
            길찾기
          </Button>
        ) : null}
      </div>
    </Card>
  );
}
