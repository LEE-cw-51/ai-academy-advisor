import { SituationCard } from "./SituationCard";
import { SITUATIONS, SITUATION_SECTION_HEADING } from "./landingFacts";

/** 메인의 유일한 첫 과업 — 두 상황 중 하나를 고르게 한다.
 *  세 번째 카드(옮기기 전)는 없다 — /checklists의 마지막 묶음이 그 맥락을 담는다. */
export function SituationSection() {
  return (
    <section className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <h2 className="text-center text-xl font-bold text-ink sm:text-2xl">
        {SITUATION_SECTION_HEADING}
      </h2>
      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {SITUATIONS.map((situation) => (
          <SituationCard
            key={situation.id}
            label={situation.label}
            title={situation.title}
            body={situation.body}
            ctaLabel={situation.ctaLabel}
            href={situation.href}
            event={situation.event}
          />
        ))}
      </div>
    </section>
  );
}
