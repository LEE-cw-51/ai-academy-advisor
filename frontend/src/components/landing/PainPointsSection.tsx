import { Card } from "@/components/ui";

/** 문제만 말하는 섹션이다. "AI가 추천해 드려요" 카드는 PlannedFeaturesSection의
 *  "맞춤 학원 추천"과 같은 말이라 뺐다 — 해결은 다음 섹션 몫이다. */
const POINTS = [
  {
    icon: "🔍",
    title: "후기 찾아보는 데 오래 걸림",
    body: "맘카페·블로그를 뒤져도 우리 아이 상황에 맞는 후기는 찾기 어렵죠.",
  },
  {
    icon: "🤔",
    title: "비교해도 확신이 안 섬",
    body: "학원마다 장점을 내세우지만, 우리 아이에게 맞는지는 알 수 없죠.",
  },
] as const;

export function PainPointsSection() {
  return (
    <section className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <div className="grid gap-4 sm:grid-cols-2">
        {POINTS.map((p) => (
          <Card key={p.title} padding="lg" className="text-center">
            <div className="text-3xl" aria-hidden>
              {p.icon}
            </div>
            <h3 className="mt-3 font-bold text-ink">{p.title}</h3>
            {/* break-keep: 375px에서 "후/기는"처럼 단어 중간이 끊기지 않게 한다. */}
            <p className="mt-2 break-keep text-sm text-ink-subtle">{p.body}</p>
          </Card>
        ))}
      </div>
    </section>
  );
}
