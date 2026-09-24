import "./index.css";
import { Composition } from "remotion";
import { VIDEO } from "./theme";
import { Part1, PART1_DURATION } from "./parts/Part1";
import { Part2, PART2_DURATION } from "./parts/Part2";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Part1"
        component={Part1}
        durationInFrames={PART1_DURATION}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
      />
      <Composition
        id="Part2"
        component={Part2}
        durationInFrames={PART2_DURATION}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
      />
    </>
  );
};
