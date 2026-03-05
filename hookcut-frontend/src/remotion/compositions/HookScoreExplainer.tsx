import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  Sequence,
} from "remotion";

function TextScene({
  text,
  subtext,
  frame,
  startFrame,
}: {
  text: string;
  subtext?: string;
  frame: number;
  startFrame: number;
  fps: number;
}) {
  const localFrame = frame - startFrame;
  const opacity = interpolate(localFrame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });
  const y = interpolate(localFrame, [0, 30], [40, 0], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        opacity,
        transform: `translateY(${y}px)`,
        textAlign: "center",
        padding: "0 60px",
      }}
    >
      <p
        style={{
          color: "#FFFFFF",
          fontSize: 52,
          fontWeight: 800,
          fontFamily: "'Outfit', system-ui",
          lineHeight: 1.2,
          margin: "0 0 20px",
        }}
      >
        {text}
      </p>
      {subtext && (
        <p
          style={{
            color: "#A1A1AA",
            fontSize: 28,
            fontFamily: "system-ui",
            margin: 0,
          }}
        >
          {subtext}
        </p>
      )}
    </div>
  );
}

export function HookScoreExplainer() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const hookTypes = ["CURIOSITY GAP", "PAIN ESCALATION", "SOCIAL PROOF"];
  const badgeColors = ["#E84A2F", "#F59E0B", "#16A34A"];

  const scoreProgress = interpolate(frame, [100, 170], [0, 87], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#111111" }}>
      {/* Scene 1: "Most AI clippers just count clips." */}
      <Sequence from={0} durationInFrames={90}>
        <AbsoluteFill
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <TextScene
            text="Most AI clippers just count clips."
            frame={frame}
            startFrame={0}
            fps={fps}
          />
        </AbsoluteFill>
      </Sequence>

      {/* Scene 2: "HookCut scores them." + gauge */}
      <Sequence from={90} durationInFrames={90}>
        <AbsoluteFill
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexDirection: "column",
            gap: 48,
          }}
        >
          <TextScene
            text="HookCut scores them."
            frame={frame}
            startFrame={90}
            fps={fps}
          />
          {/* Score gauge */}
          <div
            style={{
              width: 160,
              height: 160,
              borderRadius: "50%",
              border: "8px solid #E84A2F",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              opacity: interpolate(frame - 90, [10, 30], [0, 1], {
                extrapolateRight: "clamp",
              }),
            }}
          >
            <span
              style={{
                color: "#E84A2F",
                fontSize: 48,
                fontWeight: 700,
                fontFamily: "monospace",
              }}
            >
              {Math.round(scoreProgress)}
            </span>
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* Scene 3: Hook type badges */}
      <Sequence from={180} durationInFrames={180}>
        <AbsoluteFill
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexDirection: "column",
            gap: 24,
            padding: "0 60px",
          }}
        >
          {hookTypes.map((type, i) => {
            const badgeStartFrame = 180 + i * 50;
            const progress = spring({
              frame: frame - badgeStartFrame,
              fps,
              config: { damping: 18, stiffness: 180 },
            });
            return (
              <div
                key={type}
                style={{
                  backgroundColor: "rgba(255,255,255,0.05)",
                  border: `2px solid ${badgeColors[i]}`,
                  borderRadius: 12,
                  padding: "20px 40px",
                  transform: `translateX(${(1 - progress) * 120}px)`,
                  opacity: progress,
                  minWidth: 480,
                  textAlign: "center",
                }}
              >
                <span
                  style={{
                    color: badgeColors[i],
                    fontSize: 28,
                    fontWeight: 700,
                    fontFamily: "system-ui",
                    letterSpacing: "0.06em",
                  }}
                >
                  {type}
                </span>
              </div>
            );
          })}
        </AbsoluteFill>
      </Sequence>

      {/* Scene 4: CTA */}
      <Sequence from={360} durationInFrames={90}>
        <AbsoluteFill
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexDirection: "column",
            gap: 16,
          }}
        >
          <TextScene
            text="Find yours at"
            frame={frame}
            startFrame={360}
            fps={fps}
          />
          <p
            style={{
              color: "#E84A2F",
              fontSize: 48,
              fontWeight: 800,
              fontFamily: "'Outfit', system-ui",
              margin: 0,
              opacity: interpolate(frame - 360, [20, 40], [0, 1], {
                extrapolateRight: "clamp",
              }),
            }}
          >
            hookcut.ai
          </p>
        </AbsoluteFill>
      </Sequence>
    </AbsoluteFill>
  );
}
