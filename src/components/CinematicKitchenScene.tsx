import { motion, AnimatePresence } from 'framer-motion';
import type { DemoSnapshot } from '../types/timeline';
import { useReducedMotion } from '../hooks/useReducedMotion';
import { BoardDeck } from './BoardDeck';
import { SPEAKER_LABELS } from '../data/participants';

interface Props {
  snapshot: DemoSnapshot;
  live?: boolean;
}

const SCENE_IMG = {
  /** hero_B_2: screen-to-camera, Buzz roster on glass, night kitchen */
  idle: `${import.meta.env.BASE_URL}images/scene/ceo-kitchen-hero.jpg`,
  /** Same still while CEO VO is active (do not flip to phone-away frames) */
  speaking: `${import.meta.env.BASE_URL}images/scene/ceo-kitchen-hero.jpg`,
};

/**
 * Photoreal Sunday-night kitchen: CEO Daniel Mercer holds the phone screen to camera.
 * Interactive Buzz also lives in the hero iPhone frame on the right.
 */
export function CinematicKitchenScene({ snapshot, live = false }: Props) {
  const reduced = useReducedMotion();
  const { scene, ceoPose, lighting, activeSpeaker } = snapshot;

  if (scene === 'black' || scene === 'end-card') {
    return (
      <div
        className="absolute inset-0 bg-black"
        aria-hidden={scene === 'black'}
        data-testid="scene-black"
      />
    );
  }

  const glowClass =
    lighting === 'pressure'
      ? 'kitchen-glow-pressure'
      : lighting === 'resolve'
        ? 'kitchen-glow-resolve'
        : 'kitchen-glow';

  const talking =
    live &&
    activeSpeaker?.speaker === 'ceo' &&
    Boolean(activeSpeaker.text);

  // Speaking still when CEO is VO-active; otherwise mid-call hold
  const photoSrc = talking ? SCENE_IMG.speaking : SCENE_IMG.idle;

  const poseTransform = {
    tired: 'scale(1.01) translateY(4px)',
    guarded: 'scale(1.005) translateY(2px)',
    engaged: 'scale(1) translateY(0)',
    upright: 'scale(1.01) translateY(-2px)',
    relieved: 'scale(1.015) translateY(-3px)',
  }[ceoPose];

  const speakerLabel = activeSpeaker?.speaker
    ? SPEAKER_LABELS[activeSpeaker.speaker]
    : null;

  return (
    <div
      className={`absolute inset-0 overflow-hidden ${glowClass}`}
      data-testid="cinematic-kitchen"
      data-ceo-pose={ceoPose}
      data-lighting={lighting}
      data-live={live ? 'true' : 'false'}
      aria-label="Sunday night kitchen. Daniel Mercer on a live Buzz call with his iPhone."
    >
      {/* Photoreal hero still — CEO mid-call on iPhone Pro Max */}
      <motion.div
        className="kitchen-photo-bg"
        style={{
          backgroundImage: `url(${photoSrc})`,
          transform: reduced ? undefined : poseTransform,
        }}
        animate={
          reduced
            ? undefined
            : {
                scale: talking ? [1.02, 1.035, 1.02] : [1.02, 1.025, 1.02],
              }
        }
        transition={
          reduced
            ? undefined
            : { duration: talking ? 2.4 : 18, repeat: Infinity, ease: 'easeInOut' }
        }
        key={photoSrc}
      />

      {/* Subtle CSS glow fallback layers under photo (if image fails) */}
      <div className="kitchen-photo-vignette" />

      {/* LIVE call chrome */}
      <div className="absolute top-5 left-5 z-10 flex max-w-[min(92%,360px)] flex-col gap-2">
        {live && (
          <div className="kitchen-live-badge" data-testid="kitchen-live-badge">
            <span className="dot" aria-hidden />
            Live · iPhone · WisdomTwin
          </div>
        )}
        <div className="rounded-xl border border-white/10 bg-black/45 px-3 py-2 backdrop-blur-md">
          <p className="text-[9px] tracking-[0.2em] text-[var(--cream-dim)] uppercase">
            Board strategy session
          </p>
          <p className="mt-0.5 text-xs text-[var(--cream)]">Thursday, 9:00 AM · 14 hours</p>
        </div>
        {live && speakerLabel && (
          <AnimatePresence mode="wait">
            <motion.div
              key={activeSpeaker?.eventId ?? speakerLabel}
              initial={reduced ? false : { opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={reduced ? undefined : { opacity: 0 }}
              className="rounded-xl border border-[var(--warm)]/25 bg-black/50 px-3 py-2 backdrop-blur-md"
              data-testid="kitchen-active-line"
            >
              <p className="text-[9px] tracking-[0.16em] text-[var(--warm)] uppercase">
                {speakerLabel}
                {activeSpeaker?.speaker === 'ceo' ? ' · on device' : ' · in Buzz'}
              </p>
              {activeSpeaker?.text && (
                <p className="mt-1 line-clamp-2 text-xs leading-snug text-[var(--cream)]">
                  {activeSpeaker.text}
                </p>
              )}
            </motion.div>
          </AnimatePresence>
        )}
      </div>

      {/* Board deck chip — lower left on desk area of photo */}
      {live && snapshot.confidence != null && (
        <div className="absolute bottom-8 left-6 z-10 hidden w-44 sm:block">
          <BoardDeck confidence={snapshot.confidence} room={snapshot.room} />
        </div>
      )}

      {/* Mouth / speaking pulse when CEO talks */}
      {talking && !reduced && (
        <div
          className="pointer-events-none absolute top-[38%] left-[48%] h-16 w-16 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[var(--warm)]/10 blur-2xl md:left-[42%]"
          data-testid="ceo-speech-glow"
          aria-hidden
        />
      )}

      {/* Soft bottom fade into phone column on desktop */}
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-[var(--ink)]/50 to-transparent md:hidden" />
    </div>
  );
}
