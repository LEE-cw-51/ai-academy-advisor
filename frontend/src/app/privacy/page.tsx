import type { Metadata } from "next";
import { LandingFooter } from "@/components/landing/LandingFooter";
import { LandingHeader } from "@/components/landing/LandingHeader";
import { CONTACT_EMAIL } from "@/lib/contact";

export const metadata: Metadata = {
  title: "개인정보처리방침 | 학원콕",
};

export default function PrivacyPage() {
  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <LandingHeader />
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-10 sm:px-6">
        <h1 className="text-2xl font-black text-ink">개인정보처리방침</h1>
        <p className="mt-2 text-sm text-ink-subtle">시행일: 2026-08-15</p>

        <div className="mt-8 space-y-8 text-sm leading-relaxed text-ink-muted">
          <section>
            <h2 className="font-bold text-ink">이 소개 페이지가 받지 않는 정보</h2>
            <p className="mt-2">
              이 소개 페이지에는 회원가입·로그인·문의 양식이 없습니다. 이름,
              전화번호, 이메일, 자녀 정보를 입력받지 않습니다. 결제 기능이
              없으므로 결제 정보도 수집하지 않습니다.
            </p>
          </section>

          <section>
            <h2 className="font-bold text-ink">이전에 받은 알림 신청 기록</h2>
            <p className="mt-2">
              지금 소개 페이지는 이메일·카카오 아이디를 받지 않습니다. 예전
              버전에서 출시 알림 신청으로 이메일 또는 카카오 아이디를 받은
              기록이 남아 있을 수 있습니다. 해당 기록은 출시 알림 목적 외로
              쓰지 않으며, 문의하시면 확인·삭제해 드립니다.
            </p>
          </section>

          <section>
            <h2 className="font-bold text-ink">익명 클릭 기록</h2>
            <p className="mt-2">
              눌린 버튼의 종류와 시각만 기록합니다. 이름·연락처·기기 식별자는
              없고, 광고 쿠키나 추적 스크립트도 없습니다. 호스팅 업체의 기본
              접속 기록은 남을 수 있습니다.
            </p>
          </section>

          <section>
            <h2 className="font-bold text-ink">카카오톡 채널</h2>
            <p className="mt-2">
              출시 알림 신청은 카카오톡 채널 추가로 이루어지며, 그 과정은
              카카오의 방침을 따릅니다. 저희는 카카오가 채널 관리자에게 주는
              범위(친구 수 통계, 이용자가 보낸 채팅)만 확인합니다. 채널
              차단·해제는 카카오톡에서 언제든지 하실 수 있습니다.
            </p>
          </section>

          <section>
            <h2 className="font-bold text-ink">준비 중인 추천 화면</h2>
            <p className="mt-2">
              추천 화면(/app)은 직접 URL로 접근할 수 있습니다. 이 화면은
              시험용이며 결과의 정확성을 보장하지 않습니다. 여기에 입력하신
              질문 문장은 검색 기록으로 저장됩니다. 이름·연락처 등 개인정보를
              질문에 적지 말아 주세요. 이 화면에도 결제·수강 계약 기능은
              없으며, 지도는 네이버 지도를 이용합니다.
            </p>
          </section>

          <section>
            <h2 className="font-bold text-ink">제3자 제공·위탁</h2>
            <p className="mt-2">
              학원콕은 개인정보를 제3자에게 제공하거나 판매하지 않습니다.
              카카오톡 채널 추가 과정의 정보는 카카오가 처리합니다. 호스팅·지도
              업체의 접속 기록은 각 사의 정책을 따릅니다.
            </p>
          </section>

          <section>
            <h2 className="font-bold text-ink">보관과 삭제</h2>
            <p className="mt-2">
              목적 종료 시 삭제합니다. 보유 기록의 확인·삭제를 원하시면 아래로
              문의해 주세요.
            </p>
          </section>

          <section>
            <h2 className="font-bold text-ink">문의</h2>
            <p className="mt-2">
              이메일:{" "}
              <a
                href={`mailto:${CONTACT_EMAIL}`}
                className="underline underline-offset-2"
              >
                {CONTACT_EMAIL}
              </a>
              . 개인정보 보호책임자와 사업자 정보는 정식 출시 시점에 확정하여
              이 페이지에 공개합니다.
            </p>
          </section>
        </div>
      </main>
      <LandingFooter />
    </div>
  );
}
