import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import type { TaskStatus } from "../lib/types";
import { POLL_CONFIG } from "../lib/types";

const MAX_POLLS = 120; // ~10 min with exponential backoff — prevents infinite polling on stuck tasks

export function usePollTask(
  taskId: string | null,
  sessionId: string | null,
  onComplete: (result: TaskStatus) => void,
  onError: (error: string) => void,
  onProgress?: (progress: number, stage: string) => void
): { isPolling: boolean; stopPolling: () => void } {
  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pollCountRef = useRef(0);
  const [isPolling, setIsPolling] = useState(false);

  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);
  const onProgressRef = useRef(onProgress);

  useEffect(() => {
    onCompleteRef.current = onComplete;
    onErrorRef.current = onError;
    onProgressRef.current = onProgress;
  });

  const stopPolling = () => {
    if (pollRef.current) {
      clearTimeout(pollRef.current);
      pollRef.current = null;
    }
    setIsPolling(false);
  };

  useEffect(() => {
    if (!taskId || !sessionId) {
      return;
    }

    let cancelled = false;
    pollCountRef.current = 0;
    setIsPolling(true);

    const doPoll = async () => {
      if (cancelled) return;
      try {
        const status = await api.getTaskStatus(taskId);
        if (cancelled) return;

        const delay = Math.min(
          POLL_CONFIG.initial * POLL_CONFIG.multiplier ** pollCountRef.current,
          POLL_CONFIG.max
        );

        if (status.status === "PROGRESS") {
          if (onProgressRef.current) {
            onProgressRef.current(status.progress || 0, status.stage || "Processing...");
          }
          pollCountRef.current++;
          pollRef.current = setTimeout(doPoll, delay);
        } else if (status.status === "SUCCESS") {
          pollCountRef.current = 0;
          setIsPolling(false);
          onCompleteRef.current(status);
        } else if (status.status === "FAILURE") {
          pollCountRef.current = 0;
          setIsPolling(false);
          onErrorRef.current(status.error || "Task failed. Please try again.");
        } else {
          // PENDING, STARTED, or other transient states
          if (pollCountRef.current >= MAX_POLLS) {
            setIsPolling(false);
            onErrorRef.current("Analysis timed out. Please refresh and try again.");
            return;
          }
          if (onProgressRef.current) {
            onProgressRef.current(0, "Waiting for worker...");
          }
          pollCountRef.current++;
          pollRef.current = setTimeout(doPoll, delay);
        }
      } catch {
        if (cancelled) return;
        pollCountRef.current = 0;
        setIsPolling(false);
        onErrorRef.current("Lost connection. Please try again.");
      }
    };

    doPoll();

    return () => {
      cancelled = true;
      if (pollRef.current) {
        clearTimeout(pollRef.current);
        pollRef.current = null;
      }
      setIsPolling(false);
    };
  }, [taskId, sessionId]);

  return { isPolling, stopPolling };
}
