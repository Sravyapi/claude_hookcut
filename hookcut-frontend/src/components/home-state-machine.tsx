"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { api } from "@/lib/api";
import type { Hook, Step, VideoMeta, TaskStatus } from "@/lib/types";
import { usePollTask } from "@/hooks/usePollTask";
import Header from "@/components/header";
import { ProgressStep } from "@/components/progress-step";
import { HooksStep } from "@/components/hooks-step";
import { ShortsStep } from "@/components/shorts-step";
import { Footer } from "@/components/footer";
import { slideRight } from "@/lib/motion";
import { AnalyzeContext } from "@/contexts/analyze-context";

// ── Workflow persistence ─────────────────────────────────────────────────────

const STORAGE_KEY = "hookcut_workflow";
const STORAGE_TTL_MS = 2 * 60 * 60 * 1000; // 2 hours

interface PersistedWorkflow {
  step: Step;
  sessionId: string;
  taskId: string;
  videoTitle: string;
  shortIds: string[];
  savedAt: number;
}

function saveWorkflow(state: Omit<PersistedWorkflow, "savedAt">) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...state, savedAt: Date.now() }));
  } catch {}
}

function clearWorkflow() {
  try { localStorage.removeItem(STORAGE_KEY); } catch {}
}

function loadWorkflow(): PersistedWorkflow | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw) as PersistedWorkflow;
    if (Date.now() - data.savedAt > STORAGE_TTL_MS) {
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return data;
  } catch { return null; }
}

function extractErrorMessage(err: unknown, fallback: string): string {
  if (typeof err === "string") return err || fallback;
  if (err instanceof Error) return err.message || fallback;
  if (err && typeof err === "object") {
    const e = err as Record<string, unknown>;
    if (typeof e.message === "string" && e.message) return e.message;
    if (typeof e.detail === "string" && e.detail) return e.detail;
    if (Array.isArray(e.detail) && e.detail.length > 0) {
      const first = e.detail[0] as Record<string, unknown>;
      if (typeof first?.msg === "string") return first.msg;
    }
  }
  return fallback;
}

function ErrorBanner({ error, onDismiss }: { error: string; onDismiss: () => void }) {
  return (
    <AnimatePresence>
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -12 }}
          className="fixed top-16 left-0 right-0 z-40 px-4 py-2"
        >
          <div className="max-w-2xl mx-auto p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-3">
            <svg
              className="w-4 h-4 shrink-0"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
              />
            </svg>
            <span>{error}</span>
            <button
              onClick={onDismiss}
              className="ml-auto text-red-400/60 hover:text-red-400 transition-colors"
              aria-label="Dismiss error"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

interface Props {
  marketingContent: React.ReactNode;
}

