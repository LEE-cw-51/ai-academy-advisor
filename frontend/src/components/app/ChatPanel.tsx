"use client";

import { useCallback, useMemo, useState } from "react";
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
import { AcademyDetailModal } from "./AcademyDetailModal";
import {
  CANDIDATES_ERROR,
  CANDIDATES_HEADING,
  EMPTY_RESULTS,
  FORM_HEADING,
  FORM_SUPPORT,
  INTENTS,
  LOADING_LABEL,
  NO_CANDIDATES,
  QUESTIONS_ERROR,
  QUESTIONS_HEADING,
  SUBMIT_LABEL,
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

interface ChatPanelProps {
  onResults: (items: AiRecommendationItem[]) => void;
  onSelectAcademy: (id: number | null) => void;
  selectedAcademyId: number | null;
}

function buildQuery(parts: {
  region: string;
  grade: string | null;
  school: string;
  subject: string | null;
  tags: string[];
  note: string;
}): string {
  const chunks: string[] = [];
  if (parts.region) chunks.push(parts.region);
  if (parts.grade) chunks.push(parts.grade);
  if (parts.school.trim()) chunks.push(parts.school.trim());
  if (parts.subject) chunks.push(parts.subject);
  if (parts.tags.length) chunks.push(parts.tags.join(", "));
  if (parts.note.trim()) chunks.push(parts.note.trim());
  return chunks.join(" · ");
}

export function ChatPanel({
  onResults,
  onSelectAcademy,
  selectedAcademyId,
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
  const [detailId, setDetailId] = useState<number | null>(null);
  const [hasSubmitted, setHasSubmitted] = useState(false);

  const query = useMemo(
    () =>
      buildQuery({
        region: REGION,
        grade,
        school,
        subject,
        tags,
        note,
      }),
    [grade, school, subject, tags, note],
  );

  const canSubmit = Boolean(grade && subject && note.trim());

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

  const closeDetail = useCallback(() => setDetailId(null), []);

  return (
    <div className="flex h-full min-h-0 flex-col gap-5">
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

        <FilterRow label="지역">
          <Chip selected soft disabled>
            {REGION}
          </Chip>
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
      </div>

      <div className="space-y-2.5">
        <p className="flex items-center gap-1.5 text-sm font-medium text-ink-subtle">
          <span aria-hidden>✨</span>
          많이 찾는 질문
        </p>
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

      <div className="relative rounded-card border border-border bg-surface shadow-soft">
        <textarea
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
          placeholder="예) 내신 대비를 잘하는 학원을 찾고 싶어요. 숙제가 너무 많지는 않았으면 좋겠어요."
          className="w-full resize-none rounded-card bg-transparent px-4 py-3.5 pr-14 text-sm text-ink placeholder:text-ink-subtle focus:outline-none disabled:opacity-60"
        />
        <button
          type="button"
          aria-label={SUBMIT_LABEL}
          disabled={loading || !canSubmit}
          onClick={() => void runQuery()}
          className="absolute bottom-3 right-3 inline-flex h-9 w-9 items-center justify-center rounded-full bg-surface-subtle text-ink-subtle transition-colors hover:bg-brand hover:text-ink-strong disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-surface-subtle disabled:hover:text-ink-subtle"
        >
          {loading ? (
            <span className="text-xs font-semibold">…</span>
          ) : (
            <SendIcon />
          )}
        </button>
      </div>

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
            {items.map((item) => (
              <RecommendationCard
                key={item.academy.id}
                item={item}
                selected={selectedAcademyId === item.academy.id}
                onSelect={() => onSelectAcademy(item.academy.id)}
                onShowDetail={() => {
                  onSelectAcademy(item.academy.id);
                  setDetailId(item.academy.id);
                }}
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

      <AcademyDetailModal
        academyId={detailId}
        onClose={closeDetail}
        onTrack={(academyId, event) => void handleTrack(academyId, event)}
      />
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

function SendIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <path
        d="M3.4 20.4 21 12 3.4 3.6 3 10.5l11 1.5L3 13.5l.4 6.9Z"
        fill="currentColor"
      />
    </svg>
  );
}
