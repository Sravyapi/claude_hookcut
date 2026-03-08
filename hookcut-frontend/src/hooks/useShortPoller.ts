import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import type { Short } from "../lib/types";
import { POLL_CONFIG, SHORT_STATUS } from "../lib/constants";

const MAX_POLLS = 120; // 10 minutes at 5s intervals

export function useShortPoller(
  shortId: string,
  enabled: boolean
): { data: Short | null; isLoading: boolean; error: string | null } {
  const [data, setData] = useState<Short | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollCountRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!enabled) return;

    let active = true;
    let abortController: AbortController | null = null;
    pollCountRef.current = 0;
    setIsLoading(true);
    setError(null);

    const doPoll = async () => {
      pollCountRef.current += 1;
      if (pollCountRef.current >= MAX_POLLS) {
        if (!active) return;
        setError("Short generation timed out. Please try again.");
        setIsLoading(false);
        return;
      }

      abortController = new AbortController();
      try {
        const result = await api.getShort(shortId, abortController.signal);
        if (!active) return;
        setData(result);
        setIsLoading(false);

        if (
          result.status !== SHORT_STATUS.READY &&
          result.status !== SHORT_STATUS.FAILED
        ) {
          const delay = Math.min(
            POLL_CONFIG.initial * POLL_CONFIG.multiplier ** pollCountRef.current,
            POLL_CONFIG.max
          );
          timerRef.current = setTimeout(doPoll, delay);
        }
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Failed to load short");
        setIsLoading(false);
      }
    };

    doPoll();

    return () => {
      active = false;
      abortController?.abort();
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [shortId, enabled]);

  return { data, isLoading, error };
}
