import { Badge, Button, Card } from "@/components/ui";
import { naverDirectionsUrl } from "@/lib/maps";
import type { AiRecommendationItem, ClickEventType } from "@/lib/types";

interface RecommendationCardProps {
  item: AiRecommendationItem;
  rank: number;
  selected?: boolean;
  onSelect?: () => void;
  onShowDetail?: () => void;
  onTrack?: (event: ClickEventType) => void;
}

export function RecommendationCard({
  item,
  rank,
  selected,
  onSelect,
  onShowDetail,
  onTrack,
}: RecommendationCardProps) {
  const { academy, reason, evidence_reviews } = item;
  const coords =
    academy.latitude != null && academy.longitude != null
      ? { lat: academy.latitude, lng: academy.longitude }
      : null;

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
              // 지도에서도 해당 학원으로 이동시켜 두고 네이버 길찾기를 새 탭으로 연다.
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
