export type ClockSource = 'media' | 'performance';

export interface ClockState {
  timeMs: number;
  playing: boolean;
  source: ClockSource;
}

export class PlaybackClock {
  private media: HTMLMediaElement | null = null;
  private playing = false;
  private baseMediaMs = 0;
  private basePerfMs = 0;
  private pausedAtMs = 0;
  private durationMs: number;
  private source: ClockSource = 'performance';
  private listeners = new Set<(state: ClockState) => void>();
  private raf = 0;

  constructor(durationMs: number) {
    this.durationMs = durationMs;
  }

  setDuration(durationMs: number): void {
    this.durationMs = durationMs;
  }

  attachMedia(el: HTMLMediaElement | null): void {
    this.media = el;
    this.source = el ? 'media' : 'performance';
  }

  getSource(): ClockSource {
    return this.media ? 'media' : this.source;
  }

  now(): number {
    if (this.media && !this.media.error && this.media.readyState >= 1) {
      return Math.min(this.media.currentTime * 1000, this.durationMs);
    }
    if (!this.playing) return this.pausedAtMs;
    const elapsed = performance.now() - this.basePerfMs;
    return Math.min(this.baseMediaMs + elapsed, this.durationMs);
  }

  isPlaying(): boolean {
    return this.playing;
  }

  play(): void {
    if (this.playing) return;
    this.playing = true;
    this.baseMediaMs = this.pausedAtMs;
    this.basePerfMs = performance.now();
    if (this.media) {
      void this.media.play().catch(() => {
        this.source = 'performance';
      });
    }
    this.startLoop();
    this.emit();
  }

  pause(): void {
    if (!this.playing) return;
    this.pausedAtMs = this.now();
    this.playing = false;
    if (this.media) this.media.pause();
    this.stopLoop();
    this.emit();
  }

  seek(ms: number): void {
    const clamped = Math.max(0, Math.min(ms, this.durationMs));
    this.pausedAtMs = clamped;
    this.baseMediaMs = clamped;
    this.basePerfMs = performance.now();
    if (this.media) {
      try {
        this.media.currentTime = clamped / 1000;
      } catch {
        /* ignore */
      }
    }
    this.emit();
  }

  reset(): void {
    this.pause();
    this.seek(0);
  }

  setMuted(muted: boolean): void {
    if (this.media) this.media.muted = muted;
  }

  subscribe(fn: (state: ClockState) => void): () => void {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  destroy(): void {
    this.stopLoop();
    this.listeners.clear();
    this.media = null;
  }

  private startLoop(): void {
    this.stopLoop();
    const raf =
      typeof requestAnimationFrame === 'function'
        ? requestAnimationFrame.bind(globalThis)
        : (cb: FrameRequestCallback) =>
            setTimeout(() => cb(performance.now()), 16) as unknown as number;
    const tick = () => {
      if (!this.playing) return;
      if (this.media && this.media.readyState >= 2 && !this.media.paused) {
        this.pausedAtMs = this.media.currentTime * 1000;
        this.baseMediaMs = this.pausedAtMs;
        this.basePerfMs = performance.now();
      }
      const t = this.now();
      this.emit();
      if (t >= this.durationMs) {
        this.playing = false;
        this.pausedAtMs = this.durationMs;
        if (this.media) this.media.pause();
        this.stopLoop();
        this.emit();
        return;
      }
      this.raf = raf(tick);
    };
    this.raf = raf(tick);
  }

  private stopLoop(): void {
    if (!this.raf) return;
    if (typeof cancelAnimationFrame === 'function') {
      cancelAnimationFrame(this.raf);
    } else {
      clearTimeout(this.raf);
    }
    this.raf = 0;
  }

  private emit(): void {
    const state: ClockState = {
      timeMs: this.now(),
      playing: this.playing,
      source: this.getSource(),
    };
    for (const fn of this.listeners) fn(state);
  }
}
