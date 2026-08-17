import type { Metadata } from "next";
import { CHECKLISTS } from "@/components/checklists/checklistsData";
import { LandingFooter } from "@/components/landing/LandingFooter";
import { LandingHeader } from "@/components/landing/LandingHeader";
import { Card } from "@/components/ui";

export const metadata: Metadata = {
  title: "학원 선택·점검 체크리스트 3종 | 학원콕",
  description:
    "학원 등록 전, 지금 다니는 학원, 옮기기 전에 확인할 질문을 모았습니다. 학원을 대신 평가하거나 상담을 연결하지 않습니다.",
};

export default function ChecklistsPage() {
  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <LandingHeader />
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-8 sm:px-6 sm:py-12">
        <h1 className="break-keep text-2xl font-black leading-tight text-ink sm:text-3xl">
          학원 선택·점검 체크리스트 3종
        </h1>
        <p className="mt-2 break-keep text-sm text-ink-muted">
          지금 학원을 알아보는 중인지, 다니는 학원을 점검하고 싶은지, 옮기기
          전인지에 맞춰 필요한 자료를 골라보세요. 학원을 대신 평가하거나 상담을
          연결하지 않습니다.
        </p>
        <nav className="mt-6 flex flex-col gap-2 sm:flex-row sm:flex-wrap">
          {CHECKLISTS.map((checklist) => (
            <a
              key={checklist.id}
              href={`#${checklist.id}`}
              className="inline-flex items-center justify-center rounded-btn border border-border bg-surface px-4 py-2.5 text-sm font-semibold text-ink transition-colors hover:bg-surface-muted"
            >
              {checklist.title}
            </a>
          ))}
        </nav>
        <div className="mt-10 space-y-10">
          {CHECKLISTS.map((checklist) => (
            <section
              key={checklist.id}
              id={checklist.id}
              className="scroll-mt-20"
            >
              <Card padding="lg">
                <p className="text-xs font-semibold text-ink-muted">
                  {checklist.when}
                </p>
                <h2 className="mt-1 break-keep text-lg font-bold text-ink sm:text-xl">
                  {checklist.title}
                </h2>
                <p className="mt-2 break-keep text-sm text-ink-muted">
                  {checklist.action}
                </p>
                <ol className="mt-5 divide-y divide-border-soft">
                  {checklist.items.map((item, index) => (
                    <li key={item.title} className="break-keep pt-4 first:pt-0">
                      <p className="text-sm font-semibold text-ink">
                        <span className="mr-1 font-black text-brand">
                          {index + 1}.
                        </span>
                        {item.title}
                      </p>
                      <p className="mt-1 text-sm leading-relaxed text-ink-muted">
                        {item.prompt}
                      </p>
                    </li>
                  ))}
                </ol>
              </Card>
            </section>
          ))}
        </div>
      </main>
      <LandingFooter />
    </div>
  );
}
