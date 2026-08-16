import { Badge, Card, Disclaimer } from "@/components/ui";

/** 실제 학원 데이터가 아니다 — data/academies/*.json을 참조하지 않는다.
 *  OO/△△ 표기는 docs/design/academy-kok-landing.html 목업의 관례를 따른다. */
const EXAMPLE_ITEMS = [
  {
    rank: 1,
    name: "OO수학학원",
    tagline: "소수정예 · 내신 대비 · 도보 6분",
    reason: "아이가 경쟁 분위기에 예민하다고 하셔서 소수정예 위주로 골랐어요.",
  },
  {
    rank: 2,
    name: "△△영어학원",
    tagline: "그룹수업 · 선행 · 도보 9분",
    reason: "또래와 같이 할 때 더 잘한다고 하셔서 그룹수업을 함께 담았어요.",
  },
] as const;

/** 텍스트 전용 정적 예시. RecommendationCard(app)와 시각 스타일만 비슷하고
 *  onClick·Link·API 호출이 전혀 없다 — 클릭해도 아무 일도 일어나지 않는다. */
export function ServicePreviewSection() {
  return (
    <section className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <h2 className="text-center text-xl font-bold text-ink sm:text-2xl">
        서비스 화면 예시
      </h2>
      <p className="mx-auto mt-2 max-w-xl text-center text-sm text-ink-subtle">
        정식 출시 후 이런 모습으로 맞춤 추천을 보여드릴 예정이에요.
      </p>

      <div className="mx-auto mt-6 max-w-md space-y-3">
        {EXAMPLE_ITEMS.map((item) => (
          <Card key={item.rank} padding="sm">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <Badge tone="rank">{item.rank}순위</Badge>
              <Badge tone="brand">AI 추천 예시</Badge>
              <h3 className="font-semibold text-ink">{item.name}</h3>
            </div>
            <p className="text-sm text-ink-muted">{item.tagline}</p>
            {/* 추천 이유를 대는 것이 이 제품의 차별점이라 예시에도 함께 보여준다.
                문구는 어디까지나 예시다 — 실제 추천 근거는 출시 후 AI가 생성한다. */}
            <div className="mt-3 rounded-btn bg-surface-muted px-3 py-2">
              <p className="text-xs font-semibold text-ink-muted">
                💡 왜 추천했나요?
              </p>
              <p className="mt-1 text-xs text-ink-subtle">“{item.reason}”</p>
            </div>
            <p className="mt-3 text-xs text-ink-subtle">
              전화 · 상세 · 길찾기 — 정식 출시 후 제공
            </p>
          </Card>
        ))}
      </div>

      <Disclaimer className="mx-auto mt-4 max-w-md">
        실제 학원 정보가 아닌 예시이며, 정식 출시 후 이 화면으로 제공될
        예정입니다.
      </Disclaimer>
    </section>
  );
}
