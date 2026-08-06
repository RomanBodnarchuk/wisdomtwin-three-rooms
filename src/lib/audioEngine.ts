export type SfxId =
  | 'phone-tap'
  | 'secure-room'
  | 'join-tone'
  | 'dream-chime'
  | 'stress-chime'
  | 'build-chime'
  | 'safe-decline'
  | 'pattern-detect'
  | 'board-complete'
  | 'huddle-close'
  | 'blocker-tone'
  | 'soft-tick';

export type MusicBed = 'none' | 'dream' | 'stress' | 'build' | 'silence' | 'lift';

interface ToneSpec {
  frequency: number;
  duration: number;
  type: OscillatorType;
  attack: number;
  decay: number;
  volume: number;
  detune?: number;
}

const SFX: Record<SfxId, ToneSpec[]> = {
  'phone-tap': [{ frequency: 180, duration: 0.06, type: 'sine', attack: 0.005, decay: 0.05, volume: 0.18 }],
  'secure-room': [
    { frequency: 220, duration: 0.35, type: 'sine', attack: 0.02, decay: 0.3, volume: 0.12 },
    { frequency: 330, duration: 0.4, type: 'sine', attack: 0.04, decay: 0.35, volume: 0.08, detune: 5 },
  ],
  'join-tone': [{ frequency: 520, duration: 0.12, type: 'sine', attack: 0.01, decay: 0.1, volume: 0.1 }],
  'dream-chime': [
    { frequency: 392, duration: 0.55, type: 'sine', attack: 0.02, decay: 0.5, volume: 0.1 },
    { frequency: 523.25, duration: 0.7, type: 'sine', attack: 0.05, decay: 0.6, volume: 0.07 },
  ],
  'stress-chime': [
    { frequency: 311, duration: 0.45, type: 'triangle', attack: 0.02, decay: 0.4, volume: 0.09 },
    { frequency: 233, duration: 0.55, type: 'sine', attack: 0.04, decay: 0.5, volume: 0.07 },
  ],
  'build-chime': [
    { frequency: 349, duration: 0.4, type: 'sine', attack: 0.02, decay: 0.35, volume: 0.1 },
    { frequency: 440, duration: 0.55, type: 'sine', attack: 0.05, decay: 0.45, volume: 0.08 },
    { frequency: 523, duration: 0.7, type: 'sine', attack: 0.08, decay: 0.55, volume: 0.06 },
  ],
  'safe-decline': [{ frequency: 185, duration: 0.8, type: 'sine', attack: 0.1, decay: 0.7, volume: 0.05 }],
  'pattern-detect': [
    { frequency: 660, duration: 0.15, type: 'sine', attack: 0.01, decay: 0.12, volume: 0.08 },
    { frequency: 880, duration: 0.25, type: 'sine', attack: 0.05, decay: 0.2, volume: 0.06 },
  ],
  'board-complete': [
    { frequency: 440, duration: 0.3, type: 'sine', attack: 0.02, decay: 0.25, volume: 0.09 },
    { frequency: 554, duration: 0.4, type: 'sine', attack: 0.06, decay: 0.35, volume: 0.07 },
    { frequency: 659, duration: 0.55, type: 'sine', attack: 0.1, decay: 0.45, volume: 0.06 },
  ],
  'huddle-close': [
    { frequency: 330, duration: 0.5, type: 'sine', attack: 0.03, decay: 0.45, volume: 0.08 },
    { frequency: 220, duration: 0.7, type: 'sine', attack: 0.08, decay: 0.6, volume: 0.06 },
  ],
  'blocker-tone': [{ frequency: 277, duration: 0.25, type: 'triangle', attack: 0.02, decay: 0.22, volume: 0.07 }],
  'soft-tick': [{ frequency: 1200, duration: 0.03, type: 'sine', attack: 0.001, decay: 0.025, volume: 0.03 }],
};

export class AudioEngine {
  private ctx: AudioContext | null = null;
  private master: GainNode | null = null;
  private musicGain: GainNode | null = null;
  private sfxGain: GainNode | null = null;
  private musicOsc: OscillatorNode[] = [];
  private musicLfo: OscillatorNode | null = null;
  private muted = false;
  private unlocked = false;
  private currentBed: MusicBed = 'none';
  private playedSfx = new Set<string>();

