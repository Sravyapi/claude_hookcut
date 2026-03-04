import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import type { Short } from "../lib/types";
import { POLL_CONFIG, SHORT_STATUS } from "../lib/types";

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
    pollCountRef.current = 0;
    setIsLoading(true);
    setError(null);

    const doPoll = async () => {
      try {
        const result = await api.getShort(shortId);
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
          pollCountRef.current++;
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
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [shortId, enabled]);

  return { data, isLoading, error };
}
