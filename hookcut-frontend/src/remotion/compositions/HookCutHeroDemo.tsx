import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  Sequence,
} from "remotion";

// Scene 1: Video thumbnail + scan line animation
function Scene1({ startFrame }: { startFrame: number }) {
  const frame = useCurrentFrame();
  const localFrame = frame - startFrame;

  const scanY = interpolate(localFrame, [0, 150], [-100, 1180], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#111111" }}>
      {/* Thumbnail placeholder */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "linear-gradient(135deg, #1A1A1A 0%, #2A2A2A 100%)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div style={{ textAlign: "center" }}>
          <div
            style={{
              width: 80,
              height: 80,
              borderRadius: "50%",
              background: "rgba(232,74,47,0.2)",
              border: "2px solid #E84A2F",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 24px",
            }}
          >
            <div
              style={{
                width: 0,
                height: 0,
                borderTop: "20px solid transparent",
                borderBottom: "20px solid transparent",
                borderLeft: "32px solid #E84A2F",
                marginLeft: 6,
              }}
            />
          </div>
          <p
            style={{
              color: "#A1A1AA",
              fontSize: 18,
              fontFamily: "system-ui",
              margin: 0,
            }}
          >
            Analyzing video transcript…
          </p>
        </div>
      </div>
      {/* Scan line */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: scanY,
          height: 2,
          background:
            "linear-gradient(90deg, transparent, #E84A2F, transparent)",
          opacity: 0.8,
        }}
      />
    </AbsoluteFill>
  );
}

// Scene 2: Hook detection timeline
function Scene2({ startFrame }: { startFrame: number }) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const localFrame = frame - startFrame;

  const hooks = [
    { time: "0:14", score: 87, x: 0.12 },
    { time: "1:32", score: 74, x: 0.28 },
    { time: "3:07", score: 91, x: 0.48 },
    { time: "5:41", score: 68, x: 0.68 },
    { time: "8:23", score: 82, x: 0.85 },
  ];

  const scoreColor = (s: number) =>
    s >= 81
      ? "#16A34A"
      : s >= 66
        ? "#E84A2F"
        : s >= 41
          ? "#F59E0B"
          : "#DC2626";

  const containerOpacity = interpolate(localFrame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#FAFAF8",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexDirection: "column",
        opacity: containerOpacity,
      }}
    >
      <p
        style={{
          color: "#A1A1AA",
          fontSize: 14,
          fontFamily: "system-ui",
          textTransform: "uppercase",
          letterSpacing: "0.1em",
          marginBottom: 48,
        }}
      >
        Hook Detection Timeline
      </p>
      <div style={{ position: "relative", width: 1400, height: 120 }}>
        {/* Track */}
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: 0,
            right: 0,
            height: 2,
            backgroundColor: "#E4E4E7",
            transform: "translateY(-50%)",
          }}
        />
        {/* Markers */}
        {hooks.map((hook, i) => {
          const markerFrame = i * 40;
          const progress = spring({
            frame: localFrame - markerFrame,
            fps,
            config: { damping: 14, stiffness: 200 },
          });
          return (
            <div
              key={hook.time}
              style={{
                position: "absolute",
                left: `${hook.x * 100}%`,
                top: "50%",
                transform: `translateY(-50%) scale(${progress})`,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 8,
              }}
            >
              <div
                style={{
                  width: 0,
                  height: 0,
                  borderLeft: "8px solid transparent",
                  borderRight: "8px solid transparent",
                  borderBottom: `14px solid ${scoreColor(hook.score)}`,
                  filter: `drop-shadow(0 0 6px ${scoreColor(hook.score)})`,
                }}
              />
              <div
                style={{
                  width: 2,
                  height: 24,
                  backgroundColor: scoreColor(hook.score),
                }}
              />
              <p
                style={{
                  color: "#71717A",
                  fontSize: 13,
                  fontFamily: "monospace",
                  margin: 0,
                  whiteSpace: "nowrap",
                }}
              >
                {hook.time}
              </p>
            </div>
          );
        })}
      </div>
      <p
        style={{
          color: "#71717A",
          fontSize: 16,
          fontFamily: "system-ui",
          marginTop: 60,
        }}
      >
        5 hooks found · Avg score 80
      </p>
    </AbsoluteFill>
  );
}

