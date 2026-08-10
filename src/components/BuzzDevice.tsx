import { useState } from 'react';
import type { DemoSnapshot, DemoPhase, CutId } from '../types/timeline';
import { HuddleHeader } from './HuddleHeader';
import { ParticipantList } from './ParticipantList';
import { ActiveSpeaker } from './ActiveSpeaker';
import { ConsensusMeter } from './ConsensusMeter';
import { EscalationCard } from './EscalationCard';
import { BoardOutputPanel } from './BoardOutputPanel';
import { CompletionSummary } from './CompletionSummary';
import { BlockerRegister } from './BlockerRegister';
import { EvidenceCard } from './EvidenceCard';
import { EVIDENCE_CARDS } from '../data/evidence';
import { EvidenceDrawer } from './EvidenceDrawer';
import { BlockerDrawer } from './BlockerDrawer';
import { LiveTranscript } from './LiveTranscript';
import { PlaybackControls } from './PlaybackControls';
import { RoomMode } from './RoomMode';
import { IPhoneFrame } from './IPhoneFrame';
import { SafeDeclineBanner } from './SafeDeclineBanner';

type Drawer = 'none' | 'evidence' | 'blockers' | 'escalations' | 'transcript';

interface Props {
  snapshot: DemoSnapshot;
  phase: DemoPhase;
  cutId: CutId;
  timeMs: number;
  durationMs: number;
  muted: boolean;
  captionsOn: boolean;
  live: boolean;
  onTogglePlay: () => void;
  onRestart: () => void;
  onToggleMute: () => void;
  onToggleCaptions: () => void;
  onSeek: (ms: number) => void;
  onStartHuddle?: () => void;
}

/**
 * Live Buzz iPhone app inside a photoreal iPhone Pro Max frame.
 * Status bar / Dynamic Island come from IPhoneFrame — not duplicated here.
 */
