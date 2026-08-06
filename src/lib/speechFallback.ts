import type { SpeakerId } from '../types/timeline';

const RATE: Partial<Record<SpeakerId, number>> = {
  narrator: 0.95,
  ceo: 0.92,
  cfo: 0.96,
  cto: 0.97,
  cro: 1.0,
  cmo: 1.02,
  legal: 0.94,
  buzz: 0.9,
  system: 0.9,
};

const PITCH: Partial<Record<SpeakerId, number>> = {
  narrator: 0.9,
  ceo: 1.05,
  cfo: 0.85,
  cto: 0.88,
  cro: 0.95,
  cmo: 1.1,
  legal: 0.82,
  buzz: 0.75,
  system: 0.7,
};

let supported: boolean | null = null;

export function speechSupported(): boolean {
  if (supported !== null) return supported;
  supported = typeof window !== 'undefined' && 'speechSynthesis' in window;
  return supported;
}

export function cancelSpeech(): void {
  if (!speechSupported()) return;
  window.speechSynthesis.cancel();
}

export async function speakDialogue(speaker: SpeakerId, text: string): Promise<void> {
  if (!speechSupported() || !text.trim()) return;
  cancelSpeech();
  return new Promise((resolve) => {
    const utter = new SpeechSynthesisUtterance(text);
    utter.rate = RATE[speaker] ?? 1;
    utter.pitch = PITCH[speaker] ?? 1;
    utter.volume = 1;
    const voices = window.speechSynthesis.getVoices();
    const preferred = pickVoice(speaker, voices);
    if (preferred) utter.voice = preferred;
    utter.onend = () => resolve();
    utter.onerror = () => resolve();
    window.speechSynthesis.speak(utter);
  });
}

function pickVoice(speaker: SpeakerId, voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice | null {
  if (voices.length === 0) return null;
  const en = voices.filter((v) => v.lang.toLowerCase().startsWith('en'));
  const pool = en.length ? en : voices;
  if (speaker === 'ceo' || speaker === 'cmo') {
    return pool.find((v) => /female|samantha|karen|moira|fiona|tessa|zira|susan/i.test(v.name)) ?? pool[0];
  }
  if (speaker === 'buzz' || speaker === 'system') {
    return pool.find((v) => /daniel|fred|alex|sam|microsoft/i.test(v.name)) ?? pool[0];
  }
  if (speaker === 'legal' || speaker === 'cfo') {
    return pool.find((v) => /daniel|david|george|arthur|james/i.test(v.name)) ?? pool[Math.min(1, pool.length - 1)];
  }
  return pool[0];
}