// Scene 3: Hook card with animated score
function Scene3({ startFrame }: { startFrame: number }) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const localFrame = frame - startFrame;

  const cardProgress = spring({
    frame: localFrame,
    fps,
    config: { damping: 20, stiffness: 150 },
  });
  const scoreProgress = interpolate(localFrame, [10, 60], [0, 87], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#FAFAF8",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          width: 520,
          backgroundColor: "#FFFFFF",
          borderRadius: 16,
          border: "1px solid #E4E4E7",
          padding: 32,
          transform: `translateY(${(1 - cardProgress) * 60}px)`,
          opacity: cardProgress,
          boxShadow: "0 4px 24px rgba(0,0,0,0.06)",
        }}
      >
        {/* Score circle */}
        <div style={{ textAlign: "center", marginBottom: 24 }}>
          <div
            style={{
              width: 96,
              height: 96,
              borderRadius: "50%",
              border: "6px solid #E84A2F",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 12px",
            }}
          >
            <span
              style={{
                fontSize: 32,
                fontWeight: 700,
                color: "#E84A2F",
                fontFamily: "monospace",
              }}
            >
              {Math.round(scoreProgress)}
            </span>
          </div>
          <p
            style={{
              color: "#16A34A",
              fontSize: 12,
              fontWeight: 600,
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              margin: 0,
            }}
          >
            High Impact
          </p>
        </div>
        {/* Hook type badge */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            marginBottom: 12,
          }}
        >
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              backgroundColor: "#E84A2F",
            }}
          />
          <span
            style={{
              fontSize: 11,
              fontWeight: 700,
              color: "#E84A2F",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              fontFamily: "system-ui",
            }}
          >
            Curiosity Gap
          </span>
        </div>
        {/* Hook text */}
        <p
          style={{
            fontSize: 18,
            color: "#0A0A0A",
            fontWeight: 600,
            lineHeight: 1.4,
            margin: "0 0 20px",
            fontFamily: "'Outfit', system-ui",
          }}
        >
          "This one decision changed everything I thought I knew…"
        </p>
        {/* Timestamp */}
        <p
          style={{
            fontSize: 12,
            color: "#A1A1AA",
            fontFamily: "monospace",
            margin: 0,
          }}
        >
          3:07 → 3:40
        </p>
      </div>
    </AbsoluteFill>
  );
}

// Scene 4: 9:16 Short preview
function Scene4({ startFrame }: { startFrame: number }) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const localFrame = frame - startFrame;

  const progress = spring({
    frame: localFrame,
    fps,
    config: { damping: 18, stiffness: 120 },
  });

  const labelOpacity = interpolate(localFrame, [20, 50], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#111111",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {/* 9:16 preview frame */}
      <div
        style={{
          width: 380,
          height: 676,
          backgroundColor: "#1A1A1A",
          borderRadius: 20,
          border: "1px solid rgba(255,255,255,0.1)",
          overflow: "hidden",
          transform: `scale(${progress})`,
          opacity: progress,
          position: "relative",
          display: "flex",
          alignItems: "flex-end",
        }}
      >
        {/* Video area gradient */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            background:
              "linear-gradient(to bottom, transparent 40%, rgba(0,0,0,0.9) 100%)",
          }}
        />
        {/* Caption overlay */}
        <div
          style={{
            position: "relative",
            padding: "24px 20px",
            width: "100%",
          }}
        >
          <p
            style={{
              color: "#FFFFFF",
              fontSize: 22,
              fontWeight: 800,
              fontFamily: "'Outfit', system-ui",
              lineHeight: 1.3,
              textAlign: "center",
              textShadow: "0 2px 8px rgba(0,0,0,0.8)",
              margin: 0,
            }}
          >
            This one decision changed everything I thought I knew…
          </p>
        </div>
      </div>
      <p
        style={{
          position: "absolute",
          bottom: 60,
          color: "#71717A",
          fontSize: 16,
          fontFamily: "system-ui",
          opacity: labelOpacity,
        }}
      >
        Ready to post · 9:16 · Captions included
      </p>
    </AbsoluteFill>
  );
}

// Scene 5: HookCut wordmark
function Scene5({ startFrame }: { startFrame: number }) {
  const frame = useCurrentFrame();
  const localFrame = frame - startFrame;

  const opacity = interpolate(localFrame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });
  const urlOpacity = interpolate(localFrame, [15, 35], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0A0A0A",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexDirection: "column",
      }}
    >
      <h1
        style={{
          color: "#FFFFFF",
          fontSize: 64,
          fontWeight: 800,
          fontFamily: "'Outfit', system-ui",
          margin: "0 0 16px",
          letterSpacing: "-0.03em",
          opacity,
        }}
      >
        HookCut
      </h1>
      <p
        style={{
          color: "#A1A1AA",
          fontSize: 18,
          fontFamily: "system-ui",
          margin: 0,
          opacity: urlOpacity,
        }}
      >
        hookcut.ai
      </p>
    </AbsoluteFill>
  );
}

export function HookCutHeroDemo() {
  return (
    <AbsoluteFill>
      <Sequence from={0} durationInFrames={150}>
        <Scene1 startFrame={0} />
      </Sequence>
      <Sequence from={150} durationInFrames={210}>
        <Scene2 startFrame={150} />
      </Sequence>
      <Sequence from={360} durationInFrames={240}>
        <Scene3 startFrame={360} />
      </Sequence>
      <Sequence from={600} durationInFrames={240}>
        <Scene4 startFrame={600} />
      </Sequence>
      <Sequence from={840} durationInFrames={60}>
        <Scene5 startFrame={840} />
      </Sequence>
    </AbsoluteFill>
  );
}
