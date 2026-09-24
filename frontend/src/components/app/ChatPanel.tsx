"use client";

import { useMemo, useRef, useState } from "react";
import { Chip } from "@/components/ui";
import {
  requestAiRecommendations,
  requestConsultationQuestions,
  trackEventSafe,
} from "@/lib/api";
import type {
  AiRecommendationItem,
  ConsultationIntent,
  ConsultationQuestion,
} from "@/lib/types";
import {
  CANDIDATES_ERROR,
  CANDIDATES_HEADING,
  CONDITIONS_CHANGED_NOTE,
  EDIT_CONDITIONS_LABEL,
  FORM_HEADING,
  FORM_SUPPORT,
  INTENTS,
  LOADING_LABEL,
  MORE_DETAILS_HIDE_LABEL,
  MORE_DETAILS_LABEL,
  NO_CANDIDATES,
  NO_CANDIDATES_SEARCH_HINT,
  QUESTIONS_ERROR,
  QUESTIONS_HEADING,
  RELAXED_HEADING,
  RESUBMIT_LABEL,
  SHOW_RESULTS_LABEL,
  RETRY_LABEL,
  SUBJECT_FORM_HELPER,
  SUBJECT_HELPER,
  SUBJECT_DETAIL_LABEL,
  SUBJECT_DETAIL_HELPER,
  SUBJECT_DETAIL_PLACEHOLDER,
  SUBMIT_LABEL,
  TAGS_HEADING,
  TAGS_HELPER,
  TRUST_NOTE,
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
  subjectDetail: string;
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
  subjectDetail: string;
  note: string;
}): string {
  const chunks: string[] = [];
  if (parts.region) chunks.push(parts.region);
  if (parts.grade) chunks.push(parts.grade);
  if (parts.school.trim()) chunks.push(parts.school.trim());
  // "기타"를 고르고 실제 과목을 적었으면 그 이름을 쓴다 — "기타"만으론 신호가 없다.
  const subjectTerm =
    parts.subject === "기타" && parts.subjectDetail.trim()
      ? parts.subjectDetail.trim()
      : parts.subject;
  if (subjectTerm) chunks.push(subjectTerm);
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
  const [subjectDetail, setSubjectDetail] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [note, setNote] = useState("");
  const [currentAcademy, setCurrentAcademy] = useState("");
  const [intent, setIntent] = useState<ConsultationIntent>("find_new_academy");
  const [loading, setLoading] = useState(false);
  // 에러는 사용자 문구(QUESTIONS_ERROR·CANDIDATES_ERROR)만 보여 준다. 서버 메시지는
  // 개발자 대상이라 그대로 내보내지 않는다 — 그래서 상태도 문자열이 아니라 플래그다.
  const [questionsError, setQuestionsError] = useState(false);
  const [candidatesError, setCandidatesError] = useState(false);
  const [items, setItems] = useState<AiRecommendationItem[]>([]);
  const [questions, setQuestions] = useState<ConsultationQuestion[]>([]);
  const [questionsDisclaimer, setQuestionsDisclaimer] = useState("");
  const [relaxed, setRelaxed] = useState<string[]>([]);
  // 제출 스냅샷이 곧 "지금 화면 아래 사실을 만든 조건"이다. hasSubmitted 를 따로
  // 두면 둘이 어긋날 수 있어 파생값으로 낮춘다.
  const [submitted, setSubmitted] = useState<SubmittedConditions | null>(null);
  const [formExpanded, setFormExpanded] = useState(true);
  const [moreDetailsOpen, setMoreDetailsOpen] = useState(false);
  // 상황 제출 일련번호. 최신 요청만 상태에 반영한다 — 더블 서브밋·Enter 연타로
  // 늦게 온 응답이 새 결과를 덮어쓰는 것을 막는다 (AppShell searchSeq 와 동일).
  const querySeq = useRef(0);

  const query = useMemo(
    () =>
      buildQuery({
        region: REGION,
        grade,
        school,
        subject,
        subjectDetail,
        note,
      }),
    [grade, school, subject, subjectDetail, note],
  );

  const canSubmit = Boolean(grade && subject && note.trim());
  const hasSubmitted = submitted !== null;

  // 요약은 라이브 폼이 아니라 제출 스냅샷에서 만든다. 폼만 바꾸고 다시 보내지 않으면
  // 아래 후보·질문은 이전 조건의 사실인데 칩만 새 조건을 적어, 어떤 조건에서 나온
  // 사실인지 잘못 알린다 (docs/decision-log.md 2026-09-08 사실 우선).
  const conditionSummary = useMemo(() => {
    if (!submitted) return "";
    const subjectText =
      submitted.subject === "기타" && submitted.subjectDetail
        ? submitted.subjectDetail
        : submitted.subject;
    return [
      INTENT_SUMMARY[submitted.intent],
      submitted.grade,
      subjectText,
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
      submitted.subjectDetail !== subjectDetail.trim() ||
      submitted.school !== school.trim() ||
      submitted.currentAcademy !== currentAcademy.trim() ||
      submitted.note !== note.trim() ||
      submitted.tags.length !== tags.length ||
      submitted.tags.some((t) => !tags.includes(t))
    );
  }, [
    submitted,
    intent,
    grade,
    subject,
    subjectDetail,
    school,
    currentAcademy,
    note,
    tags,
  ]);

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
      subjectDetail: subjectDetail.trim(),
      school: school.trim(),
      currentAcademy: currentAcademy.trim(),
      tags: [...tags],
      note: note.trim(),
    };
    const seq = ++querySeq.current;
    setLoading(true);
    setQuestions([]);
    setItems([]);
    setQuestionsDisclaimer("");
    setRelaxed([]);
    onResults([]);
    setQuestionsError(false);
    setCandidatesError(false);
    // 요청이 실패해도 되돌리지 않는다 — 아래 에러 문구도 이 조건으로 보낸 결과다.
    setSubmitted(snapshot);
    setFormExpanded(false);
    onExplored?.();
    try {
      const [questionsResult, recsResult] = await Promise.allSettled([
        requestConsultationQuestions({
          grade: snapshot.grade,
          subject:
            snapshot.subject === "기타" && snapshot.subjectDetail
              ? snapshot.subjectDetail
              : snapshot.subject,
          school: snapshot.school,
          current_academy: snapshot.currentAcademy,
          style_tags: snapshot.tags,
          concern: snapshot.note,
          intent: snapshot.intent,
        }),
        // 후보는 최대 5곳. 응답을 잘라 내지 않고 온 만큼 그린다.
        requestAiRecommendations(trimmed, 5),
      ]);

      if (seq !== querySeq.current) return;

      if (questionsResult.status === "fulfilled") {
        // used_fallback이어도 200이므로 질문 본문만 보여 준다. 에러로 취급하지 않는다.
        setQuestions(questionsResult.value.questions.slice(0, 5));
        setQuestionsDisclaimer(questionsResult.value.disclaimer);
      } else {
        setQuestions([]);
        setQuestionsDisclaimer("");
        setQuestionsError(true);
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
        setCandidatesError(true);
      }
    } finally {
      if (seq === querySeq.current) setLoading(false);
    }
  }

  const anyError = questionsError || candidatesError;
  const noCandidates =
    hasSubmitted && !loading && items.length === 0 && !candidatesError;

  return (
    <div className="flex h-full min-h-0 flex-col gap-5">
      {/* 페이지 h1 은 항상 있다. 제출 뒤엔 요약 칩이 시선을 받으므로 sr-only 로
          내리고, 래퍼는 contents 로 두어 flex gap 에 빈 칸을 남기지 않는다. */}
      <div className={hasSubmitted ? "contents" : "space-y-2"}>
        <h1 id="explore-heading" className={hasSubmitted ? "sr-only" : "text-2xl font-semibold leading-snug text-ink sm:text-3xl break-keep"}>
          {FORM_HEADING}
        </h1>
        {!hasSubmitted ? (
          <>
            <p className="break-keep text-sm text-ink-muted">{FORM_SUPPORT}</p>
            <p className="break-keep text-xs text-ink-subtle">{TRUST_NOTE}</p>
          </>
        ) : null}
      </div>

      {hasSubmitted && !formExpanded ? (
        <div className="rounded-card border border-border-soft bg-surface-muted px-3 py-2.5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            {/* 제출 시점 스냅샷. 아래 후보·질문을 만든 조건이 그대로 적힌다. */}
            <p className="min-w-0 break-words text-sm font-medium text-ink">
              {conditionSummary}
            </p>
            <button
              type="button"
              onClick={() => setFormExpanded(true)}
              className="inline-flex min-h-11 items-center text-sm font-semibold text-ink underline underline-offset-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
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
          <div className="space-y-3.5">
            <FilterRow label="상황" labelId="explore-intent-label">
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

            <FilterRow label="학년" labelId="explore-grade-label">
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

            <FilterRow label="과목" labelId="explore-subject-label">
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
            {subject === "기타" ? (
              <div className="space-y-1 pl-[3.25rem]">
                <label
                  className="text-xs text-ink-subtle"
                  htmlFor="explore-subject-detail"
                >
                  {SUBJECT_DETAIL_LABEL}
                </label>
                <input
                  id="explore-subject-detail"
                  name="subject_detail"
                  type="text"
                  autoComplete="off"
                  disabled={loading}
                  value={subjectDetail}
                  onChange={(e) => setSubjectDetail(e.target.value)}
                  placeholder={SUBJECT_DETAIL_PLACEHOLDER}
                  className="w-full rounded-card border border-border bg-surface px-3 py-2 text-sm text-ink shadow-soft placeholder:text-ink-subtle focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/30 disabled:opacity-60"
                />
                <p className="text-xs text-ink-subtle">
                  {SUBJECT_DETAIL_HELPER}
                </p>
              </div>
            ) : null}
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
              className="min-h-11 w-full rounded-full bg-brand px-4 py-2.5 text-sm font-semibold text-ink-strong transition-[background-color,transform,opacity] duration-200 ease-out hover:bg-brand-dark active:scale-[0.98] motion-reduce:active:scale-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand disabled:cursor-not-allowed disabled:opacity-40 disabled:active:scale-100"
            >
              {loading ? LOADING_LABEL : SUBMIT_LABEL}
            </button>
          </div>

          <div className="space-y-2.5">
            <button
              type="button"
              disabled={loading}
              aria-expanded={moreDetailsOpen}
              aria-controls="explore-more-details"
              onClick={() => setMoreDetailsOpen((open) => !open)}
              className="inline-flex min-h-11 items-center text-sm font-medium text-ink-subtle underline-offset-2 hover:underline disabled:opacity-60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
            >
              {moreDetailsOpen ? MORE_DETAILS_HIDE_LABEL : MORE_DETAILS_LABEL}
            </button>
            {moreDetailsOpen ? (
              <div
                id="explore-more-details"
                className="space-y-3.5 rounded-card border border-border-soft bg-surface-muted px-3 py-3"
              >
                <FilterRow label="학교" htmlFor="explore-school">
                  <input
                    id="explore-school"
                    type="text"
                    name="school"
                    autoComplete="off"
                    value={school}
                    disabled={loading}
                    placeholder="학교 이름을 입력하세요 (예: 미사중학교)"
                    onChange={(e) => setSchool(e.target.value)}
                    className="min-w-0 flex-1 rounded-full border border-border bg-surface px-4 py-2 text-sm text-ink placeholder:text-ink-subtle focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/30 disabled:opacity-60"
                  />
                </FilterRow>

                <FilterRow label="학원" htmlFor="explore-current-academy">
                  <input
                    id="explore-current-academy"
                    type="text"
                    name="current_academy"
                    autoComplete="off"
                    value={currentAcademy}
                    disabled={loading}
                    placeholder="현재 다니는 학원 (없으면 비워 두세요)"
                    onChange={(e) => setCurrentAcademy(e.target.value)}
                    className="min-w-0 flex-1 rounded-full border border-border bg-surface px-4 py-2 text-sm text-ink placeholder:text-ink-subtle focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/30 disabled:opacity-60"
                  />
                </FilterRow>

                <div className="space-y-2">
                  <p
                    id="explore-tags-label"
                    className="text-sm font-medium text-ink-subtle"
                  >
                    {TAGS_HEADING}
                  </p>
                  <p className="text-xs text-ink-subtle">{TAGS_HELPER}</p>
                  <div
                    role="group"
                    aria-labelledby="explore-tags-label"
                    className="flex flex-wrap gap-2"
                  >
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
                className="inline-flex min-h-11 items-center self-start text-sm text-ink-subtle underline-offset-2 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
              >
                {SHOW_RESULTS_LABEL}
              </button>
            </div>
          ) : null}
        </>
      )}

      {/* 로딩 상태는 늘 같은 live region 에 쓴다 — 비어 있을 땐 sr-only 로 자리만 남긴다. */}
      <p
        role="status"
        aria-live="polite"
        className={loading ? "text-sm text-ink-subtle" : "sr-only"}
      >
        {loading ? LOADING_LABEL : null}
      </p>

      {anyError ? (
        <div
          role="alert"
          aria-live="assertive"
          className="space-y-1.5 rounded-card border border-warn/30 bg-warn-bg px-3 py-2.5 text-sm text-warn"
        >
          {candidatesError ? <p className="break-keep">{CANDIDATES_ERROR}</p> : null}
          {questionsError ? <p className="break-keep">{QUESTIONS_ERROR}</p> : null}
          <button
            type="button"
            disabled={loading}
            onClick={() => void runQuery()}
            className="inline-flex min-h-11 items-center font-semibold underline underline-offset-2 disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
          >
            {RETRY_LABEL}
          </button>
        </div>
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

      {/* 결과 순서: 후보 → 상담 질문. 후보 카드가 먼저 보이고, 질문은 그 뒤에 이어진다. */}
      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto pr-1">
        {items.length > 0 ? (
          <section
            aria-labelledby="explore-candidates-heading"
            className="space-y-3"
          >
            <h2
              id="explore-candidates-heading"
              className="text-sm font-semibold text-ink"
            >
              {CANDIDATES_HEADING}
            </h2>
            <p className="text-xs text-ink-subtle">{SUBJECT_HELPER}</p>
            {items.map((item) => (
              <RecommendationCard
                key={item.academy.id}
                item={item}
                selected={selectedAcademyId === item.academy.id}
                onSelect={() => onSelectAcademy(item.academy.id)}
                onShowDetail={() => onOpenDetail(item.academy.id)}
                onTrack={(event) => void trackEventSafe(item.academy.id, event)}
              />
            ))}
          </section>
        ) : null}

        {noCandidates ? (
          <div className="space-y-2 rounded-card border border-border-soft bg-surface-muted px-3 py-3">
            <p className="break-keep text-sm text-ink">{NO_CANDIDATES}</p>
            <button
              type="button"
              onClick={() => setFormExpanded(true)}
              className="inline-flex min-h-11 items-center text-sm font-semibold text-ink underline underline-offset-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
            >
              {EDIT_CONDITIONS_LABEL}
            </button>
            <p className="break-keep text-xs text-ink-subtle">
              {NO_CANDIDATES_SEARCH_HINT}
            </p>
          </div>
        ) : null}

        {questions.length > 0 ? (
          <section
            aria-labelledby="explore-questions-heading"
            className="space-y-2 rounded-card border border-border-soft bg-surface-muted px-3 py-3"
          >
            <h2
              id="explore-questions-heading"
              className="text-sm font-semibold text-ink"
            >
              {QUESTIONS_HEADING}
            </h2>
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
      </div>
    </div>
  );
}

function FilterRow({
  label,
  labelId,
  htmlFor,
  children,
}: {
  label: string;
  /** 칩 묶음 행: 라벨 span 에 id 를 주고 칩 컨테이너를 role=group 으로 묶는다. */
  labelId?: string;
  /** 텍스트 입력 행: span 대신 <label htmlFor> 로 입력과 연결한다. */
  htmlFor?: string;
  children: React.ReactNode;
}) {
  const labelClass = "w-10 shrink-0 pt-1.5 text-sm text-ink-subtle sm:pt-0";
  return (
    <div className="flex items-start gap-3 sm:items-center">
      {htmlFor ? (
        <label htmlFor={htmlFor} className={labelClass}>
          {label}
        </label>
      ) : (
        <span id={labelId} className={labelClass}>
          {label}
        </span>
      )}
      <div
        role={labelId ? "group" : undefined}
        aria-labelledby={labelId}
        className="flex min-w-0 flex-1 flex-wrap items-center gap-2"
      >
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
      <span className="break-keep">{CONDITIONS_CHANGED_NOTE}</span>
      <button
        type="button"
        disabled={disabled}
        onClick={onResubmit}
        className="inline-flex min-h-11 items-center font-semibold underline underline-offset-2 disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
      >
        {RESUBMIT_LABEL}
      </button>
    </p>
  );
}
