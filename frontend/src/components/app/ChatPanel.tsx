"use client";

import { useCallback, useMemo, useState } from "react";
import { Badge, Chip } from "@/components/ui";
import { requestAiRecommendations, trackEvent } from "@/lib/api";
import type { AiRecommendationItem, ClickEventType } from "@/lib/types";
import { ApiError } from "@/lib/types";
import { AcademyDetailModal } from "./AcademyDetailModal";
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
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [items, setItems] = useState<AiRecommendationItem[]>([]);
  const [relaxed, setRelaxed] = useState<string[]>([]);
  const [detailId, setDetailId] = useState<number | null>(null);

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

  const canSubmit = Boolean(grade || subject || school.trim() || tags.length || note.trim());

  function toggleTag(tag: string) {
    setTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag],
    );
  }

  async function runQuery() {
    const trimmed = query.trim();
    if (!trimmed || !canSubmit) return;
    setLoading(true);
    setError("");
    try {
      const res = await requestAiRecommendations(trimmed, 3);
      setItems(res.items);
      setRelaxed(res.relaxed);
      onResults(res.items);
      if (res.items[0]) {
        onSelectAcademy(res.items[0].academy.id);
      }
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "추천을 불러오지 못했어요. API 서버가 실행 중인지 확인해 주세요.",
      );
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
          <h2 className="text-lg font-bold text-ink">AI 학원 추천</h2>
          <Badge tone="brand">하남 미사</Badge>
        </div>
        <p className="text-sm text-ink-subtle">
          조건을 고르고, 추가로 원하는 점을 적어 주세요.
        </p>
      </div>

      <div className="space-y-3.5">
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
          aria-label="추천 받기"
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

      {error ? <p className="text-sm text-warn">{error}</p> : null}

      {relaxed.length > 0 ? (
        <p className="text-xs text-ink-subtle">
          일부 조건을 완화해 찾았어요: {relaxed.join(", ")}
        </p>
      ) : null}

      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto pr-1">
        {items.length === 0 && !loading && !error ? (
          <p className="text-sm text-ink-subtle">
            조건을 고른 뒤 전송하면 맞춤 학원이 여기에 표시됩니다.
          </p>
        ) : null}
        {items.map((item, idx) => (
          <RecommendationCard
            key={item.academy.id}
            item={item}
            rank={idx + 1}
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
