import Image from "next/image";
import Link from "next/link";

/** "정식 출시 준비 중" 배지는 HeroSection이 지역까지 붙여 보여준다.
 *  헤더에서 같은 배지를 반복하면 스크롤 내내 부정 신호가 따라다녀 여기서는 뺐다. */
export function LandingHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-surface/80 backdrop-blur">
      <div className="mx-auto flex max-w-5xl items-center px-4 py-3 sm:px-6">
        <Link href="/" aria-label="학원콕 홈">
          <Image
            src="/logo.png"
            alt="학원콕"
            width={1254}
            height={1254}
            priority
            className="h-9 w-9 sm:h-10 sm:w-10"
          />
        </Link>
      </div>
    </header>
  );
}
