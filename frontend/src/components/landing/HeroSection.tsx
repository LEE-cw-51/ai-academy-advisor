import { Badge, Button, ButtonLink } from "@/components/ui";

interface HeroSectionProps {
  onRequestWaitlist: () => void;
}

export function HeroSection({ onRequestWaitlist }: HeroSectionProps) {
  return (
    <section className="mx-auto max-w-5xl px-4 pb-10 pt-14 text-center sm:px-6 sm:pt-20">
      <Badge tone="brand">하남 미사 출시 알림 신청 중</Badge>
      <h1 className="mx-auto mt-5 max-w-2xl text-3xl font-black leading-tight text-ink sm:text-4xl">
        3분 만에 우리 아이에게
        <br />딱 맞는 학원을 찾아드려요.
      </h1>
      <p className="mx-auto mt-4 max-w-xl text-sm text-ink-subtle sm:text-base">
        학교, 학년, 과목, 학습 스타일만 입력하면 AI가 우리 아이에게 가장 잘
        맞는 학원을 골라드립니다.
      </p>
      <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
        <ButtonLink href="/app" className="!px-6 !py-3 text-base">
          무료 이용
        </ButtonLink>
        <Button
          variant="secondary"
          className="!px-6 !py-3 text-base"
          onClick={onRequestWaitlist}
        >
          출시 알림 신청하기
        </Button>
      </div>
    </section>
  );
}
