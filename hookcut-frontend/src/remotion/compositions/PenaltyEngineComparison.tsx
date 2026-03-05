import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

interface ClipCardProps {
  label: string;
  timestamp: string;
  bad: boolean;
  revealFrame: number;
}

function ClipCard({ label, timestamp, bad, revealFrame }: ClipCardProps) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    frame: frame - revealFrame,
    fps,
    config: { damping: 16, stiffness: 200 },
  });

  const color = bad ? "#DC2626" : "#16A34A";
  const icon = bad ? "✗" : "✓";

  return (
    <div
      style={{
        backgroundColor: "#1A1A1A",
        border: `1px solid ${bad ? "rgba(220,38,38,0.3)" : "rgba(22,163,74,0.3)"}`,
        borderRadius: 10,
        padding: "12px 16px",
        display: "flex",
        alignItems: "center",
        gap: 12,
        position: "relative",
        overflow: "hidden",
        opacity: Math.min(progress * 1.5, 1),
        transform: `translateY(${(1 - Math.min(progress * 1.2, 1)) * 20}px)`,
      }}
    >
      <div style={{ flex: 1 }}>
        <p
          style={{
            color: "#F5F5F5",
            fontSize: 14,
            fontWeight: 600,
            margin: "0 0 4px",
            fontFamily: "system-ui",
          }}
        >
          {label}
        </p>
        <p
          style={{
            color: "#71717A",
            fontSize: 12,
            fontFamily: "monospace",
            margin: 0,
          }}
        >
          {timestamp}
        </p>
      </div>
      <div
        style={{
          width: 32,
          height: 32,
          borderRadius: "50%",
          backgroundColor: color,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          transform: `scale(${progress})`,
          color: "#FFFFFF",
          fontSize: 16,
          fontWeight: 700,
          flexShrink: 0,
        }}
      >
        {icon}
      </div>
    </div>
  );
}

export function PenaltyEngineComparison() {
  const frame = useCurrentFrame();

  const titleOpacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });

  const badClips: ClipCardProps[] = [
    {
      label: '"Hey guys, welcome back!"',
      timestamp: "0:00 → 0:08",
      bad: true,
      revealFrame: 30,
    },
    {
      label: "Sponsor segment",
      timestamp: "4:12 → 5:47",
      bad: true,
      revealFrame: 70,
    },
    {
      label: "Mid-sentence cut",
      timestamp: "7:23 → 7:31",
      bad: true,
      revealFrame: 110,
    },
  ];

  const goodClips: ClipCardProps[] = [
    {
      label: "87 · CURIOSITY GAP",
      timestamp: "3:07 → 3:40",
      bad: false,
      revealFrame: 40,
    },
    {
      label: "82 · OPEN LOOP",
      timestamp: "8:23 → 8:55",
      bad: false,
      revealFrame: 80,
    },
    {
      label: "74 · SHOCK STATISTIC",
      timestamp: "1:32 → 2:01",
      bad: false,
      revealFrame: 120,
    },
    {
      label: "91 · CONTRARIAN CLAIM",
      timestamp: "5:41 → 6:14",
      bad: false,
      revealFrame: 160,
    },
    {
      label: "68 · SOCIAL PROOF",
      timestamp: "11:04 → 11:38",
      bad: false,
      revealFrame: 200,
    },
  ];

  return (
    <AbsoluteFill
      style={{ backgroundColor: "#111111", display: "flex", alignItems: "stretch" }}
    >
      {/* Left: Generic clipper */}
      <div
        style={{
          flex: 1,
          padding: "48px 48px 48px 60px",
          borderRight: "1px solid rgba(255,255,255,0.08)",
          display: "flex",
          flexDirection: "column",
          gap: 16,
        }}
      >
        <div style={{ marginBottom: 8, opacity: titleOpacity }}>
          <p
            style={{
              color: "#71717A",
              fontSize: 11,
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              fontFamily: "system-ui",
              margin: "0 0 6px",
            }}
          >
            Generic Clipper
          </p>
          <p
            style={{
              color: "#F5F5F5",
              fontSize: 20,
              fontWeight: 700,
              fontFamily: "'Outfit', system-ui",
              margin: 0,
            }}
          >
            Any moment that looks good
          </p>
        </div>
        {badClips.map((clip) => (
          <ClipCard key={clip.label} {...clip} />
        ))}
      </div>

      {/* Right: HookCut */}
      <div
        style={{
          flex: 1,
          padding: "48px 60px 48px 48px",
          display: "flex",
          flexDirection: "column",
          gap: 16,
        }}
      >
        <div style={{ marginBottom: 8, opacity: titleOpacity }}>
          <p
            style={{
              color: "#E84A2F",
              fontSize: 11,
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              fontFamily: "system-ui",
              margin: "0 0 6px",
            }}
          >
            HookCut
          </p>
          <p
            style={{
              color: "#F5F5F5",
              fontSize: 20,
              fontWeight: 700,
              fontFamily: "'Outfit', system-ui",
              margin: 0,
            }}
          >
            Only hooks that score
          </p>
        </div>
        {goodClips.map((clip) => (
          <ClipCard key={clip.label} {...clip} />
        ))}
      </div>
    </AbsoluteFill>
  );
}
