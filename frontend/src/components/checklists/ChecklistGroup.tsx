import { Card } from "@/components/ui";
import type { ResolvedConsultGroup } from "./checklistsData";

interface ChecklistGroupProps {
  group: ResolvedConsultGroup;
  index: number;
  /** 이 묶음의 첫 항목이 페이지 전체 기준 몇 번째인지 (0-based). */
  startIndex: number;
}

/** `/checklists` 상담 랜딩의 한 묶음. 번호는 묶음 안에서가 아니라 페이지 전체에서
 *  이어진다 — 광고가 "질문 12가지"라고 말하므로 방문자가 진행량을 가늠할 수 있어야 한다. */
export function ChecklistGroup({ group, index, startIndex }: ChecklistGroupProps) {
  return (
    <section id={`group-${index}`} className="scroll-mt-20">
      <Card padding="lg">
        <h2 className="break-keep text-lg font-bold text-ink sm:text-xl">
          {group.heading}
        </h2>
        <ol className="mt-4 divide-y divide-border-soft">
          {group.items.map((item, itemIndex) => (
            <li
              key={item.title}
              className="flex gap-3 break-keep py-4 first:pt-0 last:pb-0"
            >
              <span className="shrink-0 font-black text-brand">
                {startIndex + itemIndex + 1}.
              </span>
              <div>
                <p className="text-sm font-semibold text-ink">{item.title}</p>
                <p className="mt-1 text-sm leading-relaxed text-ink-muted">
                  {item.prompt}
                </p>
              </div>
            </li>
          ))}
        </ol>
      </Card>
    </section>
  );
}
