import { Badge, Card, Disclaimer } from "@/components/ui";
import {
  EXAMPLE_ITEMS,
  PREVIEW_DISCLAIMER,
  PREVIEW_HEADING,
  PREVIEW_NOTICE,
} from "./landingFacts";

/** 텍스트 전용 정적 예시. RecommendationCard(app)와 시각 스타일만 비슷하고
 *  onClick·Link·API 호출이 전혀 없다 — 클릭해도 아무 일도 일어나지 않는다. */
export function ServicePreviewSection() {
  return (
    <section className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <h2 className="text-center text-xl font-bold text-ink sm:text-2xl">
        {PREVIEW_HEADING}
      </h2>
      <p className="mx-auto mt-3 max-w-md break-keep text-center text-sm leading-relaxed text-ink-muted">
        {PREVIEW_NOTICE}
      </p>
      <div className="mx-auto mt-6 max-w-md space-y-3">
        {EXAMPLE_ITEMS.map((item) => (
          <Card key={item.rank} padding="sm">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <Badge tone="rank">{item.rank}순위</Badge>
              <Badge tone="brand">AI 추천 예시</Badge>
              <h3 className="font-semibold text-ink">{item.name}</h3>
            </div>
            <p className="text-sm text-ink-muted">{item.tagline}</p>
            <div className="mt-3 rounded-btn bg-surface-muted px-3 py-2">
              <p className="text-xs font-semibold text-ink-muted">
                왜 추천했나요?
              </p>
              <p className="mt-1 text-xs text-ink-muted">&ldquo;{item.reason}&rdquo;</p>
            </div>
          </Card>
        ))}
      </div>

      <Disclaimer className="mx-auto mt-4 max-w-md">
        {PREVIEW_DISCLAIMER}
      </Disclaimer>
    </section>
  );
}
