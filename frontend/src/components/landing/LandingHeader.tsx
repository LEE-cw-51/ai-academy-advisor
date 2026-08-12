import { ButtonLink } from "@/components/ui";

export function LandingHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-surface/80 backdrop-blur">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3 sm:px-6">
        <span className="text-lg font-black text-ink">학원콕</span>
        <ButtonLink href="/app" className="!px-4 !py-2 text-sm">
          무료 이용
        </ButtonLink>
      </div>
    </header>
  );
}
