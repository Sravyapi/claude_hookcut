import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Settings",
  description: "Manage your HookCut account settings, billing, and preferences.",
  robots: { index: false, follow: false },
};

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