export function BuzzDevice({
  snapshot,
  phase,
  cutId,
  timeMs,
  durationMs,
  muted,
  captionsOn,
  live,
  onTogglePlay,
  onRestart,
  onToggleMute,
  onToggleCaptions,
  onSeek,
  onStartHuddle,
}: Props) {
  const [drawer, setDrawer] = useState<Drawer>('none');
  const close = () => setDrawer('none');

  const latestEvidenceId = snapshot.visibleEvidenceIds[snapshot.visibleEvidenceIds.length - 1];
  const latestEvidence = latestEvidenceId ? EVIDENCE_CARDS[latestEvidenceId] : null;
  const showConsensus = snapshot.room === 'build' || snapshot.room === 'complete';

  return (
    <IPhoneFrame model="19-max" live={live} size="hero">
      <div
        className="buzz-frame relative flex h-full w-full flex-col overflow-hidden"
        data-testid="buzz-device"
        role="region"
        aria-label="WisdomTwin executive huddle iPhone app — live"
      >
      <HuddleHeader live={live} room={snapshot.room} />

      {!live ? (
        <div className="flex flex-1 flex-col justify-between p-4">
          <div>
            <p className="text-[10px] tracking-[0.18em] text-[var(--cream-dim)] uppercase">
              Suggested participants
            </p>
            <ul className="mt-3 space-y-2 text-sm text-[var(--cream)]">
              <li>CFO Twin</li>
              <li>CTO Twin</li>
              <li>CRO Twin</li>
              <li>CMO Twin</li>
              <li>Legal Twin</li>
            </ul>
          </div>
          <button
            type="button"
            onClick={onStartHuddle}
            data-testid="buzz-start-huddle"
            className="w-full rounded-2xl bg-[var(--cream)] py-3.5 text-xs font-semibold tracking-[0.14em] text-[var(--ink)] uppercase"
          >
            Start Executive Huddle
          </button>
        </div>
      ) : (
        <>
          <div className="drawer-scroll relative min-h-0 flex-1 space-y-3 overflow-y-auto px-3 py-3">
            {/* Transient room overlay inside phone */}
            {(snapshot.room === 'dream' ||
              snapshot.room === 'stress-test' ||
              snapshot.room === 'build') &&
              timeMs > 0 && <RoomMode room={snapshot.room} />}

            <ActiveSpeaker active={snapshot.activeSpeaker} />
            <SafeDeclineBanner active={snapshot.safeDeclineActive} />
            <div className="hidden sm:block">
              <ParticipantList participants={snapshot.participants} />
            </div>

            {latestEvidence && (
              <div className="hidden sm:block">
                <EvidenceCard card={latestEvidence} highlighted={snapshot.focus === 'evidence'} />
              </div>
            )}

            {snapshot.showBlockerRegister && Object.keys(snapshot.blockers).length > 0 && (
              <div className="hidden sm:block">
                <p className="mb-1.5 text-[10px] tracking-[0.16em] text-[var(--cream-dim)] uppercase">
                  Blocker register
                </p>
                <BlockerRegister blockers={snapshot.blockers} compact />
              </div>
            )}

            <EscalationCard
              activeIds={snapshot.escalations}
              highlighted={snapshot.safeDeclineActive || snapshot.focus === 'escalation'}
            />

            <ConsensusMeter value={snapshot.confidence} visible={showConsensus} />
            <BoardOutputPanel artifacts={snapshot.artifacts} />

            {snapshot.room === 'complete' && <CompletionSummary />}
          </div>

          {/* Bottom rail */}
          <div className="hidden border-t border-[var(--ink-border)] px-2 py-2 sm:block">
            <div className="mb-1 flex justify-around text-[10px] text-[var(--cream-dim)]">
              <button type="button" className="px-2 py-1" onClick={onToggleMute}>
                {muted ? 'Unmute' : 'Mute'}
              </button>
              <button type="button" className="px-2 py-1" onClick={() => setDrawer('evidence')}>
                Evidence
              </button>
              <button type="button" className="px-2 py-1" onClick={() => setDrawer('blockers')}>
                Blockers
              </button>
              <button type="button" className="px-2 py-1" onClick={() => setDrawer('escalations')}>
                Escalations
              </button>
              <button type="button" className="px-2 py-1" onClick={onRestart}>
                End
              </button>
            </div>
          </div>
        </>
      )}

      {live && (
        <PlaybackControls
          phase={phase}
          timeMs={timeMs}
          durationMs={durationMs}
          muted={muted}
          captionsOn={captionsOn}
          onTogglePlay={onTogglePlay}
          onRestart={onRestart}
          onToggleMute={onToggleMute}
          onToggleCaptions={onToggleCaptions}
          onSeek={onSeek}
          onOpenEvidence={() => setDrawer('evidence')}
          onOpenBlockers={() => setDrawer('blockers')}
          onOpenEscalations={() => setDrawer('escalations')}
          onOpenTranscript={() => setDrawer('transcript')}
        />
      )}

      <EvidenceDrawer
        open={drawer === 'evidence'}
        visibleIds={snapshot.visibleEvidenceIds}
        onClose={close}
      />
      <BlockerDrawer open={drawer === 'blockers'} blockers={snapshot.blockers} onClose={close} />
      {drawer === 'escalations' && (
        <div
          className="absolute inset-0 z-40 flex flex-col bg-[var(--ink)]/95 p-4 backdrop-blur-md"
          role="dialog"
          aria-label="Escalations"
          data-testid="escalation-drawer"
        >
          <div className="mb-3 flex justify-between">
            <h2 className="text-xs tracking-[0.2em] uppercase">Escalations</h2>
            <button type="button" onClick={close} className="text-xs text-[var(--cream-dim)]">
              Close
            </button>
          </div>
          <EscalationCard activeIds={snapshot.escalations} highlighted />
          {snapshot.escalations.length === 0 && (
            <p className="text-sm text-[var(--cream-dim)]">No human escalations yet.</p>
          )}
        </div>
      )}
      <LiveTranscript
        open={drawer === 'transcript'}
        cutId={cutId}
        timeMs={timeMs}
        onClose={close}
        onSeek={onSeek}
      />
      </div>
    </IPhoneFrame>
  );
}

export type { Drawer };
