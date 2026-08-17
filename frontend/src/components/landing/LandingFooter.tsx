import Link from "next/link";
import { Disclaimer } from "@/components/ui";
import { CONTACT_EMAIL } from "@/lib/contact";
import { KakaoChannelLink } from "./KakaoChannelLink";

export function LandingFooter() {
  return (
    <footer className="border-t border-border bg-surface">
      <div className="mx-auto max-w-5xl space-y-4 px-4 py-8 sm:px-6">
        {/* `/`와 `/privacy`가 공유하는 푸터다. "알림 신청만 가능"은 소개 페이지로
            한정하고, 사이트 전체에 참인 "중개·결제·수강 계약 없음"만 범위를 넓힌다.
            본문 섹션의 유보 문구를 여기로 통합했으므로, 고지를 지울 때는 이 블록에
            같은 내용이 남아 있는지 먼저 확인한다. */}
        <Disclaimer>
          학원콕은 아직 정식 출시 전입니다. 이 소개 페이지에서는 무료 출시 알림
          신청만 가능하며, 맞춤 추천·비교·상담 연결은 정식 출시 후 제공될
          예정입니다. 학원을 중개하거나 수강료를 대신 받지 않으며,
          결제·수강 계약·예약금 결제 기능은 어디에서도 제공하지 않습니다.
        </Disclaimer>
        <p className="text-xs text-ink-subtle">
          학원콕 · 하남 미사 AI 학원 추천 (정식 출시 준비 중)
        </p>
        <p className="text-xs text-ink-subtle">
          문의:{" "}
          <a
            href={`mailto:${CONTACT_EMAIL}`}
            className="underline underline-offset-2"
          >
            {CONTACT_EMAIL}
          </a>
        </p>
        <p className="text-xs text-ink-subtle">
          <Link href="/privacy" className="underline underline-offset-2">
            개인정보처리방침
          </Link>
          {" · "}
          <KakaoChannelLink className="underline underline-offset-2">
            카카오톡 채널
          </KakaoChannelLink>
        </p>
        <p className="text-xs text-ink-subtle">
          사업자 정보는 정식 출시 시점에 이곳에 표기할 예정입니다.
        </p>
      </div>
    </footer>
  );
}
