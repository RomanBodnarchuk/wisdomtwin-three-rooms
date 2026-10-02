import { AbsoluteFill, Composition } from "remotion";
import {
  Close,
  EmilyFilm,
  FILM_DURATION,
  IMessage,
  Mail,
  Open,
  Signal,
  Slack,
  Telegram,
  WhatsApp,
  Zoom,
} from "./EmilyFilm";

const HOLD = 300;

const hold = (Component: React.FC): React.FC => {
  const Held: React.FC = () => {
    return (
      <AbsoluteFill style={{ backgroundColor: "#07080c" }}>
        <Component />
      </AbsoluteFill>
    );
  };
  return Held;
};

const channelDemos = [
  { id: "DemoOpen", component: hold(Open) },
  { id: "DemoIMessage", component: hold(IMessage) },
  { id: "DemoWhatsApp", component: hold(WhatsApp) },
  { id: "DemoTelegram", component: hold(Telegram) },
  { id: "DemoSignal", component: hold(Signal) },
  { id: "DemoSlack", component: hold(Slack) },
  { id: "DemoEmail", component: hold(Mail) },
  { id: "DemoZoom", component: hold(Zoom) },
  { id: "DemoClose", component: hold(Close) },
];

export const MyComposition = () => {
  return (
    <>
      <Composition
        id="EmilyAlwaysOn"
        component={EmilyFilm}
        durationInFrames={FILM_DURATION}
        fps={30}
        width={1920}
        height={1080}
      />
      {channelDemos.map(({ id, component }) => (
        <Composition
          key={id}
          id={id}
          component={component}
          durationInFrames={HOLD}
          fps={30}
          width={1920}
          height={1080}
        />
      ))}
    </>
  );
};
