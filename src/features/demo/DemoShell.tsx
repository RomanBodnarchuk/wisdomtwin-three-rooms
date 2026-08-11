import { useCallback, useEffect, useMemo, useState } from 'react';
import { useDemoPlayback } from '../../hooks/useDemoPlayback';
import { useKeyboardControls } from '../../hooks/useKeyboardControls';
import { PreloadManager } from '../../components/PreloadManager';
import { StartExperience } from '../../components/StartExperience';
import { ErrorState } from '../../components/ErrorState';
import { CinematicKitchenScene } from '../../components/CinematicKitchenScene';
import { BuzzDevice } from '../../components/BuzzDevice';
import { CaptionLayer } from '../../components/CaptionLayer';
import { RoomMode } from '../../components/RoomMode';
import { EndCard } from '../../components/EndCard';
import { InvestorModeToggle } from '../../components/InvestorModeToggle';
import { SyntheticDataDisclosure } from '../../components/SyntheticDataDisclosure';
import { dialoguePlayer } from '../../lib/dialoguePlayer';
import { InvestorProofRail } from '../../components/InvestorProofRail';
import { useInvestorAnalytics } from '../../hooks/useInvestorAnalytics';
import { trackInvestorEvent } from '../../lib/investorAnalytics';

const ROOM_OVERLAY_WINDOWS = [
  { startMs: 800, endMs: 3_600 },
  { startMs: 65_800, endMs: 70_200 },
  { startMs: 94_600, endMs: 97_600 },
  { startMs: 135_200, endMs: 138_500 },
] as const;

const FILM_ENTRY_MS = 65_800;

/**
 * Top-level Three Rooms experience shell.
 * Desktop: cinematic kitchen + Buzz phone.
 * Mobile: Buzz prioritized, kitchen as atmosphere.
 * Dialogue: ElevenLabs executive VO (Web Speech only if an asset is missing).
 * Cut: the 2:54 investor film is the default experience. The 8:07 original stays
 * in code (useDemoPlayback('full')) but short cuts are not offered in UI.
 */
