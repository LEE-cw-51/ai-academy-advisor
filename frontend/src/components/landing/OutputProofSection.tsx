import {
  QUESTIONS_HEADING,
  VERIFIED_AT_LABEL,
  WHY_CANDIDATE_HEADING,
} from "@/components/app/exploreCopy";

/** 홈 히어로 바로 아래 — 제출 후 받게 되는 결과물 형태만 보여 준다.
 *  가짜 학원 상호·div 스크린샷을 넣지 않는다. 칸의 역할(이름·이유·질문·직접 확인)
 *  만 실제 앱과 같은 위계로 보여 준다 (2026-09-25 시각 언어). */
const SAMPLE_QUESTIONS = [
  "질문하면 수업 중에 바로 받아 주시나요, 따로 클리닉이 있나요?",
  "오답은 누가, 얼마나 자주 봐 주나요?",
  "학부모에게 진도와 숙제를 어떻게 알려 주시나요?",
] as const;

export function OutputProofSection() {
  return (
    <section
      aria-labelledby="home-output-proof-heading"
      className="mx-auto max-w-5xl px-4 pb-14 sm:px-6"
    >
      <h2
        id="home-output-proof-heading"
        className="text-lg font-semibold tracking-tight text-ink"
      >
        이렇게 정리해 드려요
      </h2>
      <p className="mt-1.5 max-w-xl break-keep text-sm text-ink-muted">
        확인해 볼 후보 이유, 상담에서 물어볼 질문, 그리고 직접 전화·길찾기·웹사이트.
      </p>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        {/* 후보 칸 — 상호 없이 역할만. RecommendationCard와 같은 정보 순서. */}
        <article className="overflow-hidden rounded-card bg-surface shadow-card">
          <div className="space-y-3 p-4 sm:p-5">
            <div className="flex flex-wrap items-baseline gap-2">
              <p className="text-base font-semibold text-ink">학원 이름</p>
              <span className="text-xs font-medium text-ink-subtle">과목</span>
            </div>
            <div>
              <p className="text-xs font-semibold text-ink-muted">
                {WHY_CANDIDATE_HEADING}
              </p>
              <p className="mt-1 break-keep text-sm leading-relaxed text-ink">
                입력한 학년·과목·고민과 맞는 공개 정보만으로, 왜 이 후보를 보여
                드렸는지 한 문장으로 적어요.
              </p>
            </div>
            <p className="text-xs text-ink-subtle">
              주소 · {VERIFIED_AT_LABEL}
            </p>
          </div>
          <div className="flex flex-wrap gap-2 border-t border-border-soft px-4 py-3 sm:px-5">
            <span className="inline-flex min-h-11 items-center rounded-btn border border-border bg-surface px-3 text-xs font-semibold text-ink">
              전화
            </span>
            <span className="inline-flex min-h-11 items-center rounded-btn border border-border bg-surface px-3 text-xs font-semibold text-ink">
              상세
            </span>
            <span className="inline-flex min-h-11 items-center rounded-btn px-3 text-xs font-semibold text-ink-muted">
              길찾기
            </span>
            <span className="inline-flex min-h-11 items-center rounded-btn px-3 text-xs font-semibold text-ink-muted">
              웹사이트
            </span>
          </div>
        </article>

        {/* 상담 질문 칸 — ChatPanel 질문 목록과 같은 위계. */}
        <div className="rounded-card bg-surface-muted px-4 py-4 sm:px-5 sm:py-5">
          <h3 className="text-sm font-semibold text-ink">{QUESTIONS_HEADING}</h3>
          <ol className="mt-3 space-y-3">
            {SAMPLE_QUESTIONS.map((prompt, idx) => (
              <li key={prompt} className="text-sm text-ink">
                <p className="font-medium text-ink-muted">{idx + 1}.</p>
                <p className="mt-0.5 break-keep leading-relaxed text-ink">
                  {prompt}
                </p>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
}
