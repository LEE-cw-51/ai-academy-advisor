import type { Metadata } from "next";
import { buttonClassName } from "@/components/ui";
import { ChecklistGroup } from "@/components/checklists/ChecklistGroup";
import { resolveConsultGroups } from "@/components/checklists/checklistsData";
import { KakaoChannelCta } from "@/components/landing/KakaoChannelCta";
import { HeroSection } from "@/components/landing/HeroSection";
import { SiteChrome } from "@/components/landing/SiteChrome";
import { TrackedLink } from "@/components/landing/TrackedLink";
import {
  CONSULT_CHECK_CTA_LABEL,
  CONSULT_KAKAO_CTA_LABEL,
  CONSULT_REASSURANCE,
} from "@/components/landing/landingFacts";

export const metadata: Metadata = {
  title: "학원 상담 전 질문 | 학원콕",
  description:
    "처음 등록하거나 새 학원을 알아보는 중이라면, 상담 전에 확인할 질문을 모았습니다. 학원을 대신 평가하거나 상담을 연결하지 않습니다.",
};

/** 학원을 알아보는 중인 학부모의 상담 랜딩 (당근 광고 A 착지).
 *  2026-08-19에 `체크리스트 3종` 허브에서 이 형태로 개편했다 —
 *  before-enroll 12항목을 5묶음으로 재편집하고, 이전 고민(before-switch)을
 *  네 번째 페이지 대신 다섯 번째 묶음으로 흡수했다. */
export default function ChecklistsPage() {
  const groups = resolveConsultGroups();
  // 광고가 "질문 12가지"라고 말하므로 번호는 묶음 안이 아니라 페이지 전체에서
  // 이어져야 한다 — 각 묶음의 시작 번호를 앞선 묶음들의 항목 수 누적으로 구한다.
  let runningCount = 0;
  const startIndexes = groups.map((group) => {
    const start = runningCount;
    runningCount += group.items.length;
    return start;
  });

  return (
    <SiteChrome>
      <main className="flex-1">
        <HeroSection logo={false} reassurance={false} />
        <div className="mx-auto w-full max-w-3xl px-4 sm:px-6">
          <nav className="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
            {groups.map((group, index) => (
              <a
                key={group.heading}
                href={`#group-${index}`}
                className="inline-flex items-center justify-center rounded-btn border border-border bg-surface px-4 py-2.5 text-sm font-semibold text-ink transition-colors hover:bg-surface-muted"
              >
                {group.heading}
              </a>
            ))}
          </nav>
          <div className="mt-8 space-y-8 pb-4">
            {groups.map((group, index) => (
              <ChecklistGroup
                key={group.heading}
                group={group}
                index={index}
                startIndex={startIndexes[index]}
              />
            ))}
          </div>
          <div className="flex flex-col items-stretch gap-3 pb-10">
            <TrackedLink
              href="/check"
              event="explore_check_clicked"
              className={buttonClassName({ className: "!px-6 !py-3 text-base" })}
            >
              {CONSULT_CHECK_CTA_LABEL}
            </TrackedLink>
            <KakaoChannelCta
              className={buttonClassName({
                variant: "kakao",
                className: "!px-6 !py-3 text-base",
              })}
            >
              {CONSULT_KAKAO_CTA_LABEL}
            </KakaoChannelCta>
            <p className="text-center text-xs text-ink-muted">{CONSULT_REASSURANCE}</p>
          </div>
        </div>
      </main>
    </SiteChrome>
  );
}
