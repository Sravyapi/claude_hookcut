"use client";

import { createContext, useContext } from "react";
import type { VideoMeta } from "@/lib/types";

export type AnalyzeHandler = (
  url: string,
  niche: string,
  language: string,
  meta: VideoMeta
) => void;

export const AnalyzeContext = createContext<AnalyzeHandler | null>(null);

export function useAnalyze(): AnalyzeHandler {
  const fn = useContext(AnalyzeContext);
  if (!fn) throw new Error("useAnalyze must be used inside AnalyzeContext.Provider");
  return fn;
}
