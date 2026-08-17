import { Card } from "@/components/ui";

/** 본문은 명사구로 짧게 둔다. 시점("출시하면")은 섹션 제목이 이미 말하므로
 *  카드마다 "~할 예정입니다 / 준비 중입니다"를 되풀이하지 않는다. */
const FEATURES = [
  {
    title: "맞춤 학원 추천",
    body: "학년·과목·성향에 맞는 곳을 근거와 함께",
  },
  {
    title: "학원 정보 비교",
    body: "수업 형태·커리큘럼·셔틀 등 확인된 정보만 나란히",
  },
  {
    title: "상담 연결",
    body: "마음에 드는 학원에 바로 문의",
  },
] as const;

export function PlannedFeaturesSection() {
  return (
    <section className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <h2 className="text-center text-xl font-bold text-ink sm:text-2xl">
        출시하면 이렇게 쓰시게 됩니다
      </h2>
      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        {FEATURES.map((f) => (
          <Card key={f.title} padding="lg" className="border border-border-soft text-center shadow-none">
            <h3 className="font-bold text-ink">{f.title}</h3>
            {/* break-keep: 좁은 폭에서 단어 중간이 끊기지 않게 한다. */}
            <p className="mt-2 break-keep text-sm text-ink-muted">{f.body}</p>
          </Card>
        ))}
      </div>
    </section>
  );
}
