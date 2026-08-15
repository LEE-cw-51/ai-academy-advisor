import { Card } from "@/components/ui";

const POINTS = [
  {
    icon: "🔍",
    title: "후기 찾아보는 데 오래 걸림",
    body: "맘카페, 블로그를 이리저리 뒤져도 우리 아이 상황에 맞는 후기를 찾기 어려워요.",
  },
  {
    icon: "🤔",
    title: "비교해도 확신이 안 섬",
    body: "학원마다 장점을 내세우지만, 정작 무엇이 우리 아이에게 맞는지는 알기 어려워요.",
  },
  {
    icon: "✨",
    title: "출시 후엔 AI가 맞춤 추천",
    body: "조건만 알려주시면 AI가 근거와 함께 잘 맞는 학원을 추려드릴 예정이에요.",
  },
] as const;

export function PainPointsSection() {
  return (
    <section className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <div className="grid gap-4 sm:grid-cols-3">
        {POINTS.map((p) => (
          <Card key={p.title} padding="lg" className="text-center">
            <div className="text-3xl" aria-hidden>
              {p.icon}
            </div>
            <h3 className="mt-3 font-bold text-ink">{p.title}</h3>
            <p className="mt-2 text-sm text-ink-subtle">{p.body}</p>
          </Card>
        ))}
      </div>
    </section>
  );
}
