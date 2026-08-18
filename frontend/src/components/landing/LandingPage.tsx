"use client";

import { useCallback, useRef, useState } from "react";
import { HeroSection } from "./HeroSection";
import { LandingFooter } from "./LandingFooter";
import { LandingHeader } from "./LandingHeader";
import { PlannedFeaturesSection } from "./PlannedFeaturesSection";
import { ServicePreviewSection } from "./ServicePreviewSection";
import { StickyCtaBar } from "./StickyCtaBar";
import { WaitlistModal } from "./WaitlistModal";
import { WaitlistSection } from "./WaitlistSection";

export function LandingPage() {
  const [waitlistOpen, setWaitlistOpen] = useState(false);
  const stickySentinelRef = useRef<HTMLDivElement>(null);

  const openWaitlist = useCallback(() => setWaitlistOpen(true), []);
  const closeWaitlist = useCallback(() => setWaitlistOpen(false), []);

  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <LandingHeader />
      <main className="flex-1">
        <HeroSection
          onRequestWaitlist={openWaitlist}
          ctaSentinelRef={stickySentinelRef}
        />
        <PlannedFeaturesSection />
        <ServicePreviewSection />
        <WaitlistSection onRequestWaitlist={openWaitlist} />
      </main>
      <LandingFooter />
      <div className="h-28 sm:hidden" aria-hidden />
      <StickyCtaBar
        sentinelRef={stickySentinelRef}
        suppressed={waitlistOpen}
      />
      <WaitlistModal open={waitlistOpen} onClose={closeWaitlist} />
    </div>
  );
}
