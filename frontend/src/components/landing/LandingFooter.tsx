import { Disclaimer } from "@/components/ui";

export function LandingFooter() {
  return (
    <footer className="border-t border-border bg-surface">
      <div className="mx-auto max-w-5xl space-y-4 px-4 py-8 sm:px-6">
        <Disclaimer>
          추천 결과는 참고용 정보이며, 최종 선택 전 학원에 직접 확인하시길
          권장합니다.
        </Disclaimer>
        <p className="text-xs text-ink-subtle">
          학원콕 · 하남 미사 AI 학원 추천
        </p>
      </div>
    </footer>
  );
}
