import Link from "next/link";
import { Disclaimer } from "@/components/ui";
import { CONTACT_EMAIL } from "@/lib/contact";
import { KakaoChannelCta } from "./KakaoChannelCta";
import { FOOTER_STATUS_COPY } from "./landingFacts";

export function LandingFooter() {
  return (
    <footer className="border-t border-border bg-surface">
      <div className="mx-auto max-w-5xl space-y-4 px-4 py-8 sm:px-6">
        {/* `/`와 `/privacy`·`/check`·`/checklists`가 공유하는 푸터다.
            본문 섹션의 유보 문구를 여기로 통합했으므로, 고지를 지울 때는 이 블록에
            같은 내용이 남아 있는지 먼저 확인한다. */}
        <Disclaimer>
          <p>
            {FOOTER_STATUS_COPY}
          </p>
          <p className="mt-2">
            학원을 중개하거나 수강료를 대신 받지 않으며, 결제·수강 계약·예약금
            결제 기능은 어디에서도 제공하지 않습니다.
          </p>
        </Disclaimer>
        <p className="text-xs text-ink-muted">
          학원콕 · 하남 미사 AI 학원 추천 (정식 출시 준비 중)
        </p>
        <p className="text-xs text-ink-muted">
          문의:{" "}
          <a
            href={`mailto:${CONTACT_EMAIL}`}
            className="underline underline-offset-2"
          >
            {CONTACT_EMAIL}
          </a>
        </p>
        <p className="text-xs text-ink-muted">
          <Link href="/privacy" className="underline underline-offset-2">
            개인정보처리방침
          </Link>
          {" · "}
          <KakaoChannelCta className="underline underline-offset-2">
            카카오톡 채널
          </KakaoChannelCta>
        </p>
        <p className="text-xs text-ink-muted">
          사업자 정보는 정식 출시 시점에 이곳에 표기할 예정입니다.
        </p>
      </div>
    </footer>
  );
}
