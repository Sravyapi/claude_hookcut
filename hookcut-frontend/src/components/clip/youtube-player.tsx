"use client";

import { useRef, useEffect, useState } from "react";
import type { YTPlayerInstance, YTPlayerEvent } from "@/lib/types";

declare global {
  interface Window {
    YT?: {
      Player: new (
        el: HTMLElement,
        opts: {
          videoId: string;
          width?: string | number;
          height?: string | number;
          playerVars?: Record<string, number>;
          events?: {
            onReady?: (e: YTPlayerEvent) => void;
            onError?: (e: YTPlayerEvent) => void;
          };
        }
      ) => YTPlayerInstance;
    };
    onYouTubeIframeAPIReady?: () => void;
  }
}

type YouTubePlayerProps = {
  videoId: string;
  onReady?: (player: YTPlayerInstance) => void;
  onError?: (error: string) => void;
};

export function YouTubePlayer({ videoId, onReady, onError }: YouTubePlayerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const playerRef = useRef<YTPlayerInstance | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    // Load YouTube IFrame API script if not already loaded
    if (!document.querySelector('script[src="https://www.youtube.com/iframe_api"]')) {
      const tag = document.createElement("script");
      tag.src = "https://www.youtube.com/iframe_api";
      document.body.appendChild(tag);
    }

    const initPlayer = () => {
      if (!containerRef.current || playerRef.current || !window.YT?.Player) return;

      playerRef.current = new window.YT.Player(containerRef.current, {
        videoId,
        width: "100%",
        height: "100%",
        playerVars: {
          autoplay: 0,
          controls: 1,
          modestbranding: 1,
          rel: 0,
          playsinline: 1,
        },
        events: {
          onReady: (e: YTPlayerEvent) => {
            setIsLoaded(true);
            onReady?.(e.target);
            const dur = e.target.getDuration();
            if (dur > 7200) {
              onError?.("Videos over 2 hours are not supported for manual clipping.");
            } else if (dur === 0) {
              onError?.("Live streams are not supported.");
            }
          },
          onError: (e: YTPlayerEvent) => {
            if (e.data === 150 || e.data === 101) {
              onError?.("This video cannot be embedded. Try a different video.");
            } else {
              onError?.("Failed to load video player.");
            }
          },
        },
      });
    };

    if (window.YT?.Player) {
      initPlayer();
    } else {
      // Queue-based: don't overwrite, wrap existing handler
      const prev = window.onYouTubeIframeAPIReady;
      window.onYouTubeIframeAPIReady = () => {
        prev?.();
        initPlayer();
      };
    }

    return () => {
      if (playerRef.current?.destroy) {
        playerRef.current.destroy();
        playerRef.current = null;
      }
    };
  }, [videoId]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="w-full relative rounded-xl overflow-hidden" style={{ aspectRatio: "16/9" }}>
      {!isLoaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-xl z-10">
          <div className="w-8 h-8 border-2 border-violet-400 border-t-transparent rounded-full animate-spin" />
        </div>
      )}
      <div ref={containerRef} className="w-full h-full" />
    </div>
  );
}
