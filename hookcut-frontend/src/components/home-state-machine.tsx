"use client";

import { useReducer, useCallback, useRef, useEffect } from "react";
import { useSession } from "next-auth/react";
import { AnimatePresence, motion } from "framer-motion";
import { api } from "@/lib/api";
import { extractErrorMessage } from "@/lib/utils";
import type { Hook, Step, VideoMeta, TaskStatus } from "@/lib/types";
import { usePollTask } from "@/hooks/usePollTask";
import Header from "@/components/header";
import { AuthenticatedHome } from "@/components/authenticated-home";
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
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ ...state, savedAt: Date.now() }));
  } catch {}
}

function clearWorkflow() {
  try { sessionStorage.removeItem(STORAGE_KEY); } catch {}
}

function loadWorkflow(): PersistedWorkflow | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw) as PersistedWorkflow;
    if (Date.now() - data.savedAt > STORAGE_TTL_MS) {
      sessionStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return data;
  } catch { return null; }
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

// ── State machine ─────────────────────────────────────────────────────────────

type AppState =
  | { step: "input"; error: string }
  | {
      step: "analyzing";
      sessionId: string;
      taskId: string;
      videoTitle: string;
      progress: number;
      stage: string;
      error: string;
    }
  | {
      step: "hooks";
      sessionId: string;
      videoTitle: string;
      hooks: Hook[];
      regenerationCount: number;
      isRegenerating: boolean;
      analysisElapsed: number;
      error: string;
    }
  | { step: "shorts"; sessionId: string; shortIds: string[]; error: string };

type Action =
  | { type: "ANALYZE_STARTED"; sessionId: string; taskId: string; videoTitle: string }
  | { type: "POLL_PROGRESS"; progress: number; stage: string }
  | { type: "HOOKS_LOADED"; hooks: Hook[]; regenerationCount: number; elapsed: number }
  | { type: "RESTORE_HOOKS"; sessionId: string; videoTitle: string; hooks: Hook[]; regenerationCount: number }
  | { type: "RESTORE_SHORTS"; sessionId: string; shortIds: string[] }
  | { type: "REGENERATE_STARTED"; taskId: string; regenerationCount: number }
  | { type: "SHORTS_SELECTED"; shortIds: string[] }
  | { type: "SET_ERROR"; error: string }
  | { type: "DISMISS_ERROR" }
  | { type: "RESET" };

const initialState: AppState = { step: "input", error: "" };

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case "ANALYZE_STARTED":
      return {
        step: "analyzing",
        sessionId: action.sessionId,
        taskId: action.taskId,
        videoTitle: action.videoTitle,
        progress: 0,
        stage: "Submitting analysis...",
        error: "",
      };

    case "POLL_PROGRESS":
      if (state.step !== "analyzing") return state;
      return { ...state, progress: action.progress, stage: action.stage };

    case "HOOKS_LOADED":
      if (state.step !== "analyzing") return state;
      return {
        step: "hooks",
        sessionId: state.sessionId,
        videoTitle: state.videoTitle,
        hooks: action.hooks,
        regenerationCount: action.regenerationCount,
        isRegenerating: false,
        analysisElapsed: action.elapsed,
        error: "",
      };

    case "RESTORE_HOOKS":
      return {
        step: "hooks",
        sessionId: action.sessionId,
        videoTitle: action.videoTitle,
        hooks: action.hooks,
        regenerationCount: action.regenerationCount,
        isRegenerating: false,
        analysisElapsed: 0,
        error: "",
      };

    case "RESTORE_SHORTS":
      return {
        step: "shorts",
        sessionId: action.sessionId,
        shortIds: action.shortIds,
        error: "",
      };

    case "REGENERATE_STARTED":
      if (state.step !== "hooks") return state;
      return {
        step: "analyzing",
        sessionId: state.sessionId,
        taskId: action.taskId,
        videoTitle: state.videoTitle,
        progress: 0,
        stage: "Regenerating hooks...",
        error: "",
      };

    case "SHORTS_SELECTED":
      if (state.step !== "hooks") return state;
      return {
        step: "shorts",
        sessionId: state.sessionId,
        shortIds: action.shortIds,
        error: "",
      };

    case "SET_ERROR":
      return { ...initialState, error: action.error };

    case "DISMISS_ERROR":
      return { ...state, error: "" };

    case "RESET":
      return initialState;

    default:
      return state;
  }
}

// ── Component ─────────────────────────────────────────────────────────────────

interface Props {
  marketingContent: React.ReactNode;
}

