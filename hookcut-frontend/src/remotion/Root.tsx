import { Composition } from "remotion";
import { HookCutHeroDemo } from "./compositions/HookCutHeroDemo";
import { HookScoreExplainer } from "./compositions/HookScoreExplainer";
import { PenaltyEngineComparison } from "./compositions/PenaltyEngineComparison";

export function RemotionRoot() {
  return (
    <>
      <Composition
        id="HookCutHeroDemo"
        component={HookCutHeroDemo}
        durationInFrames={900}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="HookScoreExplainer"
        component={HookScoreExplainer}
        durationInFrames={450}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="PenaltyEngineComparison"
        component={PenaltyEngineComparison}
        durationInFrames={300}
        fps={30}
        width={1920}
        height={800}
      />
    </>
  );
}