export default function HomeStateMachine({ marketingContent }: Props) {
  const [step, setStep] = useState<Step>("input");
  const [sessionId, setSessionId] = useState("");
  const [taskId, setTaskId] = useState("");
  const [videoTitle, setVideoTitle] = useState("");
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState("Starting analysis...");
  const [hooks, setHooks] = useState<Hook[]>([]);
  const [regenerationCount, setRegenerationCount] = useState(0);
  const [shortIds, setShortIds] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [analysisElapsed, setAnalysisElapsed] = useState(0);
  const analysisStartRef = useRef<number>(0);

  // ── Restore workflow on mount ──────────────────────────────────────────────
  useEffect(() => {
    const saved = loadWorkflow();
    if (!saved || saved.step === "input") return;

    setSessionId(saved.sessionId);
    setVideoTitle(saved.videoTitle);

    if (saved.step === "analyzing" && saved.taskId) {
      setTaskId(saved.taskId);
      setStep("analyzing");
    } else if (saved.step === "hooks") {
      api.getHooks(saved.sessionId)
        .then((data) => {
          setHooks(data.hooks);
          setRegenerationCount(data.regeneration_count);
          setStep("hooks");
        })
        .catch(() => clearWorkflow());
    } else if (saved.step === "shorts" && saved.shortIds.length > 0) {
      setShortIds(saved.shortIds);
      setStep("shorts");
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Persist workflow on every step/session change ──────────────────────────
  useEffect(() => {
    if (step === "input") {
      clearWorkflow();
      return;
    }
    saveWorkflow({ step, sessionId, taskId, videoTitle, shortIds });
  }, [step, sessionId, taskId, videoTitle, shortIds]);

  const handlePollComplete = useCallback(
    async (status: TaskStatus) => {
      const result = status.result;
      if (result?.error) {
        const msg =
          typeof result.error === "string"
            ? result.error
            : extractErrorMessage(result.error as unknown, "Analysis failed. Please try again.");
        setError(msg);
        setStep("input");
        return;
      }
      try {
        const hooksData = await api.getHooks(sessionId);
        setHooks(hooksData.hooks);
        setRegenerationCount(hooksData.regeneration_count);
        if (analysisStartRef.current) {
          setAnalysisElapsed(Math.round((Date.now() - analysisStartRef.current) / 1000));
        }
        setStep("hooks");
      } catch (err) {
        console.warn("Failed to load hooks:", err);
        setError("Failed to load hooks. Please try again.");
        setStep("input");
      }
    },
    [sessionId]
  );

  const handlePollError = useCallback((error: string) => {
    setError(error);
    setStep("input");
  }, []);

  const handlePollProgress = useCallback((progress: number, stage: string) => {
    setProgress(progress);
    setStage(stage);
  }, []);

  const { stopPolling } = usePollTask(
    taskId || null,
    sessionId || null,
    handlePollComplete,
    handlePollError,
    handlePollProgress
  );

  const resetAll = useCallback(() => {
    stopPolling();
    clearWorkflow();
    setStep("input");
    setSessionId("");
    setTaskId("");
    setVideoTitle("");
    setProgress(0);
    setStage("Starting analysis...");
    setHooks([]);
    setRegenerationCount(0);
    setShortIds([]);
    setError("");
    setIsRegenerating(false);
    setAnalysisElapsed(0);
    analysisStartRef.current = 0;
  }, [stopPolling]);

  const handleAnalyze = useCallback(
    async (url: string, niche: string, language: string, meta: VideoMeta) => {
      setError("");
      setVideoTitle(meta.title);
      setProgress(0);
      setStage("Submitting analysis...");
      setStep("analyzing");
      analysisStartRef.current = Date.now();
      try {
        const result = await api.analyze(url, niche, language);
        setSessionId(result.session_id);
        setTaskId(result.task_id);
      } catch (err) {
        setError(extractErrorMessage(err, "Failed to start analysis. Please try again."));
        setStep("input");
      }
    },
    []
  );

  const handleRegenerate = useCallback(async () => {
    if (!sessionId) return;
    setIsRegenerating(true);
    try {
      const result = await api.regenerateHooks(sessionId);
      setRegenerationCount(result.regeneration_count);
      setProgress(0);
      setStage("Regenerating hooks...");
      setStep("analyzing");
      analysisStartRef.current = Date.now();
      setTaskId(result.task_id);
    } catch (err) {
      setError(extractErrorMessage(err, "Regeneration failed. Please try again."));
    } finally {
      setIsRegenerating(false);
    }
  }, [sessionId]);

  const handleSelectHooks = useCallback(
    async (
      hookIds: string[],
      captionStyle: string = "clean",
      timeOverrides: Record<string, { start_seconds: number; end_seconds: number }> = {}
    ) => {
      if (!sessionId) return;
      try {
        const result = await api.selectHooks(sessionId, hookIds, captionStyle, timeOverrides);
        setShortIds(result.short_ids);
        setStep("shorts");
      } catch (err) {
        setError(extractErrorMessage(err, "Failed to start short generation. Please try again."));
      }
    },
    [sessionId]
  );

  // ── Marketing / input step ───────────────────────────────────────────────────

  if (step === "input") {
    return (
      <AnalyzeContext.Provider value={handleAnalyze}>
        <Header />
        <ErrorBanner error={error} onDismiss={() => setError("")} />
        {marketingContent}
      </AnalyzeContext.Provider>
    );
  }

  // ── Analyze / hooks / shorts steps ──────────────────────────────────────────

  return (
    <>
      <Header onReset={resetAll} />
      <ErrorBanner error={error} onDismiss={() => setError("")} />

      <main id="main-content" className="pt-24 pb-12 px-6">
        <AnimatePresence mode="wait">
          {step === "analyzing" && (
            <motion.div
              key="analyzing"
              variants={slideRight}
              initial="hidden"
              animate="show"
              exit="exit"
            >
              <ProgressStep
                progress={progress}
                videoTitle={videoTitle}
                startTime={analysisStartRef.current}
              />
            </motion.div>
          )}

          {step === "hooks" && (
            <motion.div
              key="hooks"
              variants={slideRight}
              initial="hidden"
              animate="show"
              exit="exit"
            >
              <HooksStep
                hooks={hooks}
                videoTitle={videoTitle}
                regenerationCount={regenerationCount}
                onSelectHooks={handleSelectHooks}
                onRegenerate={handleRegenerate}
                isRegenerating={isRegenerating}
                analysisElapsed={analysisElapsed}
              />
            </motion.div>
          )}

          {step === "shorts" && (
            <motion.div
              key="shorts"
              variants={slideRight}
              initial="hidden"
              animate="show"
              exit="exit"
            >
              <ShortsStep shortIds={shortIds} onReset={resetAll} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <Footer />
    </>
  );
}
