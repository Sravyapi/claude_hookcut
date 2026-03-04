"use client";

import { useState, useCallback, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { api } from "../lib/api";
import type { Hook, Step, VideoMeta, TaskStatus } from "../lib/types";
import { usePollTask } from "../hooks/usePollTask";
import Header from "../components/header";
import UrlStep from "../components/url-step";
import ProgressStep from "../components/progress-step";
import HooksStep from "../components/hooks-step";
import ShortsStep from "../components/shorts-step";
import { slideRight } from "../lib/motion";

export default function Home() {
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

  const handlePollComplete = useCallback(
    async (status: TaskStatus) => {
      const result = status.result;
      if (result?.error) {
        setError(result.error as string);
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

  const { stopPolling } = usePollTask(taskId || null, sessionId || null, handlePollComplete, handlePollError, handlePollProgress);

  const resetAll = useCallback(() => {
    stopPolling();
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

  const handleAnalyze = async (
    url: string,
    niche: string,
    language: string,
    meta: VideoMeta
  ) => {
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
      setError(
        err instanceof Error ? err.message : "Failed to start analysis"
      );
      setStep("input");
    }
  };

  const handleRegenerate = async () => {
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
      setError(
        err instanceof Error ? err.message : "Regeneration failed"
      );
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleSelectHooks = async (
    hookIds: string[],
    captionStyle: string = "clean",
    timeOverrides: Record<string, { start_seconds: number; end_seconds: number }> = {},
  ) => {
    if (!sessionId) return;
    try {
      const result = await api.selectHooks(sessionId, hookIds, captionStyle, timeOverrides);
      setShortIds(result.short_ids);
      setStep("shorts");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to start short generation"
      );
    }
  };

  return (
    <>
      <Header onReset={resetAll} />

      <main className="pt-24 pb-12 px-6">
        {/* Error banner */}
        <AnimatePresence>
          {error && step === "input" && (
            <motion.div
              initial={{ opacity: 0, y: -12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              className="max-w-2xl mx-auto mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-start gap-3"
            >
              <svg
                className="w-5 h-5 shrink-0 mt-0.5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
                />
              </svg>
              <div>
                <p className="font-medium mb-0.5">Analysis Error</p>
                <p className="text-white/50">{error}</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Step transitions */}
        <AnimatePresence mode="wait">
          {step === "input" && (
            <motion.div
              key="input"
              variants={slideRight}
              initial="hidden"
              animate="show"
              exit="exit"
            >
              <UrlStep onAnalyze={handleAnalyze} />
            </motion.div>
          )}

          {step === "analyzing" && (
            <motion.div
              key="analyzing"
              variants={slideRight}
              initial="hidden"
              animate="show"
              exit="exit"
            >
              <ProgressStep
                stage={stage}
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

      {/* Footer */}
      <footer className="border-t border-white/[0.04] mt-8">
        <div className="max-w-6xl mx-auto px-6 py-12">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-8 mb-10">
            {/* Brand */}
            <div className="sm:col-span-1">
              <span className="gradient-text font-bold text-lg">HookCut</span>
              <p className="text-xs text-white/20 mt-2 leading-relaxed">
                AI-powered YouTube to Shorts pipeline. Extract hooks, generate
                scroll-stopping content.
              </p>
            </div>

            {/* Product */}
            <div>
              <h4 className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-3">
                Product
              </h4>
              <ul className="space-y-2">
                {["Hook Extraction", "Short Generation", "Pricing", "Dashboard"].map(
                  (item) => (
                    <li key={item}>
                      <span className="text-xs text-white/20 hover:text-white/40 transition-colors cursor-default">
                        {item}
                      </span>
                    </li>
                  )
                )}
              </ul>
            </div>

            {/* Resources */}
            <div>
              <h4 className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-3">
                Resources
              </h4>
              <ul className="space-y-2">
                {["API Docs", "Changelog", "Status", "Support"].map(
                  (item) => (
                    <li key={item}>
                      <span className="text-xs text-white/20 hover:text-white/40 transition-colors cursor-default">
                        {item}
                      </span>
                    </li>
                  )
                )}
              </ul>
            </div>

            {/* Legal */}
            <div>
              <h4 className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-3">
                Legal
              </h4>
              <ul className="space-y-2">
                {["Terms of Service", "Privacy Policy", "Cookie Policy"].map(
                  (item) => (
                    <li key={item}>
                      <span className="text-xs text-white/20 hover:text-white/40 transition-colors cursor-default">
                        {item}
                      </span>
                    </li>
                  )
                )}
              </ul>
            </div>
          </div>

          <div className="flex items-center justify-between pt-6 border-t border-white/[0.04]">
            <div className="flex items-center gap-3 text-xs text-white/15">
              <span className="gradient-text font-semibold">HookCut</span>
              <span className="w-1 h-1 rounded-full bg-white/10" />
              <span>by NyxPath</span>
            </div>
            <div className="flex items-center gap-4">
              {/* Twitter/X */}
              <svg className="w-4 h-4 text-white/15 hover:text-white/30 transition-colors cursor-pointer" fill="currentColor" viewBox="0 0 24 24">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
              </svg>
              {/* YouTube */}
              <svg className="w-4 h-4 text-white/15 hover:text-white/30 transition-colors cursor-pointer" fill="currentColor" viewBox="0 0 24 24">
                <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814z" />
              </svg>
            </div>
          </div>
        </div>
      </footer>
    </>
  );
}
