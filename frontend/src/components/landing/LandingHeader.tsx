import Image from "next/image";
import Link from "next/link";
import { Badge } from "@/components/ui";

export function LandingHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-surface/80 backdrop-blur">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3 sm:px-6">
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
        <Badge tone="warn">정식 출시 준비 중</Badge>
      </div>
    </header>
  );
}