  async unlock(): Promise<void> {
    if (this.unlocked && this.ctx?.state === 'running') return;
    const ctx = this.ensureContext();
    if (ctx.state === 'suspended') await ctx.resume();
    const buffer = ctx.createBuffer(1, 1, 22050);
    const source = ctx.createBufferSource();
    source.buffer = buffer;
    source.connect(ctx.destination);
    source.start(0);
    this.unlocked = true;
  }

  setMuted(muted: boolean): void {
    this.muted = muted;
    if (this.master && this.ctx) {
      this.master.gain.setTargetAtTime(muted ? 0 : 1, this.ctx.currentTime, 0.02);
    }
  }

  isMuted(): boolean {
    return this.muted;
  }

  resetSession(): void {
    this.playedSfx.clear();
    this.setMusicBed('none');
  }

  playSfx(id: SfxId, eventKey?: string, volume = 1): void {
    if (eventKey && this.playedSfx.has(eventKey)) return;
    if (eventKey) this.playedSfx.add(eventKey);
    if (this.muted || !this.unlocked) return;
    const ctx = this.ensureContext();
    const specs = SFX[id];
    if (!specs) return;
    const now = ctx.currentTime;
    for (const spec of specs) {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = spec.type;
      osc.frequency.value = spec.frequency;
      if (spec.detune) osc.detune.value = spec.detune;
      const vol = spec.volume * volume;
      gain.gain.setValueAtTime(0, now);
      gain.gain.linearRampToValueAtTime(vol, now + spec.attack);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + spec.duration);
      osc.connect(gain);
      gain.connect(this.sfxGain ?? ctx.destination);
      osc.start(now);
      osc.stop(now + spec.duration + 0.05);
    }
  }

  playJoinSequence(baseEventKey: string): void {
    const delays = [0, 0.55, 1.1, 1.7, 2.35];
    delays.forEach((d, i) => {
      window.setTimeout(() => {
        this.playSfx('join-tone', `${baseEventKey}-${i}`, 0.9 - i * 0.05);
      }, d * 1000);
    });
  }

  setMusicBed(bed: MusicBed): void {
    if (bed === this.currentBed) return;
    this.currentBed = bed;
    this.stopMusic();
    if (this.muted || !this.unlocked) return;
    if (bed === 'none' || bed === 'silence') return;
    const ctx = this.ensureContext();
    const now = ctx.currentTime;
    const freqs =
      bed === 'dream' ? [110, 164.81] :
      bed === 'stress' ? [98, 146.83] :
      bed === 'build' ? [130.81, 196] :
      [174.61, 261.63];
    const bedGain = ctx.createGain();
    bedGain.gain.setValueAtTime(0, now);
    bedGain.gain.linearRampToValueAtTime(bed === 'lift' ? 0.035 : 0.022, now + 1.2);
    bedGain.connect(this.musicGain ?? ctx.destination);
    this.musicOsc = freqs.map((f, i) => {
      const osc = ctx.createOscillator();
      osc.type = 'sine';
      osc.frequency.value = f;
      osc.detune.value = i * 3;
      osc.connect(bedGain);
      osc.start(now);
      return osc;
    });
    const lfo = ctx.createOscillator();
    const lfoGain = ctx.createGain();
    lfo.frequency.value = 0.05;
    lfoGain.gain.value = 0.008;
    lfo.connect(lfoGain);
    lfoGain.connect(bedGain.gain);
    lfo.start(now);
    this.musicLfo = lfo;
  }

  dispose(): void {
    this.stopMusic();
    void this.ctx?.close();
    this.ctx = null;
    this.master = null;
    this.musicGain = null;
    this.sfxGain = null;
    this.unlocked = false;
  }

  private stopMusic(): void {
    for (const osc of this.musicOsc) {
      try { osc.stop(); osc.disconnect(); } catch { /* */ }
    }
    this.musicOsc = [];
    if (this.musicLfo) {
      try { this.musicLfo.stop(); this.musicLfo.disconnect(); } catch { /* */ }
      this.musicLfo = null;
    }
  }

  private ensureContext(): AudioContext {
    if (!this.ctx) {
      const Ctx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      this.ctx = new Ctx();
      this.master = this.ctx.createGain();
      this.master.gain.value = this.muted ? 0 : 1;
      this.master.connect(this.ctx.destination);
      this.musicGain = this.ctx.createGain();
      this.musicGain.connect(this.master);
      this.sfxGain = this.ctx.createGain();
      this.sfxGain.connect(this.master);
    }
    return this.ctx;
  }
}

export const audioEngine = new AudioEngine();
