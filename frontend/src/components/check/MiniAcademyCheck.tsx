"use client";

import { useEffect, useRef, useState } from "react";
import { Badge, Button, ButtonLink, Card, buttonClassName } from "@/components/ui";
import { HeroSection } from "@/components/landing/HeroSection";
import { KakaoChannelCta } from "@/components/landing/KakaoChannelCta";
import {
  CHECK_CTA_HINT,
  CHECK_CTA_LABEL,
  CHECK_RESULT_CONSULT_LABEL,
  CHECK_RESULT_HOME_LABEL,
  CHECK_RESULT_KAKAO_LABEL,
  CTA_REASSURANCE,
  KAKAO_WELCOME_HINT,
} from "@/components/landing/landingFacts";
import { TrackedLink } from "@/components/landing/TrackedLink";
import { trackEvent } from "@/lib/api";
import {
  ANSWERS,
  QUESTIONS,
  RESULT_COPY,
  classifyResult,
  pickCounselingQuestions,
  type AnswerId,
  COUNSELING_HEADING_DEFAULT,
  COUNSELING_HEADING_STABLE,
} from "./checkData";

type Phase = "intro" | "questions" | "result";

export function MiniAcademyCheck() {
  const [phase, setPhase] = useState<Phase>("intro");
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<AnswerId[]>([]);
  const resultTrackedRef = useRef(false);
  const question = QUESTIONS[step];

  const progressLabel =
    phase === "result" ? "결과" : `${step + 1} / ${QUESTIONS.length}`;
  const progressRatio =
    phase === "intro"
      ? 0
      : phase === "result"
        ? 1
        : (step + 1) / QUESTIONS.length;

  useEffect(() => {
    if (phase !== "result" || resultTrackedRef.current) return;
    resultTrackedRef.current = true;
    trackEvent({ event: "mini_check_result_viewed" }).catch(() => {
      // 추적 실패가 결과를 가리지 않는다
    });
  }, [phase]);

  function startCheck() {
    trackEvent({ event: "mini_check_started" }).catch(() => {
      // 추적 실패가 점검을 막지 않는다
    });
    setPhase("questions");
  }

  function selectAnswer(answer: AnswerId) {
    const next = [...answers.slice(0, step), answer];
    setAnswers(next);
    if (step === QUESTIONS.length - 1) {
      trackEvent({ event: "mini_check_completed" }).catch(() => {
        // 추적 실패가 결과 화면을 막지 않는다
      });
      setPhase("result");
      return;
    }
    setStep(step + 1);
  }

  function goBack() {
    if (step <= 0) return;
    setStep(step - 1);
  }

  function trackHomeClick() {
    trackEvent({ event: "mini_check_home_clicked" }).catch(() => {
      // 추적 실패가 이동을 막지 않는다
    });
  }

  if (phase === "intro") {
    return (
      <>
        <HeroSection reassurance={false} />
        <div className="mx-auto w-full max-w-lg space-y-3 px-4 pb-8 sm:px-6">
          <Button
            fullWidth
            className="!px-6 !py-3 text-base"
            onClick={startCheck}
          >
            {CHECK_CTA_LABEL}
          </Button>
          <p className="text-center text-xs text-ink-muted">{CHECK_CTA_HINT}</p>
        </div>
      </>
    );
  }

  if (phase === "result") {
    const kind = classifyResult(answers);
    const copy = RESULT_COPY[kind];
    const counseling = pickCounselingQuestions(answers);

    return (
      <div className="mx-auto w-full max-w-lg space-y-5 px-4 py-8 sm:px-6 sm:py-12">
        <ProgressHeader label={progressLabel} ratio={progressRatio} />
        <Card padding="lg">
          <Badge tone="neutral">학원 평가가 아닙니다</Badge>
          <h2 className="mt-3 break-keep text-xl font-bold text-ink sm:text-2xl">
            {copy.headline}
          </h2>
          <p className="mt-2 break-keep text-sm leading-relaxed text-ink-muted">
            {copy.body}
          </p>
          <p className="mt-3 break-keep text-sm font-semibold text-ink">
            {copy.next}
          </p>
          {counseling.length > 0 ? (
            <div className="mt-5 border-t border-border-soft pt-5">
              <p className="text-sm font-semibold text-ink">
                {kind === "stable"
                  ? COUNSELING_HEADING_STABLE
                  : COUNSELING_HEADING_DEFAULT}
              </p>
              <ol className="mt-3 list-decimal space-y-3 pl-5 text-sm leading-relaxed text-ink-muted">
                {counseling.map((item) => (
                  <li key={item} className="break-keep">
                    {item}
                  </li>
                ))}
              </ol>
            </div>
          ) : null}
        </Card>
        <div className="flex flex-col items-stretch gap-3">
          <KakaoChannelCta
            event="checklist_kakao_clicked"
            className={buttonClassName({
              variant: "kakao",
              fullWidth: true,
              className: "!px-6 !py-3 text-base",
            })}
          >
            {CHECK_RESULT_KAKAO_LABEL}
          </KakaoChannelCta>
          <p className="text-center text-xs leading-relaxed text-ink-muted">
            {CTA_REASSURANCE} · {KAKAO_WELCOME_HINT}
          </p>
          <TrackedLink
            href="/checklists"
            event="check_explore_clicked"
            className={buttonClassName({
              variant: "secondary",
              className: "!px-6 !py-3 text-base",
            })}
          >
            {CHECK_RESULT_CONSULT_LABEL}
          </TrackedLink>
          <ButtonLink
            href="/"
            variant="ghost"
            className="text-sm"
            onClick={trackHomeClick}
          >
            {CHECK_RESULT_HOME_LABEL}
          </ButtonLink>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-lg space-y-5 px-4 py-8 sm:px-6 sm:py-12">
      <ProgressHeader label={progressLabel} ratio={progressRatio} />
      <Card padding="lg">
        <p className="break-keep text-lg font-bold leading-snug text-ink sm:text-xl">
          {question.prompt}
        </p>
        <div className="mt-6 flex flex-col gap-2.5">
          {ANSWERS.map((answer) => (
            <Button
              key={answer.id}
              variant="secondary"
              fullWidth
              className="!justify-start !px-4 !py-3.5 text-left text-sm"
              onClick={() => selectAnswer(answer.id)}
            >
              {answer.label}
            </Button>
          ))}
        </div>
      </Card>
      {step > 0 ? (
        <Button variant="ghost" className="text-sm" onClick={goBack}>
          이전 질문
        </Button>
      ) : null}
    </div>
  );
}

function ProgressHeader({ label, ratio }: { label: string; ratio: number }) {
  return (
    <div>
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-sm font-semibold text-ink">{CHECK_CTA_LABEL}</h1>
        <p className="text-sm text-ink-muted">{label}</p>
      </div>
      <div
        className="mt-2 h-1.5 overflow-hidden rounded-full bg-surface-subtle"
        aria-hidden
      >
        <div
          className="h-full rounded-full bg-brand transition-[width] duration-200 motion-reduce:transition-none"
          style={{ width: `${Math.round(ratio * 100)}%` }}
        />
      </div>
    </div>
  );
}
