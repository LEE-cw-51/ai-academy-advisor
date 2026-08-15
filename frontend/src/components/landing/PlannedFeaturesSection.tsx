import { Card, Disclaimer } from "@/components/ui";

const FEATURES = [
  {
    title: "맞춤 학원 추천",
    body: "학년·과목·학습 스타일을 알려주시면, 조건에 맞는 학원을 추려드릴 예정입니다.",
  },
  {
    title: "학원 정보 비교",
    body: "수업 형태, 커리큘럼, 셔틀 운행 여부처럼 확인된 정보를 나란히 비교하실 수 있게 준비 중입니다.",
  },
  {
    title: "상담 연결",
    body: "마음에 드는 학원에 직접 문의하실 수 있도록 연결하는 기능을 준비 중입니다.",
  },
] as const;

export function PlannedFeaturesSection() {
  return (
    <section className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <h2 className="text-center text-xl font-bold text-ink sm:text-2xl">
        정식 출시 후 제공될 기능
      </h2>
      <p className="mx-auto mt-2 max-w-xl text-center text-sm text-ink-subtle">
        아래 기능은 준비 중이며, 아직 이용하실 수 없습니다.
      </p>
      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        {FEATURES.map((f) => (
          <Card key={f.title} padding="lg" className="text-center">
            <h3 className="font-bold text-ink">{f.title}</h3>
            <p className="mt-2 text-sm text-ink-subtle">{f.body}</p>
          </Card>
        ))}
      </div>
      <Disclaimer className="mt-6">
        학원콕은 학원을 중개하거나 수강료를 대신 받지 않습니다. 이 사이트에는
        결제·수강 계약·예약금 결제 기능이 없습니다.
      </Disclaimer>
    </section>
  );
}
