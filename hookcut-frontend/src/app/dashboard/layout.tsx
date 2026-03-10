import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Dashboard",
  description: "Your HookCut dashboard. View analysis history, credit balance, and create new YouTube Shorts.",
  robots: { index: false, follow: false },
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
