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
  CONDITIONS_CHANGED_NOTE,
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
  RELAXED_HEADING,
  RESUBMIT_LABEL,
  SUBJECT_FORM_HELPER,
  SUBJECT_HELPER,
  SUBMIT_LABEL,
  TAGS_HEADING,
  TAGS_HELPER,
  relaxedNotes,
} from "./exploreCopy";
import { RecommendationCard } from "./RecommendationCard";

// /app 을 하남 미사로 고정하는 값. 폼에 지역 행은 없다(헤더 배지로 충분).
// 후보가 비어 이 조건이 풀리면 relaxed 에 "region" 이 담기는데, 키가 아니라
// RELAXED_NOTES.region 문장으로 설명한다.
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

/** 제출 시점에 고정한 조건. 요약 칩과 "조건이 바뀌었어요" 비교의 기준이고,
 *  요청도 여기서 보낸다 — 화면에 적힌 조건과 실제로 보낸 값을 구조로 일치시킨다.
 *  runQuery 가드(!grade || !subject)를 통과한 뒤에만 만들어지므로 null 필드가 없다. */
interface SubmittedConditions {
  intent: ConsultationIntent;
  grade: string;
  subject: string;
  school: string;
  currentAcademy: string;
  tags: string[];
  note: string;
}

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
  // 제출 스냅샷이 곧 "지금 화면 아래 사실을 만든 조건"이다. hasSubmitted 를 따로
  // 두면 둘이 어긋날 수 있어 파생값으로 낮춘다.
  const [submitted, setSubmitted] = useState<SubmittedConditions | null>(null);
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
  const hasSubmitted = submitted !== null;

  // 요약은 라이브 폼이 아니라 제출 스냅샷에서 만든다. 폼만 바꾸고 다시 보내지 않으면
  // 아래 질문·후보는 이전 조건의 사실인데 칩만 새 조건을 적어, 어떤 조건에서 나온
  // 사실인지 잘못 알린다 (docs/decision-log.md 2026-09-08 사실 우선).
  const conditionSummary = useMemo(() => {
    if (!submitted) return "";
    return [
      INTENT_SUMMARY[submitted.intent],
      submitted.grade,
      submitted.subject,
    ].join(" · ");
  }, [submitted]);

  // 요약에 안 보이는 학교·현재 학원·태그·고민도 아래 결과를 바꾼다. 학교·고민은 AI
  // 쿼리 문자열에, 태그·현재 학원·상황은 상담 질문에 들어간다. 요약 3필드만 비교하면
  // 태그만 바꾼 사용자는 칩이 맞는데 질문이 이전 것인 상태를 안내 없이 본다.
  // 태그는 순서를 무시한다 — 고르는 차례가 조건 변경은 아니다.
  const conditionsChanged = useMemo(() => {
    if (!submitted) return false;
    return (
      submitted.intent !== intent ||
      submitted.grade !== grade ||
      submitted.subject !== subject ||
      submitted.school !== school.trim() ||
      submitted.currentAcademy !== currentAcademy.trim() ||
      submitted.note !== note.trim() ||
      submitted.tags.length !== tags.length ||
      submitted.tags.some((t) => !tags.includes(t))
    );
  }, [submitted, intent, grade, subject, school, currentAcademy, note, tags]);

  const relaxedSentences = useMemo(() => relaxedNotes(relaxed), [relaxed]);

  function toggleTag(tag: string) {
    setTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag],
    );
  }

  async function runQuery() {
    const trimmed = query.trim();
    if (!trimmed || !canSubmit || !grade || !subject) return;
    // 보내는 값과 요약이 같은 객체에서 나오게 한다 — 규칙이 아니라 구조로 일치시킨다.
    const snapshot: SubmittedConditions = {
      intent,
      grade,
      subject,
      school: school.trim(),
      currentAcademy: currentAcademy.trim(),
      tags: [...tags],
      note: note.trim(),
    };
    setLoading(true);
    setQuestions([]);
    setItems([]);
    setQuestionsDisclaimer("");
    setRelaxed([]);
    onResults([]);
    setQuestionsError("");
    setCandidatesError("");
    // 요청이 실패해도 되돌리지 않는다 — 아래 에러 문구도 이 조건으로 보낸 결과다.
    setSubmitted(snapshot);
    setFormExpanded(false);
    onExplored?.();
    try {
      const [questionsResult, recsResult] = await Promise.allSettled([
        requestConsultationQuestions({
          grade: snapshot.grade,
          subject: snapshot.subject,
          school: snapshot.school,
          current_academy: snapshot.currentAcademy,
          style_tags: snapshot.tags,
          concern: snapshot.note,
          intent: snapshot.intent,
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
        <div className="rounded-card border border-border-soft bg-surface-muted px-3 py-2.5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            {/* 제출 시점 스냅샷. 아래 질문·후보를 만든 조건이 그대로 적힌다. */}
            <p className="text-sm font-medium text-ink">{conditionSummary}</p>
            <button
              type="button"
              onClick={() => setFormExpanded(true)}
              className="text-sm font-semibold text-brand underline-offset-2 hover:underline"
            >
              {EDIT_CONDITIONS_LABEL}
            </button>
          </div>
          {conditionsChanged ? (
            <ChangedConditionsNotice
              disabled={loading || !canSubmit}
              onResubmit={() => void runQuery()}
            />
          ) : null}
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
            <div className="space-y-1.5">
              {/* 이 버튼이 버그의 진입점이었다 — 접기만 하므로 접기 전에 경고가 보여야 한다. */}
              {conditionsChanged ? (
                <ChangedConditionsNotice
                  disabled={loading || !canSubmit}
                  onResubmit={() => void runQuery()}
                />
              ) : null}
              <button
                type="button"
                onClick={() => setFormExpanded(false)}
                className="self-start text-sm text-ink-subtle underline-offset-2 hover:underline"
              >
                질문·후보 보기
              </button>
            </div>
          ) : null}
        </>
      )}

      {loading ? <p className="text-sm text-ink-subtle">{LOADING_LABEL}</p> : null}
      {questionsError ? <p className="text-sm text-warn">{questionsError}</p> : null}
      {candidatesError ? (
        <p className="text-sm text-warn">{candidatesError}</p>
      ) : null}

      {relaxed.length > 0 ? (
        <div className="space-y-0.5 rounded-card border border-border-soft bg-surface-muted px-3 py-2 text-xs text-ink-subtle">
          {/* 어떤 조건이 어떻게 넓어졌는지 문장으로. 백엔드 키(region·q)는 노출하지 않는다. */}
          <p>{RELAXED_HEADING}</p>
          {relaxedSentences.map((note) => (
            <p key={note}>{note}</p>
          ))}
        </div>
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

/** 라이브 폼이 제출 스냅샷과 달라졌을 때의 안내. 접힌 요약과 펼친 폼 두 곳에서
 *  같은 문구·같은 동작을 쓴다 — 한쪽만 고쳐 어긋나는 걸 막는다.
 *  고민을 비워 canSubmit 이 꺼지면 버튼도 꺼진다. 그때 길은 옆의 조건 바꾸기다. */
function ChangedConditionsNotice({
  disabled,
  onResubmit,
}: {
  disabled: boolean;
  onResubmit: () => void;
}) {
  return (
    <p className="mt-1.5 flex flex-wrap items-center gap-2 text-xs text-warn">
      <span>{CONDITIONS_CHANGED_NOTE}</span>
      <button
        type="button"
        disabled={disabled}
        onClick={onResubmit}
        className="font-semibold underline underline-offset-2 disabled:cursor-not-allowed disabled:opacity-40"
      >
        {RESUBMIT_LABEL}
      </button>
    </p>
  );
}
