import type { CutId, SpeakerId } from '../types/timeline';
import { FULL_TIMELINE } from './fullTimeline';
import { INVESTOR_60_TIMELINE } from './investor60Timeline';
import { OUTREACH_45_TIMELINE } from './outreach45Timeline';
import { INVESTOR_240_TIMELINE } from './investor240Timeline';
import { SPEAKER_LABELS } from './participants';

export interface TranscriptLine {
  id: string;
  startMs: number;
  endMs: number;
  speaker: SpeakerId;
  speakerLabel: string;
  text: string;
}

const configs = {
  full: FULL_TIMELINE,
  investor60: INVESTOR_60_TIMELINE,
  outreach45: OUTREACH_45_TIMELINE,
  investor240: INVESTOR_240_TIMELINE,
} as const;

export function getTranscript(cut: CutId): TranscriptLine[] {
  const config = configs[cut];
  return config.events
    .filter((e) => e.type === 'dialogue')
    .map((e) => {
      if (e.type !== 'dialogue') throw new Error('unreachable');
      return {
        id: e.id,
        startMs: e.startMs,
        endMs: e.endMs ?? e.startMs + 3000,
        speaker: e.speaker,
        speakerLabel: SPEAKER_LABELS[e.speaker],
        text: e.text,
      };
    });
}

export const FULL_TRANSCRIPT = getTranscript('full');
