import Image from "next/image";
import { Badge, Button } from "@/components/ui";

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
      {/* 410 = data/academies/*.json 중 주소에 "미사"가 포함된 실측값 (전체 411곳,
          나머지 1곳은 덕풍동). 카피에 쓰는 숫자는 반드시 정본에서 다시 세고 고친다. */}
      <h1 className="mx-auto mt-5 max-w-2xl break-keep text-3xl font-black leading-tight text-ink sm:text-4xl">
        하남 미사 학원 410곳,
        <br />
        우리 아이에게 맞는 곳부터
      </h1>
      <p className="mx-auto mt-4 max-w-xl text-sm text-ink-subtle sm:text-base">
        경기도 공공데이터 기준 미사 지역 등록 학원·교습소 410곳을 모았습니다.
        여기에 학년·과목·학습 스타일을 더해 맞는 곳을 추려드리는 서비스를
        준비하고 있습니다.
      </p>
      <div className="mt-5 flex flex-col items-center justify-center gap-3">
        <Button className="!px-6 !py-3 text-base" onClick={onRequestWaitlist}>
          카카오톡으로 무료 출시 알림 받기
        </Button>
        {/* WaitlistModal이 모달 안에서만 보여주던 세 가지 사실을 버튼 옆으로 끌어올린 것.
            새 약속을 만들지 않는다 — 문구를 바꾸려면 WaitlistModal도 함께 고친다. */}
        <p className="text-xs text-ink-subtle">
          무료 · 개인정보 입력 없음 · 언제든 차단 가능
        </p>
      </div>
    </section>
  );
}
