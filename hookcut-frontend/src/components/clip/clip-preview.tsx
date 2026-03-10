"use client";

import { memo, useCallback, useRef, useState, useEffect } from "react";
import { Loader2, Download, AlertCircle } from "lucide-react";
import { api } from "@/lib/api";
import { useShortPoller } from "@/hooks/useShortPoller";
import { SHORT_STATUS } from "@/lib/constants";
import { formatClipTime } from "@/lib/clip-utils";

interface ClipShortCardProps {
  shortId: string;
  index: number;
  onDone: () => void;
}

export const ClipShortCard = memo(function ClipShortCard({
  shortId,
  index,
  onDone,
}: ClipShortCardProps) {
  const { data, isLoading, error } = useShortPoller(shortId, true);
  const firedRef = useRef(false);
  const [blobUrl, setBlobUrl] = useState<string | null>(null);

  const isDone =
    data?.status === SHORT_STATUS.READY || data?.status === SHORT_STATUS.FAILED;

  useEffect(() => {
    if (isDone && !firedRef.current) {
      firedRef.current = true;
      onDone();
    }
  }, [isDone, onDone]);

  // Fetch video with auth and create blob URL for preview + download
  useEffect(() => {
    if (data?.status !== SHORT_STATUS.READY || blobUrl) return;
    let cancelled = false;

    api.downloadShort(shortId).then(async (result) => {
      if (!result.download_url || cancelled) return;
      const url = await api.getVideoBlobUrl(result.download_url);
      if (!cancelled) setBlobUrl(url);
    }).catch((err) => {
      console.warn("Failed to load video preview:", err);
    });

    return () => { cancelled = true; };
  }, [data?.status, shortId, blobUrl]);

  // Clean up blob URL on unmount
  useEffect(() => {
    return () => { if (blobUrl) URL.revokeObjectURL(blobUrl); };
  }, [blobUrl]);

  const handleDownload = useCallback(() => {
    if (!blobUrl) return;
    const a = document.createElement("a");
    a.href = blobUrl;
    a.download = `clip-${index + 1}.mp4`;
    a.click();
  }, [blobUrl, index]);

  return (
    <div className="glass-card p-4 rounded-xl flex flex-col items-center gap-3">
      <div className="text-sm font-medium text-white/80">Clip #{index + 1}</div>

      {/* Loading / Processing */}
      {(isLoading || (data && !isDone)) && (
        <div className="flex items-center gap-2 text-violet-300 text-sm">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>{data?.status ?? "queued"}</span>
        </div>
      )}

      {/* Ready */}
      {data?.status === SHORT_STATUS.READY && (
        <>
          {blobUrl ? (
            <video
              src={blobUrl}
              controls
              playsInline
              preload="metadata"
              className="w-full rounded-lg aspect-[9/16] max-h-[480px] bg-black"
              aria-label={`Clip ${index + 1} preview`}
            />
          ) : (
            <div className="w-full aspect-[9/16] max-h-[480px] bg-black/50 rounded-lg flex items-center justify-center">
              <Loader2 className="w-5 h-5 animate-spin text-white/40" />
            </div>
          )}
          {data.duration_seconds != null && (
            <div className="text-xs text-white/40">
              {formatClipTime(data.duration_seconds)}
            </div>
          )}
          <button
            type="button"
            onClick={handleDownload}
            className="w-full px-4 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium transition-colors flex items-center justify-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5" /> Download
          </button>
        </>
      )}

      {/* Failed */}
      {data?.status === SHORT_STATUS.FAILED && (
        <>
          <AlertCircle className="w-6 h-6 text-red-400" />
          <div className="text-xs text-red-300/80">
            {data.error_message || "Generation failed"}
          </div>
        </>
      )}

      {/* Error from polling */}
      {error && !data && (
        <div className="text-xs text-red-300/80">{error}</div>
      )}
    </div>
  );
});
