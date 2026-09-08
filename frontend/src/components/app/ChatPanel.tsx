"use client";

import { useMemo, useState } from "react";
import { Badge, Chip } from "@/components/ui";
import {
  requestAiRecommendations,
  requestConsultationQuestions,
  trackEvent,
} from "@/lib/api";
import type {
  AiRecommendationItem,
  ClickEventType,
  ConsultationIntent,
  ConsultationQuestion,
} from "@/lib/types";
import { ApiError } from "@/lib/types";
import {
  CANDIDATES_ERROR,
  CANDIDATES_HEADING,
  EDIT_CONDITIONS_LABEL,
  EMPTY_RESULTS,
  FORM_HEADING,
  FORM_SUPPORT,
  INTENTS,
  LOADING_LABEL,
  MORE_DETAILS_HIDE_LABEL,
  MORE_DETAILS_LABEL,
  NO_CANDIDATES,
  QUESTIONS_ERROR,
  QUESTIONS_HEADING,
  SUBJECT_FORM_HELPER,
  SUBJECT_HELPER,
  SUBMIT_LABEL,
  TAGS_HEADING,
  TAGS_HELPER,
} from "./exploreCopy";
import { RecommendationCard } from "./RecommendationCard";

const REGION = "하남 미사";

const GRADES = ["중1", "중2", "중3", "고1", "고2", "고3"] as const;
const SUBJECTS = ["국어", "영어", "수학", "기타"] as const;
const STYLE_TAGS = [
  "내신 대비",
  "선행",
  "소수정예",
  "최상위권",
  "숙제가 적은",
  "개념 위주",
] as const;

const INTENT_SUMMARY: Record<ConsultationIntent, string> = {
  find_new_academy: "새 학원",
  counsel_only: "상담",
};

interface ChatPanelProps {
  onResults: (items: AiRecommendationItem[]) => void;
  /** 상황 입력을 제출하면 부모가 2열 레이아웃으로 전환한다. */
  onExplored?: () => void;
  onSelectAcademy: (id: number | null) => void;
  selectedAcademyId: number | null;
  onOpenDetail: (id: number) => void;
}

// AI 후보 쿼리. 태그(소수정예·선행 등)는 넣지 않는다 — 백엔드 intent 파서가
// class_*/curriculum_* 조건으로 읽지만 그 컬럼은 아직 대부분 null이라 카드마다
// "미확인"만 늘어난다. 태그는 상담 질문(style_tags)에만 쓴다.
function buildQuery(parts: {
  region: string;
  grade: string | null;
  school: string;
  subject: string | null;
  note: string;
}): string {
  const chunks: string[] = [];
  if (parts.region) chunks.push(parts.region);
  if (parts.grade) chunks.push(parts.grade);
  if (parts.school.trim()) chunks.push(parts.school.trim());
  if (parts.subject) chunks.push(parts.subject);
  if (parts.note.trim()) chunks.push(parts.note.trim());
  return chunks.join(" · ");
}

