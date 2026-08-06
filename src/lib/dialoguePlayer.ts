/**
 * Timeline-synced dialogue player for pre-rendered executive VO (ElevenLabs).
 * Prefers /audio/dialogue/{id}.mp3; falls back to Web Speech only if a file is missing.
 */
import type { SpeakerId } from '../types/timeline';
import { speakDialogue, cancelSpeech, speechSupported } from './speechFallback';

export interface DialogueClip {
  id: string;
  speaker: SpeakerId;
  text: string;
  /** Absolute path under public, e.g. /audio/dialogue/ceo-01.mp3 */
  src: string;
  startMs: number;
  endMs: number;
}

/** Map timeline dialogue event ids → audio file basenames (without .mp3). */
export const DIALOGUE_AUDIO_MAP: Record<string, string> = {
  'dlg-narr-1': 'narrator-cold-open',
  'dlg-buzz-open': 'buzz-activation',
  'dlg-ceo-open': 'ceo-01',
  'dlg-cro-1': 'cro-01',
  'dlg-cmo-1': 'cmo-01',
  'dlg-ceo-kill': 'ceo-02',
  'dlg-ceo-hole': 'ceo-03',
  'dlg-legal-quick': 'legal-01',
  'dlg-cfo-quick': 'cfo-01',
  'dlg-cto-quick': 'cto-01',
  'dlg-ceo-legal-first': 'ceo-04',
  'dlg-legal-full': 'legal-02',
  'dlg-cfo-full': 'cfo-02',
  'dlg-cto-full': 'cto-02',
  'dlg-cto-decline': 'cto-02',
  'dlg-ceo-stop': 'ceo-05',
  'dlg-cto-not-kill': 'cto-03',
  'dlg-buzz-blockers': 'buzz-blockers',
  'dlg-ceo-build': 'ceo-06',
  'dlg-legal-build': 'legal-03',
  'dlg-cfo-build': 'cfo-03',
  'dlg-cto-build': 'cto-04',
  'dlg-cro-build': 'cro-02',
  'dlg-cmo-build': 'cmo-02',
  'dlg-ceo-why': 'ceo-07',
  'dlg-buzz-pattern': 'buzz-pattern',
  'dlg-ceo-which': 'ceo-08',
  'dlg-buzz-cyber': 'buzz-sequence',
  'dlg-ceo-presentation': 'ceo-09',
  'dlg-buzz-package': 'buzz-output',
  'dlg-ceo-sleep': 'ceo-10',
  'dlg-buzz-close': 'buzz-close',
};

function publicAudioUrl(basename: string): string {
  const base = import.meta.env.BASE_URL || '/';
  const root = base.endsWith('/') ? base : `${base}/`;
  return `${root}audio/dialogue/${basename}.mp3`;
}

export class DialoguePlayer {
  private audio: HTMLAudioElement | null = null;
  private currentKey: string | null = null;
  private muted = false;
  private unlocked = false;
  private missing = new Set<string>();
  private useSpeechFallback = true;

  async unlock(): Promise<void> {
    if (this.unlocked) return;
    // Silent play/pause to unlock autoplay after user gesture
    const a = new Audio();
    a.src =
      'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=';
    try {
      await a.play();
      a.pause();
    } catch {
      /* ignore */
    }
    this.unlocked = true;
  }

  setMuted(muted: boolean): void {
    this.muted = muted;
    if (this.audio) this.audio.muted = muted;
    if (muted) cancelSpeech();
  }

  stop(): void {
    cancelSpeech();
    if (this.audio) {
      this.audio.pause();
      this.audio.removeAttribute('src');
      this.audio.load();
      this.audio = null;
    }
    this.currentKey = null;
  }

  /**
   * Play the clip for this timeline dialogue event if it changed.
   * Seeking mid-line restarts from the relative offset when possible.
   */
  async playEvent(opts: {
    eventId: string;
    speaker: SpeakerId;
    text: string;
    startMs: number;
    endMs: number;
    timeMs: number;
    playing: boolean;
  }): Promise<void> {
    if (!opts.playing || this.muted) {
      this.pauseOnly();
      return;
    }

    const basename = DIALOGUE_AUDIO_MAP[opts.eventId];
    // Key by audio file so split caption windows (e.g. CTO full/decline) don't restart VO
    const key = basename ?? `${opts.eventId}`;
    // For multi-event same file, offset from the earliest known start of that file in this session
    const offsetSec = Math.max(0, (opts.timeMs - opts.startMs) / 1000);

    if (!basename || this.missing.has(basename)) {
      if (this.useSpeechFallback && speechSupported() && this.currentKey !== key) {
        this.currentKey = key;
        this.stopAudioElement();
        await speakDialogue(opts.speaker, opts.text);
      }
      return;
    }

    const src = publicAudioUrl(basename);

    if (this.currentKey === key && this.audio) {
      if (this.audio.paused && opts.playing) {
        void this.audio.play().catch(() => undefined);
      }
      // Drift correction only when seek jumped significantly
      if (Math.abs(this.audio.currentTime - offsetSec) > 1.2 && offsetSec < 2) {
        // Only hard-seek near the start of a line; mid-line caption splits should not seek
        try {
          this.audio.currentTime = offsetSec;
        } catch {
          /* ignore */
        }
      }
      return;
    }

    // New line
    this.currentKey = key;
    cancelSpeech();
    this.stopAudioElement();

    const el = new Audio(src);
    el.preload = 'auto';
    el.muted = this.muted;
    this.audio = el;

    await new Promise<void>((resolve) => {
      const onReady = () => {
        el.removeEventListener('canplay', onReady);
        resolve();
      };
      el.addEventListener('canplay', onReady);
      el.addEventListener(
        'error',
        () => {
          this.missing.add(basename);
          this.currentKey = null;
          resolve();
        },
        { once: true },
      );
      el.load();
      if (el.readyState >= 2) resolve();
    });

    if (this.audio !== el) return;

    if (this.missing.has(basename)) {
      if (this.useSpeechFallback && speechSupported()) {
        await speakDialogue(opts.speaker, opts.text);
      }
      return;
    }

    try {
      // Only seek when resuming mid-line after a scrub (offset meaningfully into the line)
      if (offsetSec > 0.35 && Number.isFinite(el.duration)) {
        el.currentTime = Math.min(offsetSec, Math.max(0, el.duration - 0.05));
      }
      await el.play();
    } catch {
      if (this.useSpeechFallback && speechSupported()) {
        await speakDialogue(opts.speaker, opts.text);
      }
    }
  }

  private pauseOnly(): void {
    cancelSpeech();
    if (this.audio && !this.audio.paused) this.audio.pause();
  }

  private stopAudioElement(): void {
    if (this.audio) {
      this.audio.pause();
      this.audio.removeAttribute('src');
      this.audio.load();
      this.audio = null;
    }
  }
}

export const dialoguePlayer = new DialoguePlayer();
