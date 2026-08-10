import type {
  ActiveSpeakerState,
  BoardArtifact,
  DemoEvent,
  DemoPhase,
  DemoSnapshot,
  DialogueEvent,
  EndCardEvent,
  MusicEvent,
  ParticipantState,
  RoomMode,
  SceneEvent,
  SpeakerId,
  TimelineConfig,
  VisualFocusEvent,
} from '../types/timeline';
import { BOARD_ARTIFACTS } from '../data/blockers';
import { TWIN_IDS } from '../data/participants';

const DEFAULT_PARTICIPANTS = (): Record<string, ParticipantState> => {
  const map: Record<string, ParticipantState> = { ceo: 'present', buzz: 'present' };
  for (const id of TWIN_IDS) map[id] = 'offline';
  return map;
};

export function createInitialSnapshot(): DemoSnapshot {
  return {
    timeMs: 0,
    phase: 'ready',
    room: 'idle',
    roomTitleCard: null,
    scene: 'black',
    ceoPose: 'tired',
    lighting: 'cold',
    activeSpeaker: null,
    caption: null,
    participants: DEFAULT_PARTICIPANTS(),
    visibleEvidenceIds: [],
    blockers: {},
    showBlockerRegister: false,
    escalations: [],
    confidence: null,
    artifacts: BOARD_ARTIFACTS.map((a) => ({ ...a, status: 'pending' as const })),
    safeDeclineActive: false,
    focus: 'kitchen',
    musicBed: 'none',
    endCard: null,
    systemMessages: [],
    completed: false,
  };
}

function isActive(event: DemoEvent, timeMs: number): boolean {
  if (timeMs < event.startMs) return false;
  if (event.endMs === undefined) return timeMs >= event.startMs;
  return timeMs >= event.startMs && timeMs < event.endMs;
}

function hasStarted(event: DemoEvent, timeMs: number): boolean {
  return timeMs >= event.startMs;
}

function latestActive<T extends DemoEvent>(events: T[], timeMs: number): T | null {
  let best: T | null = null;
  for (const e of events) {
    if (isActive(e, timeMs) && (!best || e.startMs >= best.startMs)) best = e;
  }
  return best;
}

function latestStarted<T extends DemoEvent>(events: T[], timeMs: number): T | null {
  let best: T | null = null;
  for (const e of events) {
    if (hasStarted(e, timeMs) && (!best || e.startMs >= best.startMs)) best = e;
  }
  return best;
}

export function buildSnapshot(
  config: TimelineConfig,
  timeMs: number,
  phase: DemoPhase = 'playing',
): DemoSnapshot {
  const clamped = Math.max(0, Math.min(timeMs, config.durationMs));
  const events = config.events;
  const snap = createInitialSnapshot();
  snap.timeMs = clamped;
  snap.phase = phase;

  const scenes = events.filter((e): e is SceneEvent => e.type === 'scene');
  const scene = latestStarted(scenes, clamped);
  if (scene) {
    snap.scene = scene.scene;
    if (scene.ceoPose) snap.ceoPose = scene.ceoPose;
    if (scene.lighting) snap.lighting = scene.lighting;
  }

  const rooms = events.filter((e) => e.type === 'room-transition');
  const roomEv = latestStarted(rooms, clamped);
  if (roomEv && roomEv.type === 'room-transition') {
    snap.room = roomEv.room as RoomMode;
    snap.roomTitleCard = roomEv.titleCard ?? null;
  }

  const dialogues = events.filter((e): e is DialogueEvent => e.type === 'dialogue');
  const activeDialogue = latestActive(dialogues, clamped);
  if (activeDialogue) {
    const end = activeDialogue.endMs ?? activeDialogue.startMs + 4000;
    snap.activeSpeaker = {
      speaker: activeDialogue.speaker,
      text: activeDialogue.text,
      startMs: activeDialogue.startMs,
      endMs: end,
      eventId: activeDialogue.id,
    };
    snap.caption = { speaker: activeDialogue.speaker, text: activeDialogue.text };
    if (activeDialogue.speaker in snap.participants) {
      snap.participants[activeDialogue.speaker] = 'speaking';
    }
  } else {
    const recent = [...dialogues]
      .filter((d) => d.endMs !== undefined && clamped >= d.endMs && clamped - d.endMs < 800)
      .sort((a, b) => (b.endMs ?? 0) - (a.endMs ?? 0))[0];
    if (recent) snap.caption = { speaker: recent.speaker, text: recent.text };
  }

  for (const e of events) {
    if (e.type !== 'participant-join' || !hasStarted(e, clamped)) continue;
    const state = e.state ?? 'present';
    if (snap.participants[e.participantId] !== 'speaking') {
      snap.participants[e.participantId] = state;
    } else if (e.participantId !== snap.activeSpeaker?.speaker) {
      snap.participants[e.participantId] = state;
    }
  }

  for (const e of events) {
    if (e.type !== 'evidence' || !hasStarted(e, clamped)) continue;
    if (e.action === 'show' || e.action === 'highlight') {
      if (!snap.visibleEvidenceIds.includes(e.evidenceId)) snap.visibleEvidenceIds.push(e.evidenceId);
      const cardRole = e.evidenceId.split('_')[0];
      if (cardRole && snap.participants[cardRole] && snap.participants[cardRole] !== 'speaking' && isActive(e, clamped)) {
        snap.participants[cardRole] = 'finding-evidence';
      }
    }
    if (e.action === 'hide') {
      snap.visibleEvidenceIds = snap.visibleEvidenceIds.filter((id) => id !== e.evidenceId);
    }
  }

  for (const e of events) {
    if (e.type !== 'blocker' || !hasStarted(e, clamped)) continue;
    if (e.action === 'show-register') {
      snap.showBlockerRegister = true;
      continue;
    }
    if (e.action === 'create' || e.action === 'update' || e.action === 'resolve' || e.action === 'escalate') {
      snap.blockers[e.blockerId] = e.status ?? (e.action === 'resolve' ? 'resolved' : 'open');
      if (e.action === 'create') snap.showBlockerRegister = true;
    }
  }

  for (const e of events) {
    if (e.type !== 'escalation' || !hasStarted(e, clamped)) continue;
    if (!snap.escalations.includes(e.escalationId)) snap.escalations.push(e.escalationId);
    if (snap.participants.cto && snap.participants.cto !== 'speaking' && isActive(e, clamped)) {
      snap.participants.cto = 'escalating';
    }
  }

  const conf = latestStarted(events.filter((e) => e.type === 'confidence'), clamped);
  if (conf && conf.type === 'confidence') snap.confidence = conf.value;

  for (const e of events) {
    if (e.type !== 'artifact' || !hasStarted(e, clamped)) continue;
    const existing = snap.artifacts.find((a) => a.id === e.artifactId);
    if (existing) {
      existing.status = e.action === 'ready' || e.action === 'update' ? 'ready' : existing.status;
      if (e.detail) existing.detail = e.detail;
      if (e.title) existing.title = e.title;
    } else {
      snap.artifacts.push({
        id: e.artifactId,
        title: e.title,
        detail: e.detail ?? '',
        status: e.action === 'ready' ? 'ready' : 'pending',
      });
    }
  }

  const decline = latestStarted(events.filter((e) => e.type === 'safe-decline'), clamped);
  if (decline && decline.type === 'safe-decline') {
    snap.safeDeclineActive = decline.active;
    if (decline.active && snap.participants.cto !== 'speaking') snap.participants.cto = 'declining';
  }

  const focusEv = latestStarted(events.filter((e) => e.type === 'visual-focus'), clamped);
  if (focusEv && focusEv.type === 'visual-focus') snap.focus = focusEv.target as VisualFocusEvent['target'];

  const musicEv = latestStarted(events.filter((e) => e.type === 'music'), clamped);
  if (musicEv && musicEv.type === 'music') snap.musicBed = musicEv.bed as MusicEvent['bed'];

  const endCard = latestStarted(events.filter((e): e is EndCardEvent => e.type === 'end-card'), clamped);
  snap.endCard = endCard;

  const systems = events.filter((e) => e.type === 'system' && hasStarted(e, clamped));
  snap.systemMessages = systems.slice(-3).map((e) => (e.type === 'system' ? e.text : '')).filter(Boolean);

  if (clamped >= config.durationMs - 50) {
    snap.completed = true;
    if (phase === 'playing' || phase === 'paused') snap.phase = 'complete';
    snap.room = 'complete';
  }

  if (snap.room === 'build' && snap.confidence !== null && snap.confidence >= 90) {
    for (const id of TWIN_IDS) {
      if (snap.participants[id] === 'present' || snap.participants[id] === 'finding-evidence') {
        snap.participants[id] = 'consensus';
      }
    }
  }

  return snap;
}