export function ChatPanel({
  onResults,
  onExplored,
  onSelectAcademy,
  selectedAcademyId,
  onOpenDetail,
}: ChatPanelProps) {
  const [grade, setGrade] = useState<string | null>("중2");
  const [school, setSchool] = useState("");
  const [subject, setSubject] = useState<string | null>("수학");
  const [tags, setTags] = useState<string[]>([]);
  const [note, setNote] = useState("");
  const [currentAcademy, setCurrentAcademy] = useState("");
  const [intent, setIntent] = useState<ConsultationIntent>("find_new_academy");
  const [loading, setLoading] = useState(false);
  const [questionsError, setQuestionsError] = useState("");
  const [candidatesError, setCandidatesError] = useState("");
  const [items, setItems] = useState<AiRecommendationItem[]>([]);
  const [questions, setQuestions] = useState<ConsultationQuestion[]>([]);
  const [questionsDisclaimer, setQuestionsDisclaimer] = useState("");
  const [relaxed, setRelaxed] = useState<string[]>([]);
  const [hasSubmitted, setHasSubmitted] = useState(false);
  const [formExpanded, setFormExpanded] = useState(true);
  const [moreDetailsOpen, setMoreDetailsOpen] = useState(false);

  const query = useMemo(
    () =>
      buildQuery({
        region: REGION,
        grade,
        school,
        subject,
        note,
      }),
    [grade, school, subject, note],
  );

  const canSubmit = Boolean(grade && subject && note.trim());

  const conditionSummary = useMemo(() => {
    const parts = [INTENT_SUMMARY[intent]];
    if (grade) parts.push(grade);
    if (subject) parts.push(subject);
    return parts.join(" · ");
  }, [intent, grade, subject]);

  function toggleTag(tag: string) {
    setTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag],
    );
  }

  async function runQuery() {
    const trimmed = query.trim();
    if (!trimmed || !canSubmit || !grade || !subject) return;
    setLoading(true);
    setQuestions([]);
    setItems([]);
    setQuestionsDisclaimer("");
    setRelaxed([]);
    onResults([]);
    setQuestionsError("");
    setCandidatesError("");
    setHasSubmitted(true);
    setFormExpanded(false);
    onExplored?.();
    try {
      const [questionsResult, recsResult] = await Promise.allSettled([
        requestConsultationQuestions({
          grade,
          subject,
          school: school.trim(),
          current_academy: currentAcademy.trim(),
          style_tags: tags,
          concern: note.trim(),
          intent,
        }),
        requestAiRecommendations(trimmed, 3),
      ]);

      if (questionsResult.status === "fulfilled") {
        // used_fallback이어도 200이므로 질문 본문만 보여 준다. 에러로 취급하지 않는다.
        setQuestions(questionsResult.value.questions.slice(0, 5));
        setQuestionsDisclaimer(questionsResult.value.disclaimer);
      } else {
        setQuestions([]);
        setQuestionsDisclaimer("");
        setQuestionsError(
          questionsResult.reason instanceof ApiError
            ? questionsResult.reason.message
            : QUESTIONS_ERROR,
        );
      }

      if (recsResult.status === "fulfilled") {
        setItems(recsResult.value.items);
        setRelaxed(recsResult.value.relaxed);
        onResults(recsResult.value.items);
        if (recsResult.value.items[0]) {
          onSelectAcademy(recsResult.value.items[0].academy.id);
        }
      } else {
        setItems([]);
        setRelaxed([]);
        onResults([]);
        onSelectAcademy(null);
        setCandidatesError(
          recsResult.reason instanceof ApiError
            ? recsResult.reason.message
            : CANDIDATES_ERROR,
        );
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleTrack(academyId: number, event: ClickEventType) {
    try {
      await trackEvent({ academy_id: academyId, event });
    } catch {
      // tracking should not block UX
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col gap-5">
      {hasSubmitted && !formExpanded ? (
        <div className="flex flex-wrap items-center justify-between gap-2 rounded-card border border-border-soft bg-surface-muted px-3 py-2.5">
          <p className="text-sm font-medium text-ink">{conditionSummary}</p>
          <button
            type="button"
            onClick={() => setFormExpanded(true)}
            className="text-sm font-semibold text-brand underline-offset-2 hover:underline"
          >
            {EDIT_CONDITIONS_LABEL}
          </button>
        </div>
      ) : (
        <>
          <div>
            <div className="mb-1 flex items-center gap-2">
              <h2 className="text-lg font-bold text-ink">{FORM_HEADING}</h2>
              <Badge tone="brand">하남 미사</Badge>
            </div>
            <p className="text-sm text-ink-subtle">{FORM_SUPPORT}</p>
          </div>

          <div className="space-y-3.5">
            <FilterRow label="상황">
              {INTENTS.map((option) => (
                <Chip
                  key={option.id}
                  selected={intent === option.id}
                  disabled={loading}
                  onClick={() => setIntent(option.id)}
                >
                  {option.label}
                </Chip>
              ))}
            </FilterRow>

            <FilterRow label="학년">
              {GRADES.map((g) => (
                <Chip
                  key={g}
                  selected={grade === g}
                  disabled={loading}
                  onClick={() => setGrade(grade === g ? null : g)}
                >
                  {g}
                </Chip>
              ))}
            </FilterRow>

            <FilterRow label="과목">
              {SUBJECTS.map((s) => (
                <Chip
                  key={s}
                  selected={subject === s}
                  disabled={loading}
                  onClick={() => setSubject(subject === s ? null : s)}
                >
                  {s}
                </Chip>
              ))}
            </FilterRow>
            <p className="pl-[3.25rem] text-xs text-ink-subtle">
              {SUBJECT_FORM_HELPER}
            </p>
          </div>

          <div className="space-y-2.5">
            <label className="sr-only" htmlFor="explore-concern">
              고민
            </label>
            <textarea
              id="explore-concern"
              name="note"
              rows={3}
              disabled={loading}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void runQuery();
                }
              }}
              placeholder="예) 질문하면 잘 받아주는지, 오답은 어떻게 봐 주는지 궁금해요."
              className="w-full resize-none rounded-card border border-border bg-surface px-4 py-3.5 text-sm text-ink shadow-soft placeholder:text-ink-subtle focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/30 disabled:opacity-60"
            />
            <button
              type="button"
              disabled={loading || !canSubmit}
              onClick={() => void runQuery()}
              className="w-full rounded-full bg-brand px-4 py-2.5 text-sm font-bold text-ink-strong transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {loading ? LOADING_LABEL : SUBMIT_LABEL}
            </button>
          </div>

          <div className="space-y-2.5">
            <button
              type="button"
              disabled={loading}
              aria-expanded={moreDetailsOpen}
              onClick={() => setMoreDetailsOpen((open) => !open)}
              className="text-sm font-medium text-ink-subtle underline-offset-2 hover:underline disabled:opacity-60"
            >
              {moreDetailsOpen ? MORE_DETAILS_HIDE_LABEL : MORE_DETAILS_LABEL}
            </button>
            {moreDetailsOpen ? (
              <div className="space-y-3.5 rounded-card border border-border-soft bg-surface-muted px-3 py-3">
                <FilterRow label="학교">
                  <input
                    type="text"
                    name="school"
                    value={school}
                    disabled={loading}
                    placeholder="학교 이름을 입력하세요 (예: 미사중학교)"
                    onChange={(e) => setSchool(e.target.value)}
                    className="min-w-0 flex-1 rounded-full border border-border bg-surface px-4 py-2 text-sm text-ink placeholder:text-ink-subtle focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/30 disabled:opacity-60"
                  />
                </FilterRow>

                <FilterRow label="학원">
                  <input
                    type="text"
                    name="current_academy"
                    value={currentAcademy}
                    disabled={loading}
                    placeholder="현재 다니는 학원 (없으면 비워 두세요)"
                    onChange={(e) => setCurrentAcademy(e.target.value)}
                    className="min-w-0 flex-1 rounded-full border border-border bg-surface px-4 py-2 text-sm text-ink placeholder:text-ink-subtle focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/30 disabled:opacity-60"
                  />
                </FilterRow>

                <div className="space-y-2">
                  <p className="text-sm font-medium text-ink-subtle">
                    {TAGS_HEADING}
                  </p>
                  <p className="text-xs text-ink-subtle">{TAGS_HELPER}</p>
                  <div className="flex flex-wrap gap-2">
                    {STYLE_TAGS.map((tag) => (
                      <Chip
                        key={tag}
                        selected={tags.includes(tag)}
                        disabled={loading}
                        onClick={() => toggleTag(tag)}
                      >
                        {tag}
                      </Chip>
                    ))}
                  </div>
                </div>
              </div>
            ) : null}
          </div>

          {hasSubmitted ? (
            <button
              type="button"
              onClick={() => setFormExpanded(false)}
              className="self-start text-sm text-ink-subtle underline-offset-2 hover:underline"
            >
              질문·후보 보기
            </button>
          ) : null}
        </>
      )}

      {loading ? <p className="text-sm text-ink-subtle">{LOADING_LABEL}</p> : null}
      {questionsError ? <p className="text-sm text-warn">{questionsError}</p> : null}
      {candidatesError ? (
        <p className="text-sm text-warn">{candidatesError}</p>
      ) : null}

      {relaxed.length > 0 ? (
        <p className="text-xs text-ink-subtle">
          일부 조건을 완화해 찾았어요: {relaxed.join(", ")}
        </p>
      ) : null}

      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto pr-1">
        {questions.length > 0 ? (
          <section className="space-y-2 rounded-card border border-border-soft bg-surface-muted px-3 py-3">
            <h3 className="text-sm font-semibold text-ink">{QUESTIONS_HEADING}</h3>
            {questionsDisclaimer ? (
              <p className="text-xs text-ink-subtle">{questionsDisclaimer}</p>
            ) : null}
            <ol className="space-y-2">
              {questions.map((question, idx) => (
                <li key={`${question.topic}-${idx}`} className="text-sm text-ink">
                  <p className="font-medium">
                    {idx + 1}. {question.topic}
                  </p>
                  <p className="mt-0.5 text-ink-muted">{question.prompt}</p>
                </li>
              ))}
            </ol>
          </section>
        ) : null}

        {items.length > 0 ? (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-ink">{CANDIDATES_HEADING}</h3>
            <p className="text-xs text-ink-subtle">{SUBJECT_HELPER}</p>
            {items.map((item) => (
              <RecommendationCard
                key={item.academy.id}
                item={item}
                selected={selectedAcademyId === item.academy.id}
                onSelect={() => onSelectAcademy(item.academy.id)}
                onShowDetail={() => onOpenDetail(item.academy.id)}
                onTrack={(event) => void handleTrack(item.academy.id, event)}
              />
            ))}
          </div>
        ) : null}

        {hasSubmitted && !loading && items.length === 0 && !candidatesError ? (
          <p className="text-sm text-ink-subtle">{NO_CANDIDATES}</p>
        ) : null}

        {!hasSubmitted && items.length === 0 && questions.length === 0 && !loading ? (
          <p className="text-sm text-ink-subtle">{EMPTY_RESULTS}</p>
        ) : null}
      </div>
    </div>
  );
}

function FilterRow({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-3 sm:items-center">
      <span className="w-10 shrink-0 pt-1.5 text-sm text-ink-subtle sm:pt-0">
        {label}
      </span>
      <div className="flex min-w-0 flex-1 flex-wrap items-center gap-2">
        {children}
      </div>
    </div>
  );
}
