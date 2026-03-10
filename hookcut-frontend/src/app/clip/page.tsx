"use client";

import { Suspense, useReducer, useCallback, useRef, useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Scissors, Plus, Play, Loader2, ArrowLeft, CreditCard } from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import { YouTubePlayer } from "@/components/clip/youtube-player";
import { TimelineScrubber } from "@/components/clip/timeline-scrubber";
import { ClipQueue } from "@/components/clip/clip-queue";
import { ClipSettings } from "@/components/clip/clip-settings";
import { ClipForm } from "@/components/clip/clip-form";
import { GeneratingStep } from "@/components/clip/clip-status";
import type { CaptionStyle, YTPlayerInstance } from "@/lib/types";
import { formatClipTime } from "@/lib/clip-utils";
import Header from "@/components/header";
import type { CreditBalance } from "@/lib/types";

// State machine types
type ClipEntry = {
  id: string;
  startTime: number;
  endTime: number;
};

type ClipSettingsData = {
  aspectRatio: "9:16" | "1:1" | "4:5";
  captionStyle: CaptionStyle;
  captionsEnabled: boolean;
  audioNormalization: boolean;
};

type ClipperState =
  | { step: "input"; url: string; error: string }
  | { step: "video_loaded"; videoId: string; videoTitle: string; duration: number; clips: ClipEntry[]; settings: ClipSettingsData; startTime: number; endTime: number; error: string }
  | { step: "generating"; videoId: string; videoTitle: string; clips: ClipEntry[]; sessionId: string; shortIds: string[]; taskIds: string[]; error: string }
  | { step: "complete"; videoId: string; videoTitle: string; sessionId: string; shortIds: string[]; taskIds: string[]; error: string };

type ClipperAction =
  | { type: "SET_URL"; url: string }
  | { type: "LOAD_VIDEO"; videoId: string; videoTitle: string; duration: number }
  | { type: "LOAD_VIDEO_ERROR"; error: string }
  | { type: "SET_START_TIME"; time: number }
  | { type: "SET_END_TIME"; time: number }
  | { type: "ADD_CLIP" }
  | { type: "REMOVE_CLIP"; clipId: string }
  | { type: "EDIT_CLIP"; clipId: string }
  | { type: "UPDATE_SETTINGS"; settings: Partial<ClipSettingsData> }
  | { type: "START_GENERATE"; sessionId: string; shortIds: string[]; taskIds: string[] }
  | { type: "GENERATION_COMPLETE" }
  | { type: "SET_ERROR"; error: string }
  | { type: "DISMISS_ERROR" }
  | { type: "RESET" };

const MIN_CLIP_DURATION_S = 3;
const MAX_CLIP_DURATION_S = 300;
const DEFAULT_END_TIME_S = 30;
const MAX_CLIPS_PER_VIDEO = 10;

const DEFAULT_SETTINGS: ClipSettingsData = {
  aspectRatio: "9:16",
  captionStyle: "clean",
  captionsEnabled: true,
  audioNormalization: true,
};

