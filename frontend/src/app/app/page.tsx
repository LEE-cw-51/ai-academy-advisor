import type { Metadata } from "next";
import { AppShell } from "@/components/app/AppShell";

export const metadata: Metadata = {
  robots: { index: false, follow: false },
};

export default function AppPage() {
  return <AppShell />;
}
