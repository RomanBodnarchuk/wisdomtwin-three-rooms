import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { PlaybackClock } from '../lib/clock';
import { audioEngine, type SfxId } from '../lib/audioEngine';
import { buildSnapshot, getEventsStartingBetween } from '../lib/timelineEngine';
import type { CutId, DemoPhase, DemoSnapshot, TimelineConfig } from '../types/timeline';
import { FULL_TIMELINE } from '../data/fullTimeline';
import { INVESTOR_60_TIMELINE } from '../data/investor60Timeline';
import { OUTREACH_45_TIMELINE } from '../data/outreach45Timeline';
import { INVESTOR_240_TIMELINE } from '../data/investor240Timeline';

const CUTS: Record<CutId, TimelineConfig> = {
  full: FULL_TIMELINE,
  investor60: INVESTOR_60_TIMELINE,
  outreach45: OUTREACH_45_TIMELINE,
  investor240: INVESTOR_240_TIMELINE,
};

export interface DemoPlaybackApi {
  snapshot: DemoSnapshot;
  phase: DemoPhase;
  cutId: CutId;
  config: TimelineConfig;
  muted: boolean;
  captionsOn: boolean;
  investorMode: boolean;
  timeMs: number;
  durationMs: number;
  mediaRef: React.RefObject<HTMLAudioElement>;
  start: () => Promise<void>;
  pause: () => void;
  resume: () => void;
  togglePlay: () => void;
  restart: () => void;
  replay: () => Promise<void>;
  seek: (ms: number) => void;
  setMuted: (muted: boolean) => void;
  toggleMute: () => void;
  setCaptionsOn: (on: boolean) => void;
  setInvestorMode: (on: boolean) => void;
  setCut: (cut: CutId) => void;
  error: string | null;
}