export function DemoShell() {
  const playback = useDemoPlayback('investor240');
  // Investor mode is for investors only — enable with ?investor in the URL
  const investorParam =
    typeof window !== 'undefined' && new URLSearchParams(window.location.search).has('investor');
  const {
    snapshot,
    phase,
    cutId,
    muted,
    captionsOn,
    investorMode,
    timeMs,
    durationMs,
    mediaRef,
    start,
    pause,
    resume,
    togglePlay,
    restart,
    replay,
    seek,
    toggleMute,
    setCaptionsOn,
    setInvestorMode,
    error,
  } = playback;

  const [started, setStarted] = useState(false);
  const live = started && phase !== 'ready';
  const active = snapshot.activeSpeaker;

  useEffect(() => {
    dialoguePlayer.setMuted(muted);
  }, [muted]);

  // ElevenLabs executive VO — synced to the timeline clock
  useEffect(() => {
    if (phase === 'ready') {
      dialoguePlayer.stop();
      return;
    }
    if (!live || !active?.speaker || !active.eventId) return;
    void dialoguePlayer.playEvent({
      eventId: active.eventId,
      speaker: active.speaker,
      text: active.text,
      startMs: active.startMs,
      endMs: active.endMs,
      timeMs,
      playing: phase === 'playing' && !muted,
    });
  }, [live, phase, muted, active, timeMs]);

  const handleStart = useCallback(async () => {
    setStarted(true);
    await dialoguePlayer.unlock();
    await start();
    seek(FILM_ENTRY_MS);
  }, [seek, start]);

  const handleRestart = useCallback(() => {
    dialoguePlayer.stop();
    setStarted(false);
    restart();
  }, [restart]);

  const handleReplay = useCallback(async () => {
    dialoguePlayer.stop();
    setStarted(true);
    await dialoguePlayer.unlock();
    await replay();
    seek(FILM_ENTRY_MS);
  }, [replay, seek]);

  const keyboardHandlers = useMemo(
    () => ({
      onTogglePlay: () => {
        if (!started) {
          void handleStart();
          return;
        }
        togglePlay();
      },
      onMute: toggleMute,
      onCaptions: () => setCaptionsOn(!captionsOn),
      onRestart: handleRestart,
      onSeekRelative: (delta: number) => {
        if (!started) return;
        seek(timeMs + delta);
      },
      onEscape: () => {
        /* drawers managed inside BuzzDevice */
      },
      enabled: true,
    }),
    [started, handleStart, togglePlay, toggleMute, captionsOn, setCaptionsOn, handleRestart, seek, timeMs],
  );

  useKeyboardControls(keyboardHandlers);
  useInvestorAnalytics({
    cutId,
    durationMs: durationMs - FILM_ENTRY_MS,
    phase,
    timeMs: Math.max(0, timeMs - FILM_ENTRY_MS),
  });

  if (error) {
    return <ErrorState message={error} onRetry={() => void handleStart()} />;
  }

  const roomOverlay = ROOM_OVERLAY_WINDOWS.find(
    ({ startMs, endMs }) => timeMs >= startMs && timeMs < endMs,
  );
  const showRoomOverlay = live && Boolean(roomOverlay) && snapshot.focus !== 'end-card';
  const visibleCaption =
    timeMs >= FILM_ENTRY_MS && snapshot.caption?.speaker === 'narrator' ? null : snapshot.caption;

  return (
    <PreloadManager>
      <div
        className="relative min-h-[100dvh] w-full overflow-hidden bg-[var(--ink)]"
        data-testid="demo-shell"
        data-phase={phase}
        data-room={snapshot.room}
        data-safe-decline={snapshot.safeDeclineActive ? 'true' : 'false'}
      >
        {/* Hidden master media element — attach real mix at public/audio/master/{cut}.mp3 */}
        <audio
          ref={mediaRef}
          preload="none"
          playsInline
          className="hidden"
          data-testid="master-audio"
          src={`/audio/master/${cutId}.mp3`}
          onError={() => {
            /* Missing master audio is expected; performance clock + speech fallback used */
          }}
        />

        {/* Cinematic environment — CEO live on iPhone 19 Max */}
        <div className="absolute inset-0 md:right-[40%]">
          <CinematicKitchenScene snapshot={snapshot} live={live} />
          {showRoomOverlay && phase === 'playing' && (
            <div className="pointer-events-none absolute inset-0 z-10 flex">
              <RoomMode room={snapshot.room} overlay subtitle={snapshot.roomTitleCard} />
            </div>
          )}
        </div>

        {/* Timed investor thesis — makes problem, moat, mechanism, and value explicit */}
        {live && snapshot.scene !== 'end-card' && <InvestorProofRail timeMs={timeMs} />}

        {/* Captions */}
        <CaptionLayer
          visible={captionsOn && live && snapshot.scene !== 'end-card'}
          speaker={visibleCaption?.speaker ?? null}
          text={visibleCaption?.text ?? null}
        />

        {/* Hero iPhone 19 Max — live Buzz app */}
        <div className="relative z-20 flex min-h-[100dvh] items-end justify-center px-3 pt-[26vh] pb-4 md:absolute md:inset-y-0 md:right-0 md:w-[40%] md:items-center md:px-5 md:pt-0">
          <div className="flex h-[min(760px,74dvh)] w-full max-w-[400px] flex-col items-center md:h-[min(860px,94dvh)]">
            <p className="mb-2 hidden text-[10px] tracking-[0.2em] text-[var(--cream-dim)] uppercase md:block">
              Live Executive Huddle · iPhone
            </p>
            <div className="h-full w-full">
              <BuzzDevice
                snapshot={snapshot}
                phase={phase}
                cutId={cutId}
                timeMs={timeMs}
                durationMs={durationMs}
                timelineStartMs={FILM_ENTRY_MS}
                muted={muted}
                captionsOn={captionsOn}
                live={live}
                onTogglePlay={() => {
                  if (phase === 'playing') pause();
                  else if (phase === 'paused') resume();
                  else void handleStart();
                }}
                onRestart={handleRestart}
                onToggleMute={toggleMute}
                onToggleCaptions={() => setCaptionsOn(!captionsOn)}
                onSeek={seek}
                onStartHuddle={() => void handleStart()}
              />
            </div>
          </div>
        </div>

        {/* Top chrome when live */}
        {live && snapshot.scene !== 'end-card' && (
          <div className="absolute top-3 right-3 left-3 z-30 flex flex-wrap items-center justify-between gap-2 md:right-[42%]">
            <div className="rounded-full border border-white/10 bg-black/40 px-3 py-1.5 backdrop-blur">
              <p className="text-[10px] tracking-[0.18em] text-[var(--cream-dim)] uppercase">
                WisdomTwin · Judgment platform · Demo film · 2:54
              </p>
            </div>
            {investorParam && (
              <div className="hidden items-center gap-3 rounded-2xl border border-white/10 bg-black/40 px-3 py-2 backdrop-blur sm:flex">
                <InvestorModeToggle on={investorMode} onChange={setInvestorMode} />
              </div>
            )}
          </div>
        )}

        {/* Start gate */}
        {!started && phase !== 'complete' && (
          <StartExperience
            investorMode={investorMode}
            showInvestorToggle={investorParam}
            onInvestorModeChange={setInvestorMode}
            onStart={() => void handleStart()}
          />
        )}

        {/* End card */}
        {snapshot.endCard && (phase === 'complete' || snapshot.scene === 'end-card') && (
          <EndCard
            endCard={snapshot.endCard}
            investorMode={investorMode}
            onReplay={() => void handleReplay()}
            onRestart={handleRestart}
          />
        )}

        {/* Footer disclosure on start only handled in StartExperience; live compact */}
        {live && snapshot.scene !== 'end-card' && (
          <div className="pointer-events-none absolute bottom-2 left-3 z-20 hidden md:block">
            <SyntheticDataDisclosure compact />
          </div>
        )}

        {/* Persistent booking CTA — one ask, always visible while live */}
        {live && snapshot.scene !== 'end-card' && (
          <a
            href="https://calendly.com/romanbodnarchuk/20min"
            target="_blank"
            rel="noreferrer"
            data-testid="live-cta"
            onClick={() => trackInvestorEvent('investor_cta_click', { placement: 'live' })}
            className="absolute right-3 bottom-3 z-30 rounded-full bg-[var(--cream)] px-4 py-2 text-[11px] font-semibold tracking-[0.12em] text-[var(--ink)] uppercase shadow-lg transition hover:bg-white md:right-[calc(40%+1rem)]"
          >
            Book a Judgment Assessment ($0)
          </a>
        )}
      </div>
    </PreloadManager>
  );
}
