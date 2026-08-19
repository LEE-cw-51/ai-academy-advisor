import { Badge } from "@/components/ui";
import {
  PLANNED_BADGE_LABEL,
  PLANNED_FEATURES,
  PLANNED_FEATURES_HEADING,
} from "./landingFacts";

/** 지금 없는 기능을 예고한다. 현재형으로 쓰면 같은 화면 하단
 *  GroundworkSection의 "정식 출시 후 제공됩니다"와 충돌한다. */
export function PlannedFeaturesSection() {
  return (
    <section className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <h2 className="text-center text-xl font-bold text-ink sm:text-2xl">
        {PLANNED_FEATURES_HEADING}
      </h2>
      <dl className="mx-auto mt-6 grid max-w-3xl gap-4 sm:grid-cols-2">
        {PLANNED_FEATURES.map((feature) => (
          <div
            key={feature.id}
            className="rounded-card border border-border-soft bg-surface px-5 py-4"
          >
            <dt className="flex flex-wrap items-center gap-2 font-bold text-ink">
              {feature.title}
              <Badge tone="neutral">{PLANNED_BADGE_LABEL}</Badge>
            </dt>
            <dd className="mt-1.5 break-keep text-sm leading-relaxed text-ink-muted">
              {feature.body}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