function clipperReducer(state: ClipperState, action: ClipperAction): ClipperState {
  switch (action.type) {
    case "SET_URL":
      if (state.step !== "input") return state;
      return { ...state, url: action.url };

    case "LOAD_VIDEO":
      return {
        step: "video_loaded",
        videoId: action.videoId,
        videoTitle: action.videoTitle,
        duration: action.duration,
        clips: [],
        settings: DEFAULT_SETTINGS,
        startTime: 0,
        endTime: Math.min(action.duration, DEFAULT_END_TIME_S),
        error: "",
      };

    case "LOAD_VIDEO_ERROR":
      return { step: "input", url: state.step === "input" ? state.url : "", error: action.error };

    case "SET_START_TIME":
      if (state.step !== "video_loaded") return state;
      return { ...state, startTime: action.time };

    case "SET_END_TIME":
      if (state.step !== "video_loaded") return state;
      return { ...state, endTime: action.time };

    case "ADD_CLIP":
      if (state.step !== "video_loaded") return state;
      if (state.clips.length >= MAX_CLIPS_PER_VIDEO) return { ...state, error: `Maximum ${MAX_CLIPS_PER_VIDEO} clips per video` };
      if (state.endTime - state.startTime < MIN_CLIP_DURATION_S) return { ...state, error: `Minimum clip duration is ${MIN_CLIP_DURATION_S} seconds` };
      return {
        ...state,
        clips: [...state.clips, {
          id: crypto.randomUUID(),
          startTime: state.startTime,
          endTime: state.endTime,
        }],
        error: "",
      };

    case "REMOVE_CLIP":
      if (state.step !== "video_loaded") return state;
      return { ...state, clips: state.clips.filter(c => c.id !== action.clipId) };

    case "EDIT_CLIP": {
      if (state.step !== "video_loaded") return state;
      const clip = state.clips.find(c => c.id === action.clipId);
      if (!clip) return state;
      return {
        ...state,
        startTime: clip.startTime,
        endTime: clip.endTime,
        clips: state.clips.filter(c => c.id !== action.clipId),
      };
    }

    case "UPDATE_SETTINGS":
      if (state.step !== "video_loaded") return state;
      return { ...state, settings: { ...state.settings, ...action.settings } };

    case "START_GENERATE":
      if (state.step !== "video_loaded") return state;
      return {
        step: "generating",
        videoId: state.videoId,
        videoTitle: state.videoTitle,
        clips: state.clips,
        sessionId: action.sessionId,
        shortIds: action.shortIds,
        taskIds: action.taskIds,
        error: "",
      };

    case "GENERATION_COMPLETE":
      if (state.step !== "generating") return state;
      return {
        step: "complete",
        videoId: state.videoId,
        videoTitle: state.videoTitle,
        sessionId: state.sessionId,
        shortIds: state.shortIds,
        taskIds: state.taskIds,
        error: "",
      };

    case "SET_ERROR":
      return { ...state, error: action.error };

    case "DISMISS_ERROR":
      return { ...state, error: "" };

    case "RESET":
      return { step: "input", url: "", error: "" };

    default:
      return state;
  }
}

export default function ClipPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-violet-400" /></div>}>
      <ClipPageContent />
    </Suspense>
  );
}

