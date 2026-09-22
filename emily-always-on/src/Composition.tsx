import { Composition } from "remotion";
import { EmilyFilm, FILM_DURATION } from "./EmilyFilm";

export const MyComposition = () => {
  return (
    <Composition
      id="EmilyAlwaysOn"
      component={EmilyFilm}
      durationInFrames={FILM_DURATION}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