export default function HomeStateMachine({ marketingContent }: Props) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const { status: authStatus } = useSession();
  const analysisStartRef = useRef<number>(0);

  const taskId = state.step === "analyzing" ? state.taskId : "";
  const sessionId = "sessionId" in state ? state.sessionId : "";

  // ── Restore workflow on mount ────────────────────────────────────────────────
  useEffect(() => {
    const saved = loadWorkflow();
    if (!saved || saved.step === "input") return;

    if (saved.step === "analyzing" && saved.taskId) {
      dispatch({
        type: "ANALYZE_STARTED",
        sessionId: saved.sessionId,
        taskId: saved.taskId,
        videoTitle: saved.videoTitle,
      });
    } else if (saved.step === "hooks") {
      api.getHooks(saved.sessionId)
        .then((data) => {
          dispatch({
            type: "RESTORE_HOOKS",
            sessionId: saved.sessionId,
            videoTitle: saved.videoTitle,
            hooks: data.hooks,
            regenerationCount: data.regeneration_count,
          });
        })
        .catch(() => clearWorkflow());
    } else if (saved.step === "shorts" && saved.shortIds.length > 0) {
      dispatch({
        type: "RESTORE_SHORTS",
        sessionId: saved.sessionId,
        shortIds: saved.shortIds,
      });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Persist workflow on every step/session change ────────────────────────────
  useEffect(() => {
    if (state.step === "input") {
      clearWorkflow();
      return;
    }
    saveWorkflow({
      step: state.step,
      sessionId: "sessionId" in state ? state.sessionId : "",
      taskId: state.step === "analyzing" ? state.taskId : "",
      videoTitle: "videoTitle" in state ? state.videoTitle : "",
      shortIds: state.step === "shorts" ? state.shortIds : [],
    });
  }, [state]);

  const handlePollComplete = useCallback(
    async (status: TaskStatus) => {
      const result = status.result;
      if (result?.error) {
        const msg =
          typeof result.error === "string"
            ? result.error
            : extractErrorMessage(result.error as unknown, "Analysis failed. Please try again.");
        dispatch({ type: "SET_ERROR", error: msg });
        return;
      }
      try {
        const hooksData = await api.getHooks(sessionId);
        dispatch({
          type: "HOOKS_LOADED",
          hooks: hooksData.hooks,
          regenerationCount: hooksData.regeneration_count,
          elapsed: analysisStartRef.current
            ? Math.round((Date.now() - analysisStartRef.current) / 1000)
            : 0,
        });
      } catch (err) {
        console.warn("Failed to load hooks:", err);
        dispatch({ type: "SET_ERROR", error: "Failed to load hooks. Please try again." });
      }
    },
    [sessionId]
  );

  const handlePollError = useCallback((error: string) => {
    dispatch({ type: "SET_ERROR", error });
  }, []);

  const handlePollProgress = useCallback((progress: number, stage: string) => {
    dispatch({ type: "POLL_PROGRESS", progress, stage });
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
    analysisStartRef.current = 0;
    dispatch({ type: "RESET" });
  }, [stopPolling]);

  const handleAnalyze = useCallback(
    async (url: string, niche: string, language: string, meta: VideoMeta) => {
      dispatch({ type: "DISMISS_ERROR" });
      analysisStartRef.current = Date.now();
      try {
        const result = await api.analyze(url, niche, language);
        dispatch({
          type: "ANALYZE_STARTED",
          sessionId: result.session_id,
          taskId: result.task_id,
          videoTitle: meta.title,
        });
      } catch (err) {
        dispatch({
          type: "SET_ERROR",
          error: extractErrorMessage(err, "Failed to start analysis. Please try again."),
        });
      }
    },
    []
  );

  const handleRegenerate = useCallback(async () => {
    if (!sessionId || state.step !== "hooks") return;
    try {
      const result = await api.regenerateHooks(sessionId);
      analysisStartRef.current = Date.now();
      dispatch({
        type: "REGENERATE_STARTED",
        taskId: result.task_id,
        regenerationCount: result.regeneration_count,
      });
    } catch (err) {
      dispatch({
        type: "SET_ERROR",
        error: extractErrorMessage(err, "Regeneration failed. Please try again."),
      });
    }
  }, [sessionId, state.step]);

  const handleSelectHooks = useCallback(
    async (
      hookIds: string[],
      captionStyle: string = "clean",
      timeOverrides: Record<string, { start_seconds: number; end_seconds: number }> = {}
    ) => {
      if (!sessionId) return;
      try {
        const result = await api.selectHooks(sessionId, hookIds, captionStyle, timeOverrides);
        dispatch({ type: "SHORTS_SELECTED", shortIds: result.short_ids });
      } catch (err) {
        dispatch({
          type: "SET_ERROR",
          error: extractErrorMessage(err, "Failed to start short generation. Please try again."),
        });
      }
    },
    [sessionId]
  );

  const error = state.error;

  // ── Marketing / input step ───────────────────────────────────────────────────

  if (state.step === "input") {
    const isAuthenticated = authStatus === "authenticated";
    return (
      <AnalyzeContext.Provider value={handleAnalyze}>
        <Header />
        <ErrorBanner error={error} onDismiss={() => dispatch({ type: "DISMISS_ERROR" })} />
        {isAuthenticated ? <AuthenticatedHome /> : marketingContent}
      </AnalyzeContext.Provider>
    );
  }

  // ── Analyze / hooks / shorts steps ──────────────────────────────────────────

  return (
    <>
      <Header onReset={resetAll} />
      <ErrorBanner error={error} onDismiss={() => dispatch({ type: "DISMISS_ERROR" })} />

      <main id="main-content" className="pt-24 pb-12 px-6">
        <AnimatePresence mode="wait">
          {state.step === "analyzing" && (
            <motion.div
              key="analyzing"
              variants={slideRight}
              initial="hidden"
              animate="show"
              exit="exit"
            >
              <ProgressStep
                progress={state.progress}
                videoTitle={state.videoTitle}
                startTime={analysisStartRef.current}
              />
            </motion.div>
          )}

          {state.step === "hooks" && (
            <motion.div
              key="hooks"
              variants={slideRight}
              initial="hidden"
              animate="show"
              exit="exit"
            >
              <HooksStep
                hooks={state.hooks}
                videoTitle={state.videoTitle}
                regenerationCount={state.regenerationCount}
                onSelectHooks={handleSelectHooks}
                onRegenerate={handleRegenerate}
                isRegenerating={state.isRegenerating}
                analysisElapsed={state.analysisElapsed}
              />
            </motion.div>
          )}

          {state.step === "shorts" && (
            <motion.div
              key="shorts"
              variants={slideRight}
              initial="hidden"
              animate="show"
              exit="exit"
            >
              <ShortsStep shortIds={state.shortIds} onReset={resetAll} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <Footer />
    </>
  );
}