function ClipPageContent() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const searchParams = useSearchParams();
  const aiSessionId = searchParams?.get("session") ?? undefined;

  // Restore generating/complete state from URL params on refresh
  const initialState = (): ClipperState => {
    const shortIdsParam = searchParams?.get("shorts");
    const sessionIdParam = searchParams?.get("sid");
    if (shortIdsParam && sessionIdParam) {
      const shortIds = shortIdsParam.split(",").filter(Boolean);
      if (shortIds.length > 0) {
        return {
          step: "generating",
          videoId: "",
          videoTitle: "",
          clips: [],
          sessionId: sessionIdParam,
          shortIds,
          taskIds: [],
          error: "",
        };
      }
    }
    return { step: "input", url: searchParams?.get("url") || "", error: "" };
  };

  const [state, dispatch] = useReducer(clipperReducer, undefined, initialState);
  const playerRef = useRef<YTPlayerInstance | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [creditBalance, setCreditBalance] = useState<CreditBalance | null>(null);

  // Auth gate
  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/auth/login?callbackUrl=/clip");
    }
  }, [status, router]);

  // Fetch credit balance
  useEffect(() => {
    if (status !== "authenticated") return;
    api.getBalance()
      .then(setCreditBalance)
      .catch((err) => console.warn("Failed to load balance:", err));
  }, [status]);

  // Auto-load URL from query param
  useEffect(() => {
    const url = searchParams?.get("url");
    if (url && state.step === "input") {
      dispatch({ type: "SET_URL", url });
    }
  }, [searchParams, state.step]);

  const handlePlayerReady = useCallback((player: YTPlayerInstance) => {
    playerRef.current = player;
  }, []);

  const handleLoadVideo = useCallback(async () => {
    if (state.step !== "input" || !state.url) return;
    try {
      const result = await api.validateUrl(state.url);
      if (!result.video_id) {
        dispatch({ type: "LOAD_VIDEO_ERROR", error: "Invalid YouTube URL" });
        return;
      }
      dispatch({
        type: "LOAD_VIDEO",
        videoId: result.video_id,
        videoTitle: result.title || "",
        duration: result.duration_seconds || 0,
      });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to load video";
      dispatch({ type: "LOAD_VIDEO_ERROR", error: message });
    }
  }, [state]);

  const handleGenerate = useCallback(async () => {
    if (state.step !== "video_loaded" || state.clips.length === 0) return;
    setIsGenerating(true);
    try {
      const result = await api.generateClips({
        youtube_url: `https://www.youtube.com/watch?v=${state.videoId}`,
        clips: state.clips.map(c => ({ start_time: c.startTime, end_time: c.endTime })),
        caption_style: state.settings.captionStyle,
        captions_enabled: state.settings.captionsEnabled,
        audio_normalization: state.settings.audioNormalization,
        aspect_ratio: state.settings.aspectRatio,
        ai_session_id: aiSessionId,
      });
      // Persist to URL so refresh resumes polling
      const params = new URLSearchParams();
      params.set("sid", result.session_id);
      params.set("shorts", result.short_ids.join(","));
      router.replace(`/clip?${params.toString()}`, { scroll: false });

      dispatch({ type: "START_GENERATE", sessionId: result.session_id, shortIds: result.short_ids, taskIds: result.task_ids });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Generation failed";
      dispatch({ type: "SET_ERROR", error: message });
    } finally {
      setIsGenerating(false);
    }
  }, [state, aiSessionId]);

  if (status === "loading") {
    return (
      <>
        <Header />
        <div className="min-h-screen flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-violet-400" />
        </div>
      </>
    );
  }

  return (
    <>
    <Header />
    <main className="min-h-screen bg-[var(--color-surface-primary)] pt-20 pb-16">
      <div className="max-w-4xl mx-auto px-4 sm:px-6">
        {/* Back to dashboard + credit display */}
        <div className="flex items-center justify-between mb-6">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1.5 text-sm text-white/40 hover:text-white/70 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>
          {creditBalance && (
            creditBalance.manual_clip_minutes_remaining > 0 ? (
              <div className="flex items-center gap-2 text-sm">
                <Scissors className="w-3.5 h-3.5 text-violet-400" />
                <span className="font-mono tabular-nums text-violet-300 font-semibold">{creditBalance.manual_clip_minutes_remaining.toFixed(0)}</span>
                <span className="text-white/40">clip min remaining</span>
              </div>
            ) : (
              <Link
                href="/pricing"
                className="flex items-center gap-2 text-sm text-amber-400 hover:text-amber-300 transition-colors"
              >
                <Scissors className="w-3.5 h-3.5" />
                <span>No clip minutes</span>
                <span className="font-semibold">Top up &rarr;</span>
              </Link>
            )
          )}
        </div>

        {/* Page title */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-violet-500/10 text-violet-300 text-sm mb-4">
            <Scissors className="w-4 h-4" />
            Manual Clipper
          </div>
          <h1 className="text-3xl font-bold text-white">Clip Any Moment</h1>
          <p className="text-white/50 mt-2">Set start and end points to create clips from any YouTube video</p>
        </div>

        {/* Error banner */}
        <AnimatePresence>
          {state.error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-300 flex items-center justify-between"
            >
              <span>{state.error}</span>
              <button onClick={() => dispatch({ type: "DISMISS_ERROR" })} className="text-red-300/60 hover:text-red-300">&#x2715;</button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Step: URL Input */}
        {state.step === "input" && (
          <ClipForm
            url={state.url}
            onUrlChange={(url) => dispatch({ type: "SET_URL", url })}
            onSubmit={handleLoadVideo}
          />
        )}

        {/* Step: Video Loaded — Clipper Interface */}
        {state.step === "video_loaded" && (
          <div className="space-y-6">
            {/* YouTube Player */}
            <div className="glass-card rounded-2xl overflow-hidden">
              <YouTubePlayer videoId={state.videoId} onReady={handlePlayerReady} />
            </div>

            {/* Timeline Scrubber */}
            <div className="glass-card p-6 rounded-2xl">
              <TimelineScrubber
                duration={state.duration}
                startTime={state.startTime}
                endTime={state.endTime}
                onStartChange={t => dispatch({ type: "SET_START_TIME", time: t })}
                onEndChange={t => dispatch({ type: "SET_END_TIME", time: t })}
                player={playerRef.current ?? undefined}
              />

              {/* Set Start/End buttons */}
              <div className="flex items-center gap-3 mt-4">
                <button
                  onClick={() => {
                    if (playerRef.current) dispatch({ type: "SET_START_TIME", time: playerRef.current.getCurrentTime() });
                  }}
                  className="px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-white/80 text-sm border border-white/10 transition-colors"
                >
                  Set Start ({formatClipTime(state.startTime)})
                </button>
                <button
                  onClick={() => {
                    if (playerRef.current) dispatch({ type: "SET_END_TIME", time: playerRef.current.getCurrentTime() });
                  }}
                  className="px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-white/80 text-sm border border-white/10 transition-colors"
                >
                  Set End ({formatClipTime(state.endTime)})
                </button>
                <button
                  onClick={() => {
                    if (playerRef.current) {
                      playerRef.current.seekTo(state.startTime, true);
                      playerRef.current.playVideo();
                    }
                  }}
                  className="px-4 py-2 rounded-lg bg-violet-500/10 hover:bg-violet-500/20 text-violet-300 text-sm border border-violet-500/20 transition-colors flex items-center gap-1.5"
                >
                  <Play className="w-3.5 h-3.5" /> Preview Selection
                </button>
                <div className="ml-auto text-sm text-white/40">
                  Duration: {formatClipTime(state.endTime - state.startTime)}
                </div>
              </div>
            </div>

            {/* Add Clip + Clip Queue */}
            <div className="glass-card p-6 rounded-2xl">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Clip Queue</h3>
                <button
                  onClick={() => dispatch({ type: "ADD_CLIP" })}
                  disabled={state.clips.length >= MAX_CLIPS_PER_VIDEO}
                  className="px-4 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5"
                >
                  <Plus className="w-4 h-4" /> Add Clip
                </button>
              </div>

              <ClipQueue
                clips={state.clips}
                onRemove={id => dispatch({ type: "REMOVE_CLIP", clipId: id })}
                onEdit={id => dispatch({ type: "EDIT_CLIP", clipId: id })}
              />
            </div>

            {/* Settings + Generate */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <ClipSettings
                settings={state.settings}
                onUpdate={s => dispatch({ type: "UPDATE_SETTINGS", settings: s })}
              />

              <div className="glass-card p-6 rounded-2xl flex flex-col justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-white mb-2">Generate</h3>
                  <p className="text-sm text-white/50">
                    {state.clips.length} clip{state.clips.length !== 1 ? "s" : ""} &middot;{" "}
                    {formatClipTime(state.clips.reduce((sum, c) => sum + (c.endTime - c.startTime), 0))} total
                  </p>
                </div>
                <button
                  onClick={handleGenerate}
                  disabled={state.clips.length === 0 || isGenerating}
                  className="mt-4 w-full py-3 rounded-xl bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-500 hover:to-cyan-500 text-white font-semibold disabled:opacity-40 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
                >
                  {isGenerating ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> Generating...</>
                  ) : (
                    <>Generate {state.clips.length} Clip{state.clips.length !== 1 ? "s" : ""}</>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step: Generating / Complete — show polled short cards */}
        {(state.step === "generating" || state.step === "complete") && (
          <GeneratingStep
            shortIds={state.shortIds}
            onAllDone={() => dispatch({ type: "GENERATION_COMPLETE" })}
            isComplete={state.step === "complete"}
            onReset={() => {
              router.replace("/clip", { scroll: false });
              dispatch({ type: "RESET" });
            }}
          />
        )}
      </div>
    </main>
    </>
  );
}
