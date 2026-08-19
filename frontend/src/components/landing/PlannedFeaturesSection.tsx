import { Card } from "@/components/ui";
import { LIFECYCLE_SECTION_HEADING, LIFECYCLE_STAGES } from "./landingFacts";

export function PlannedFeaturesSection() {
  return (
    <section className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <h2 className="text-center text-xl font-bold text-ink sm:text-2xl">
        {LIFECYCLE_SECTION_HEADING}
      </h2>
      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        {LIFECYCLE_STAGES.map((stage) => (
          <Card key={stage.title} padding="lg" className="border border-border-soft text-center shadow-none">
            <h3 className="font-bold text-ink">{stage.title}</h3>
            {/* break-keep: 좁은 폭에서 단어 중간이 끊기지 않게 한다. */}
            <p className="mt-2 break-keep text-sm text-ink-muted">{stage.body}</p>
          </Card>
        ))}
      </div>
    </section>
  );
}