export function useDemoPlayback(initialCut: CutId = 'full'): DemoPlaybackApi {
  const [cutId, setCutId] = useState<CutId>(initialCut);
  const config = CUTS[cutId];
  const [phase, setPhase] = useState<DemoPhase>('ready');
  const [timeMs, setTimeMs] = useState(0);
  const [muted, setMutedState] = useState(false);
  const [captionsOn, setCaptionsOn] = useState(true);
  const [investorMode, setInvestorMode] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clockRef = useRef<PlaybackClock | null>(null);
  const mediaRef = useRef<HTMLAudioElement>(null!);
  const lastTickRef = useRef(0);
  const phaseRef = useRef<DemoPhase>('ready');

  useEffect(() => {
    phaseRef.current = phase;
  }, [phase]);

  useEffect(() => {
    clockRef.current?.destroy();
    const clock = new PlaybackClock(config.durationMs);
    clockRef.current = clock;
    if (mediaRef.current) clock.attachMedia(mediaRef.current);

    const unsub = clock.subscribe((state) => {
      setTimeMs(state.timeMs);
      if (state.timeMs >= config.durationMs - 30 && phaseRef.current === 'playing') {
        setPhase('complete');
        audioEngine.playSfx('huddle-close', 'end-close');
        audioEngine.setMusicBed('none');
      }
    });

    setTimeMs(0);
    setPhase('ready');
    audioEngine.resetSession();
    lastTickRef.current = 0;

    return () => {
      unsub();
      clock.destroy();
    };
  }, [config.durationMs, cutId]);

  useEffect(() => {
    const el = mediaRef.current;
    if (!el || !clockRef.current) return;
    clockRef.current.attachMedia(el);
    el.muted = muted;
  }, [muted, cutId]);

  // Tab switching is the norm for emailed links — pause cleanly on hide, resume on return
  const pausedByHideRef = useRef(false);
  useEffect(() => {
    const onVis = () => {
      if (document.hidden) {
        if (phaseRef.current === 'playing') {
          pausedByHideRef.current = true;
          clockRef.current?.pause();
          setPhase('paused');
        }
        return;
      }
      if (pausedByHideRef.current && phaseRef.current === 'paused') {
        pausedByHideRef.current = false;
        setPhase('playing');
        clockRef.current?.play();
        return;
      }
      if (clockRef.current && phaseRef.current === 'playing') {
        setTimeMs(clockRef.current.now());
      }
    };
    document.addEventListener('visibilitychange', onVis);
    return () => document.removeEventListener('visibilitychange', onVis);
  }, []);

  const snapshot = useMemo(
    () => buildSnapshot(config, timeMs, phase),
    [config, timeMs, phase],
  );

  useEffect(() => {
    if (phase !== 'playing') return;
    const from = lastTickRef.current;
    const to = timeMs;
    if (to < from) {
      audioEngine.resetSession();
      lastTickRef.current = to;
      return;
    }
    const started = getEventsStartingBetween(config, from, to);
    for (const ev of started) {
      if (ev.type === 'sound') {
        const map: Record<string, SfxId> = {
          'phone-tap': 'phone-tap',
          'secure-room': 'secure-room',
          'join-tones': 'join-tone',
          'dream-chime': 'dream-chime',
          'stress-chime': 'stress-chime',
          'build-chime': 'build-chime',
          'safe-decline': 'safe-decline',
          'pattern-detect': 'pattern-detect',
          'board-complete': 'board-complete',
          'huddle-close': 'huddle-close',
          'blocker-tone': 'blocker-tone',
        };
        if (ev.soundId === 'join-tones') {
          audioEngine.playJoinSequence(ev.id);
        } else {
          const sfx = map[ev.soundId];
          if (sfx) audioEngine.playSfx(sfx, ev.id, ev.volume ?? 1);
        }
      }
      if (ev.type === 'music') {
        audioEngine.setMusicBed(ev.bed);
      }
    }
    lastTickRef.current = to;
  }, [timeMs, phase, config]);

  useEffect(() => {
    if (phase === 'playing' || phase === 'paused') {
      audioEngine.setMusicBed(snapshot.musicBed);
    }
  }, [snapshot.musicBed, phase]);

  const start = useCallback(async () => {
    try {
      setError(null);
      await audioEngine.unlock();
      audioEngine.resetSession();
      lastTickRef.current = 0;
      clockRef.current?.seek(0);
      setPhase('playing');
      clockRef.current?.play();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to start experience');
      setPhase('error');
    }
  }, []);

  const pause = useCallback(() => {
    clockRef.current?.pause();
    setPhase('paused');
  }, []);

  const resume = useCallback(() => {
    if (phaseRef.current === 'complete') return;
    setPhase('playing');
    clockRef.current?.play();
  }, []);

  const togglePlay = useCallback(() => {
    if (phaseRef.current === 'playing') pause();
    else if (phaseRef.current === 'paused') resume();
    else if (phaseRef.current === 'ready' || phaseRef.current === 'complete') void start();
  }, [pause, resume, start]);

  const restart = useCallback(() => {
    audioEngine.resetSession();
    audioEngine.setMusicBed('none');
    lastTickRef.current = 0;
    clockRef.current?.reset();
    setTimeMs(0);
    setPhase('ready');
  }, []);

  const replay = useCallback(async () => {
    restart();
    await start();
  }, [restart, start]);

  const seek = useCallback(
    (ms: number) => {
      const clamped = Math.max(0, Math.min(ms, config.durationMs));
      if (clamped < lastTickRef.current) audioEngine.resetSession();
      lastTickRef.current = clamped;
      clockRef.current?.seek(clamped);
      setTimeMs(clamped);
      if (clamped >= config.durationMs - 30) setPhase('complete');
      else if (phaseRef.current === 'complete') setPhase('paused');
    },
    [config.durationMs],
  );

  const setMuted = useCallback((m: boolean) => {
    setMutedState(m);
    audioEngine.setMuted(m);
    clockRef.current?.setMuted(m);
    if (mediaRef.current) mediaRef.current.muted = m;
  }, []);

  const toggleMute = useCallback(() => {
    setMuted(!muted);
  }, [muted, setMuted]);

  const setCut = useCallback((cut: CutId) => {
    audioEngine.resetSession();
    audioEngine.setMusicBed('none');
    setCutId(cut);
    setPhase('ready');
    setTimeMs(0);
  }, []);

  return {
    snapshot,
    phase,
    cutId,
    config,
    muted,
    captionsOn,
    investorMode,
    timeMs,
    durationMs: config.durationMs,
    mediaRef,
    start,
    pause,
    resume,
    togglePlay,
    restart,
    replay,
    seek,
    setMuted,
    toggleMute,
    setCaptionsOn,
    setInvestorMode,
    setCut,
    error,
  };
}
