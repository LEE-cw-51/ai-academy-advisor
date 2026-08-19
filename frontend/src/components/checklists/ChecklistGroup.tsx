import { Card } from "@/components/ui";
import type { ResolvedConsultGroup } from "./checklistsData";

interface ChecklistGroupProps {
  group: ResolvedConsultGroup;
  index: number;
}

/** `/checklists` 상담 랜딩의 한 묶음. 번호는 묶음 안에서가 아니라 페이지 전체에서
 *  이어진다 — 광고가 "질문 12가지"라고 말하므로 방문자가 진행량을 가늠할 수 있어야 한다. */
export function ChecklistGroup({ group, index }: ChecklistGroupProps) {
  return (
    <section id={`group-${index}`} className="scroll-mt-20">
      <Card padding="lg">
        <h2 className="break-keep text-lg font-bold text-ink sm:text-xl">
          {group.heading}
        </h2>
        <ol className="mt-4 divide-y divide-border-soft">
          {group.items.map((item) => (
            <li key={item.title} className="break-keep py-4 first:pt-0 last:pb-0">
              <p className="text-sm font-semibold text-ink">{item.title}</p>
              <p className="mt-1 text-sm leading-relaxed text-ink-muted">
                {item.prompt}
              </p>
            </li>
          ))}
        </ol>
      </Card>
    </section>
  );
}
