/** 3문항 미니 점검의 질문·선택지·결과 문구 정본. 서버에 저장하지 않는다. */

export const ANSWERS = [
  { id: "well", label: "잘 되고 있어요" },
  { id: "sometimes", label: "가끔 아쉬워요" },
  { id: "needs_work", label: "개선이 필요해요" },
  { id: "unknown", label: "잘 모르겠어요" },
] as const;

export type AnswerId = (typeof ANSWERS)[number]["id"];

export type ResultKind = "stable" | "check_needed" | "needs_attention";

export interface CheckQuestion {
  id: string;
  prompt: string;
  counseling: Partial<Record<AnswerId, string>>;
}

export const QUESTIONS: CheckQuestion[] = [
  {
    id: "fit",
    prompt: "우리 아이는 지금 수업을 자신의 수준에 맞게 따라가고 있나요?",
    counseling: {
      well: "아이의 현재 수준을 어떤 근거로 판단했고, 다음 평가 전까지 무엇을 관찰하나요?",
      sometimes:
        "수업이 너무 쉽거나 어렵지 않은지, 아이 수준에 맞춰 진도를 조절해 주시나요?",
      needs_work:
        "지금 반의 진도와 난이도가 아이 수준과 맞는지, 최근 수업에서 어떻게 판단하고 계신가요?",
      unknown:
        "아이의 현재 학습 수준을 어떤 기준으로 진단하고, 수업 난이도에 어떻게 반영하나요?",
    },
  },
  {
    id: "feedback",
    prompt: "숙제·테스트·오답을 통해 부족한 부분이 꾸준히 관리되고 있나요?",
    counseling: {
      well: "숙제·테스트·오답에서 반복되는 유형은 무엇이며, 다음 보완 계획은 무엇인가요?",
      sometimes:
        "숙제와 테스트 결과를 학부모가 어떤 방식으로, 얼마나 자주 확인할 수 있나요?",
      needs_work: "오답이 반복될 때 어떤 피드백과 보충을 하시나요?",
      unknown:
        "결석, 오답 누적, 이해 부족이 있을 때 어떤 보충 수업 또는 클리닉을 제공하나요?",
    },
  },
  {
    id: "climate",
    prompt: "아이에게 강사·친구·수업 분위기가 편안하고 긍정적인가요?",
    counseling: {
      well: "아이가 질문하거나 이해를 표현하기 어려울 때, 어떤 방식으로 확인하고 돕나요?",
      sometimes: "아이가 수업 시간에 질문하거나 어려움을 말하기 편한 분위기인가요?",
      needs_work:
        "아이와 강사·친구 관계가 불편하다면, 반 조정이나 상담은 어떻게 진행되나요?",
      unknown:
        "담당 강사와 학부모가 아이의 수업 적응·또래 관계를 어떻게 공유하나요?",
    },
  },
];

export const RESULT_COPY: Record<
  ResultKind,
  { headline: string; body: string; next: string }
> = {
  stable: {
    headline: "전반적으로 안정적이에요",
    body: "현재 학습 환경이 아이에게 잘 맞는 부분이 있어 보여요.",
    next: "같은 세 가지 기준으로, 한 학기에 한 번씩 다시 점검해 보세요.",
  },
  check_needed: {
    headline: "일부 확인이 필요해 보여요",
    body: "현재 학원에 구체적으로 확인해 볼 항목이 있어요.",
    next: "아래 질문을 상담 때 그대로 사용해 보세요.",
  },
  needs_attention: {
    headline: "한 번 더 살펴볼 시점일 수 있어요",
    body: "수업 방식이나 학습 환경을 한 번 더 점검해 볼 시점일 수 있어요.",
    next: "현재 학원에 보완을 먼저 물어본 뒤, 필요하면 다른 선택지도 비교해 보세요.",
  },
};

/** 학원을 좋음/나쁨으로 나누지 않는다. 확인이 필요한 영역만 가른다. */
export function classifyResult(answers: AnswerId[]): ResultKind {
  if (answers.includes("needs_work")) return "needs_attention";
  const unknownCount = answers.filter((answer) => answer === "unknown").length;
  const sometimesCount = answers.filter((answer) => answer === "sometimes").length;
  if (unknownCount > 0 || sometimesCount >= 2) return "check_needed";
  return "stable";
}

export const COUNSELING_HEADING_STABLE = "다음 상담에서 확인해 보세요";
export const COUNSELING_HEADING_DEFAULT = "상담 때 물어보세요";

export const COUNSELING_PRIORITY: AnswerId[] = [
  "needs_work",
  "unknown",
  "sometimes",
  "well",
];

export function pickCounselingQuestions(answers: AnswerId[]): string[] {
  const picked: string[] = [];
  for (const level of COUNSELING_PRIORITY) {
    QUESTIONS.forEach((question, index) => {
      if (answers[index] !== level) return;
      const prompt = question.counseling[level];
      if (prompt) picked.push(prompt);
    });
    if (picked.length >= 3) break;
  }
  return picked.slice(0, 3);
}
