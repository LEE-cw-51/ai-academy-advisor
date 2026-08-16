import Image from "next/image";
import { Badge, Button, Disclaimer } from "@/components/ui";

interface HeroSectionProps {
  onRequestWaitlist: () => void;
}

export function HeroSection({ onRequestWaitlist }: HeroSectionProps) {
  return (
    <section className="mx-auto max-w-5xl px-4 pb-10 pt-8 text-center sm:px-6 sm:pt-16">
      <Image
        src="/logo.png"
        alt="학원콕 — 우리 아이에게 맞는 학원을 찾다."
        width={1254}
        height={1254}
        priority
        className="mx-auto h-28 w-28 sm:h-36 sm:w-36"
      />
      <Badge tone="warn" className="mt-4">정식 출시 준비 중 · 하남 미사</Badge>
      {/* break-keep: 한글 단어 중간에서 줄이 끊기지 않게 한다 (375px에서 "서비/스," 방지) */}
      <h1 className="mx-auto mt-5 max-w-2xl break-keep text-3xl font-black leading-tight text-ink sm:text-4xl">
        유명한 학원보다,
        <br />
        우리 아이에게 맞는 학원
      </h1>
      <p className="mx-auto mt-4 max-w-xl text-sm text-ink-subtle sm:text-base">
        맘카페·블로그·당근을 찾아보고 여러 학원을 직접 비교해도, 우리 아이에게
        맞는 곳을 고르기는 쉽지 않습니다. 학원콕은 하남 미사 학원 정보를 바탕으로
        아이의 학년·과목·학습 스타일에 맞는 선택을 도울 서비스를 준비하고 있습니다.
      </p>
      <div className="mt-5 flex flex-col items-center justify-center gap-3">
        <Button className="!px-6 !py-3 text-base" onClick={onRequestWaitlist}>
          카카오톡으로 무료 출시 알림 받기
        </Button>
        <p className="text-xs text-ink-subtle">
          비용 없음 · 수강 신청/결제 아님 · 출시 소식만 안내
        </p>
      </div>
      <Disclaimer className="mx-auto mt-5 max-w-xl text-left">
        지금 이 사이트에서 하실 수 있는 것은 출시 알림 신청뿐입니다. 학원
        추천·비교·상담 연결, 결제·수강 계약·예약금 결제 기능은 제공하지
        않습니다.
      </Disclaimer>
    </section>
  );
}
