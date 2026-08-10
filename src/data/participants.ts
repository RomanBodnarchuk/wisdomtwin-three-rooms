import type { SpeakerId } from '../types/timeline';

export interface ParticipantMeta {
  id: SpeakerId;
  label: string;
  shortLabel: string;
  initials: string;
  glyph: string;
  role: string;
  isTwin: boolean;
  firstIntro: string;
}

export const PARTICIPANTS: ParticipantMeta[] = [
  { id: 'cfo', label: 'CFO Twin', shortLabel: 'CFO', initials: 'CF', glyph: '◈', role: 'Chief Financial Officer', isTwin: true, firstIntro: "Your CFO's twin." },
  { id: 'cto', label: 'CTO Twin', shortLabel: 'CTO', initials: 'CT', glyph: '◇', role: 'Chief Technology Officer', isTwin: true, firstIntro: "Your CTO's twin." },
  { id: 'cro', label: 'CRO Twin', shortLabel: 'CRO', initials: 'CR', glyph: '△', role: 'Chief Revenue Officer', isTwin: true, firstIntro: "Your CRO's twin." },
  { id: 'cmo', label: 'CMO Twin', shortLabel: 'CMO', initials: 'CM', glyph: '○', role: 'Chief Marketing Officer', isTwin: true, firstIntro: "Your CMO's twin." },
  { id: 'legal', label: 'Chief Legal Officer Twin', shortLabel: 'Legal', initials: 'CL', glyph: '□', role: 'Chief Legal Officer', isTwin: true, firstIntro: "Your Chief Legal Officer's twin." },
];

export const SPEAKER_LABELS: Record<SpeakerId, string> = {
  narrator: 'Narrator',
  ceo: 'Daniel Mercer, CEO',
  cfo: 'CFO Twin',
  cto: 'CTO Twin',
  cro: 'CRO Twin',
  cmo: 'CMO Twin',
  legal: 'Chief Legal Officer Twin',
  buzz: 'WisdomTwin',
  system: 'System',
};

export const TWIN_IDS: SpeakerId[] = ['cfo', 'cto', 'cro', 'cmo', 'legal'];

export function getParticipant(id: SpeakerId): ParticipantMeta | undefined {
  return PARTICIPANTS.find((p) => p.id === id);
}
