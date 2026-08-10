/**
 * Timeline type definitions for the WisdomTwin Executive Huddle demo.
 * Reconstructed from compiled source maps; types are erased at runtime.
 */

export type CutId = 'full' | 'investor60' | 'outreach45' | 'investor240';

export type DemoPhase = 'ready' | 'playing' | 'paused' | 'complete' | 'error';

export type SpeakerId =
  | 'narrator'
  | 'ceo'
  | 'cfo'
  | 'cto'
  | 'cro'
  | 'cmo'
  | 'legal'
  | 'buzz'
  | 'system';

export type RoomMode = 'idle' | 'dream' | 'stress-test' | 'build' | 'complete';

export type SceneId =
  | 'black'
  | 'kitchen-cold'
  | 'kitchen-active'
  | 'kitchen-focus'
  | 'kitchen-resolved'
  | 'kitchen-glow'
  | 'kitchen-glow-pressure'
  | 'kitchen-glow-resolve'
  | 'end-card';

export type CeoPose = 'tired' | 'guarded' | 'engaged' | 'upright' | 'relieved';

export type LightingMode = 'cold' | 'warm' | 'pressure' | 'resolve';

export type ParticipantState =
  | 'offline'
  | 'joining'
  | 'present'
  | 'thinking'
  | 'speaking'
  | 'finding-evidence'
  | 'escalating'
  | 'declining'
  | 'consensus';

export type BlockerStatus = 'open' | 'mitigated' | 'escalated' | 'resolved';

export type ArtifactStatus = 'pending' | 'ready';

export type MusicBedId = 'none' | 'dream' | 'stress' | 'build' | 'silence' | 'lift';

export type VisualFocusTarget =
  | 'kitchen'
  | 'buzz'
  | 'evidence'
  | 'blockers'
  | 'board-deck'
  | 'escalation'
  | 'end-card';

interface BaseEvent {
  id: string;
  type: string;
  startMs: number;
  endMs?: number;
  priority?: number;
}

export interface SceneEvent extends BaseEvent {
  type: 'scene';
  scene: SceneId;
  ceoPose?: CeoPose;
  lighting?: LightingMode;
}

export interface MusicEvent extends BaseEvent {
  type: 'music';
  bed: MusicBedId;
  volume?: number;
}

export interface DialogueEvent extends BaseEvent {
  type: 'dialogue';
  speaker: SpeakerId;
  text: string;
  allowOverlap?: boolean;
}

export interface SoundEvent extends BaseEvent {
  type: 'sound';
  soundId: string;
  volume?: number;
}

export interface ParticipantJoinEvent extends BaseEvent {
  type: 'participant-join';
  participantId: string;
  state?: ParticipantState;
}

export interface VisualFocusEvent extends BaseEvent {
  type: 'visual-focus';
  target: VisualFocusTarget;
}

export interface RoomTransitionEvent extends BaseEvent {
  type: 'room-transition';
  room: RoomMode;
  label?: string;
  /** One-shot title card shown under the room label (first transition only). */
  titleCard?: string;
}

export interface EvidenceEvent extends BaseEvent {
  type: 'evidence';
  evidenceId: string;
  action: 'show' | 'highlight' | 'hide';
}

export interface BlockerEvent extends BaseEvent {
  type: 'blocker';
  blockerId: string;
  action: 'create' | 'update' | 'resolve' | 'escalate' | 'show-register';
  status?: BlockerStatus;
}

export interface EscalationEvent extends BaseEvent {
  type: 'escalation';
  escalationId: string;
  action: 'create' | 'update' | 'resolve';
}

export interface ConfidenceEvent extends BaseEvent {
  type: 'confidence';
  value: number;
}

export interface ArtifactEvent extends BaseEvent {
  type: 'artifact';
  artifactId: string;
  action: 'pending' | 'update' | 'ready';
  title: string;
  detail?: string;
}

export interface SafeDeclineEvent extends BaseEvent {
  type: 'safe-decline';
  active: boolean;
}

export interface EndCardEvent extends BaseEvent {
  type: 'end-card';
  stage: number;
  lines: string[];
  showInvestorContrast?: boolean;
  /** Money-math card — the cost of waiting vs. one huddle. */
  moneyCard?: string[];
}

export interface SystemEvent extends BaseEvent {
  type: 'system';
  text: string;
}

export type DemoEvent =
  | SceneEvent
  | MusicEvent
  | DialogueEvent
  | SoundEvent
  | ParticipantJoinEvent
  | VisualFocusEvent
  | RoomTransitionEvent
  | EvidenceEvent
  | BlockerEvent
  | EscalationEvent
  | ConfidenceEvent
  | ArtifactEvent
  | SafeDeclineEvent
  | EndCardEvent
  | SystemEvent;

export interface TimelineConfig {
  id: CutId;
  label: string;
  durationMs: number;
  events: DemoEvent[];
}

export interface ActiveSpeakerState {
  speaker: SpeakerId;
  text: string;
  startMs: number;
  endMs: number;
  eventId: string;
}

export interface BoardArtifact {
  id: string;
  title: string;
  detail: string;
  status: ArtifactStatus;
}

export interface BlockerItem {
  id: string;
  title: string;
  category: string;
  policy: string;
  precedent: string;
  owner: string;
  decision: string;
  status: BlockerStatus;
}

export interface EscalationItem {
  id: string;
  title: string;
  reason: string;
  reviewer: string;
  estimatedMinutes: number;
  status: 'pending-human' | 'resolved';
  auditRecorded: boolean;
}

export interface EvidenceMetric {
  label: string;
  value: string;
}

export interface EvidenceCard {
  id: string;
  title: string;
  role: SpeakerId | 'buzz' | 'system';
  sources: string[];
  finding: string;
  metrics: EvidenceMetric[];
}

export interface DemoSnapshot {
  timeMs: number;
  phase: DemoPhase;
  room: RoomMode;
  roomTitleCard: string | null;
  scene: SceneId;
  ceoPose: CeoPose;
  lighting: LightingMode;
  activeSpeaker: ActiveSpeakerState | null;
  caption: { speaker: SpeakerId; text: string } | null;
  participants: Record<string, ParticipantState>;
  visibleEvidenceIds: string[];
  blockers: Record<string, BlockerStatus>;
  showBlockerRegister: boolean;
  escalations: string[];
  confidence: number | null;
  artifacts: BoardArtifact[];
  safeDeclineActive: boolean;
  focus: VisualFocusTarget;
  musicBed: MusicBedId;
  endCard: EndCardEvent | null;
  systemMessages: string[];
  completed: boolean;
}
