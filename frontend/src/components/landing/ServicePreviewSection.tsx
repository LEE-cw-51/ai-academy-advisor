import { Badge, Card, Disclaimer } from "@/components/ui";

/** 실제 학원 데이터가 아니다 — data/academies/*.json을 참조하지 않는다.
 *  OO/△△ 표기는 docs/design/academy-kok-landing.html 목업의 관례를 따른다. */
const EXAMPLE_ITEMS = [
  {
    rank: 1,
    name: "OO수학학원",
    tagline: "소수정예 · 내신 대비 · 도보 6분",
  },
  {
    rank: 2,
    name: "△△영어학원",
    tagline: "그룹수업 · 선행 · 도보 9분",
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