export function getEventsAt(config: TimelineConfig, timeMs: number): DemoEvent[] {
  return config.events.filter((e) => isActive(e, timeMs));
}

export function getEventsStartingBetween(config: TimelineConfig, fromMs: number, toMs: number): DemoEvent[] {
  return config.events.filter((e) => e.startMs > fromMs && e.startMs <= toMs);
}

export function getActiveSpeaker(config: TimelineConfig, timeMs: number): ActiveSpeakerState | null {
  return buildSnapshot(config, timeMs).activeSpeaker;
}

export function getRoomAt(config: TimelineConfig, timeMs: number): RoomMode {
  return buildSnapshot(config, timeMs).room;
}

export function sortTimeline(events: DemoEvent[]): DemoEvent[] {
  return [...events].sort((a, b) => {
    if (a.startMs !== b.startMs) return a.startMs - b.startMs;
    return (a.priority ?? 0) - (b.priority ?? 0);
  });
}

export function assertTimelineOrdered(events: DemoEvent[]): boolean {
  for (let i = 1; i < events.length; i += 1) {
    if (events[i].startMs < events[i - 1].startMs) return false;
  }
  return true;
}

export function dialogueEvents(config: TimelineConfig): DialogueEvent[] {
  return config.events.filter((e): e is DialogueEvent => e.type === 'dialogue');
}

export function estimateSpeechMs(text: string, wpm = 155): number {
  const words = text.trim().split(/\s+/).filter(Boolean).length;
  const base = (words / wpm) * 60_000;
  const pauses = (text.match(/[.!?]/g) || []).length * 220;
  const commas = (text.match(/[,;:]/g) || []).length * 90;
  return Math.max(900, Math.round(base + pauses + commas));
}

export function speakerColor(speaker: SpeakerId): string {
  const map: Record<SpeakerId, string> = {
    narrator: '#a8a29e',
    ceo: '#f5f0e8',
    cfo: '#7dd3fc',
    cto: '#86efac',
    cro: '#fcd34d',
    cmo: '#f9a8d4',
    legal: '#c4b5fd',
    buzz: '#94a3b8',
    system: '#64748b',
  };
  return map[speaker];
}

export function formatTime(ms: number): string {
  const totalSec = Math.max(0, Math.floor(ms / 1000));
  const m = Math.floor(totalSec / 60);
  const s = totalSec % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export function cloneArtifacts(artifacts: BoardArtifact[]): BoardArtifact[] {
  return artifacts.map((a) => ({ ...a }));
}
