"use client";

import { useCallback, useState } from "react";
import { HeroSection } from "./HeroSection";
import { LandingFooter } from "./LandingFooter";
import { LandingHeader } from "./LandingHeader";
import { PainPointsSection } from "./PainPointsSection";
import { WaitlistModal } from "./WaitlistModal";
import { WaitlistSection } from "./WaitlistSection";

export function LandingPage() {
  const [waitlistOpen, setWaitlistOpen] = useState(false);

  const openWaitlist = useCallback(() => setWaitlistOpen(true), []);
  const closeWaitlist = useCallback(() => setWaitlistOpen(false), []);

  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <LandingHeader />
      <main className="flex-1">
        <HeroSection onRequestWaitlist={openWaitlist} />
        <PainPointsSection />
        <WaitlistSection onRequestWaitlist={openWaitlist} />
      </main>
      <LandingFooter />
      <WaitlistModal open={waitlistOpen} onClose={closeWaitlist} />
    </div>
  );
}
