import type { DemoEvent, TimelineConfig } from '../types/timeline';
import { sortTimeline } from '../lib/timelineEngine';

/**
 * v2.2 recut — proof first, explanation second.
 * Opens mid-huddle on the rapid-fire exchange (was 1:38), safe decline lands at 0:45
 * (was 3:03), then the narrator explains what was just seen. Dropped segments:
 * buzz activation, CRO account analysis, CTO build detail, CRO/CMO build one-liners,
 * and the small CEO interjections. Legal block trimmed to gate one (12s window).
 * Runtime: 4:34 (was 7:37).
 */
const events: DemoEvent[] = [
  // ── COLD OPEN: mid-huddle rapid fire (no narrator, no logo) ─────────────
  { id: 'sc-black', type: 'scene', startMs: 0, endMs: 800, scene: 'black', ceoPose: 'guarded', lighting: 'pressure' },
  { id: 'sc-open', type: 'scene', startMs: 800, scene: 'kitchen-focus', ceoPose: 'guarded', lighting: 'pressure' },
  { id: 'focus-buzz', type: 'visual-focus', startMs: 0, target: 'buzz' },
  { id: 'music-stress', type: 'music', startMs: 0, bed: 'stress' },
  { id: 'room-stress', type: 'room-transition', startMs: 800, room: 'stress-test', label: 'STRESS-TEST' },
  { id: 'join-cfo', type: 'participant-join', startMs: 200, participantId: 'cfo', state: 'present' },
  { id: 'join-cto', type: 'participant-join', startMs: 300, participantId: 'cto', state: 'present' },
  { id: 'join-cro', type: 'participant-join', startMs: 400, participantId: 'cro', state: 'present' },
  { id: 'join-cmo', type: 'participant-join', startMs: 500, participantId: 'cmo', state: 'present' },
  { id: 'join-legal', type: 'participant-join', startMs: 600, participantId: 'legal', state: 'present' },
  { id: 'dlg-ceo-kill', type: 'dialogue', startMs: 800, endMs: 2750, speaker: 'ceo', text: 'Good. Now kill it.' },
  { id: 'dlg-ceo-hole', type: 'dialogue', startMs: 3050, endMs: 4165, speaker: 'ceo', text: 'Biggest hole?' },
  { id: 'dlg-legal-quick', type: 'dialogue', startMs: 4465, endMs: 5719, speaker: 'legal', text: 'Public cloud.', allowOverlap: true },
  { id: 'dlg-cfo-quick', type: 'dialogue', startMs: 6019, endMs: 6901, speaker: 'cfo', text: 'Budget.', allowOverlap: true },
  { id: 'dlg-cto-quick', type: 'dialogue', startMs: 7201, endMs: 8083, speaker: 'cto', text: 'Scale.', allowOverlap: true },
  { id: 'dlg-ceo-legal-first', type: 'dialogue', startMs: 8383, endMs: 9358, speaker: 'ceo', text: 'Legal first.' },

  // ── THE MOAT: safe decline lands at 0:29–0:45 ───────────────────────────
  { id: 'dlg-cto-full', type: 'dialogue', startMs: 10000, endMs: 29080, speaker: 'cto', text: "Your CTO's twin. I reviewed 12,400 historical authorization decisions. Ninety-one percent follow six documented policy gates and can be processed inside our private environment. The remaining nine percent are exactly where clinical judgment changed the outcome." },
  { id: 'ev-cto', type: 'evidence', startMs: 10500, endMs: 45000, evidenceId: 'cto_history', action: 'show' },
  { id: 'music-silence', type: 'music', startMs: 28500, bed: 'silence' },
  { id: 'sfx-decline', type: 'sound', startMs: 28800, soundId: 'safe-decline' },
  { id: 'safe-decline-on', type: 'safe-decline', startMs: 29100, endMs: 44690, active: true },
  { id: 'focus-escalation', type: 'visual-focus', startMs: 29100, target: 'escalation' },
  { id: 'dlg-cto-decline', type: 'dialogue', startMs: 29380, endMs: 44690, speaker: 'cto', text: 'One warning. I found no reliable precedent for peak-load throughput at the proposed volume. Confidence is below governance threshold. I am declining to answer. Recommended human reviewer: Vice President of Clinical Operations. Estimated review time: thirty-eight minutes.' },
  { id: 'ev-decline', type: 'evidence', startMs: 29600, endMs: 45000, evidenceId: 'safe_decline', action: 'show' },
  { id: 'esc-vp', type: 'escalation', startMs: 31000, escalationId: 'esc_vp_clinical', action: 'create' },
  { id: 'blk-scale-create', type: 'blocker', startMs: 31500, blockerId: 'blk_scale_precedent', action: 'escalate', status: 'escalated' },
  { id: 'safe-decline-off', type: 'safe-decline', startMs: 45000, active: false },

  // ── NOW EXPLAIN: narrator rewinds the night ──────────────────────────────
  { id: 'sc-rewind', type: 'scene', startMs: 45200, scene: 'kitchen-cold', ceoPose: 'tired', lighting: 'cold' },
  { id: 'focus-kitchen', type: 'visual-focus', startMs: 45200, target: 'kitchen' },
  { id: 'dlg-narr-1', type: 'dialogue', startMs: 45200, endMs: 65401, speaker: 'narrator', text: 'Sunday, 9:40 p.m. Daniel Mercer runs a publicly traded healthcare company. Thursday, the board expects his AI strategy. Getting his five senior officers together takes three weeks. He does not have three weeks. He has one button.' },
  { id: 'sfx-tap', type: 'sound', startMs: 63000, soundId: 'phone-tap' },
  { id: 'sfx-secure', type: 'sound', startMs: 63300, soundId: 'secure-room' },
  { id: 'sfx-joins', type: 'sound', startMs: 63600, soundId: 'join-tones' },
  { id: 'sc-active', type: 'scene', startMs: 64000, scene: 'kitchen-active', ceoPose: 'guarded', lighting: 'warm' },

  // ── DREAM: the pitch ─────────────────────────────────────────────────────
  { id: 'sfx-dream', type: 'sound', startMs: 65800, soundId: 'dream-chime' },
  { id: 'room-dream', type: 'room-transition', startMs: 65800, room: 'dream', label: 'DREAM' },
  { id: 'music-dream', type: 'music', startMs: 65800, bed: 'dream' },
  { id: 'sc-engaged', type: 'scene', startMs: 65800, scene: 'kitchen-active', ceoPose: 'engaged', lighting: 'warm' },
  { id: 'dlg-ceo-open', type: 'dialogue', startMs: 66200, endMs: 94296, speaker: 'ceo', text: "Morning. And... sorry to interrupt everyone's Sunday. My board packet locks tomorrow. If I walk in with the wrong AI strategy, I am going to spend the next year defending it. So I need you to be brutal. Here is the idea. We have two decades of prior-authorization decisions. What if we cut authorization time from fourteen days to one... and sell that speed to every payer we serve?" },
  { id: 'dlg-cmo-1', type: 'dialogue', startMs: 94600, endMs: 106071, speaker: 'cmo', text: "Your CMO's twin. And this is not a feature story. It is a category story. Nobody in our market owns judgment-speed. If we move first, we define the category." },

  // ── STRESS-TEST: legal gate one, then the budget wall ────────────────────
  { id: 'sfx-stress', type: 'sound', startMs: 106400, soundId: 'stress-chime' },
  { id: 'room-stress-2', type: 'room-transition', startMs: 106400, room: 'stress-test', label: 'STRESS-TEST' },
  { id: 'music-stress-2', type: 'music', startMs: 106400, bed: 'stress' },
  { id: 'sc-pressure', type: 'scene', startMs: 106400, scene: 'kitchen-focus', ceoPose: 'guarded', lighting: 'pressure' },
  { id: 'dlg-legal-full', type: 'dialogue', startMs: 106600, endMs: 118600, speaker: 'legal', text: "Your Chief Legal Officer's twin. Three gates. One: patient data cannot touch a public cloud model. That rules out every external model evaluated last year. I have the governance memos and the rejection rationale." },
  { id: 'ev-legal', type: 'evidence', startMs: 107000, endMs: 138000, evidenceId: 'legal_gates', action: 'show' },
  { id: 'blk-cloud-create', type: 'blocker', startMs: 107500, blockerId: 'blk_public_cloud', action: 'create', status: 'open' },
  { id: 'blk-securities-create', type: 'blocker', startMs: 110000, blockerId: 'blk_securities', action: 'create', status: 'open' },
  { id: 'blk-denial-create', type: 'blocker', startMs: 112500, blockerId: 'blk_human_denial', action: 'create', status: 'open' },
  { id: 'dlg-cfo-full', type: 'dialogue', startMs: 118800, endMs: 137515, speaker: 'cfo', text: "Your CFO's twin. The board capped new-program spending at eleven million dollars this fiscal year. That motion passed seven to two in March. I preserved the dissent notes. Anything above the cap requires board approval Thursday, not after." },
  { id: 'ev-cfo', type: 'evidence', startMs: 119200, endMs: 138000, evidenceId: 'cfo_cap', action: 'show' },
  { id: 'blk-budget-create', type: 'blocker', startMs: 119500, blockerId: 'blk_budget_cap', action: 'create', status: 'open' },
  { id: 'dlg-buzz-blockers', type: 'dialogue', startMs: 137900, endMs: 145052, speaker: 'buzz', text: 'Blocker register created. Five unresolved items. Each includes policy, precedent, owner, and required decision.' },
  { id: 'blk-register', type: 'blocker', startMs: 138200, blockerId: 'blk_public_cloud', action: 'show-register' },
  { id: 'focus-blockers', type: 'visual-focus', startMs: 138200, target: 'blockers' },

  // ── BUILD: resolutions with precedent attached ───────────────────────────
  { id: 'dlg-ceo-build', type: 'dialogue', startMs: 145400, endMs: 146747, speaker: 'ceo', text: 'Okay. Build it.' },
  { id: 'sfx-build', type: 'sound', startMs: 146800, soundId: 'build-chime' },
  { id: 'room-build', type: 'room-transition', startMs: 147000, room: 'build', label: 'BUILD' },
  { id: 'music-build', type: 'music', startMs: 147000, bed: 'build' },
  { id: 'sc-resolve-light', type: 'scene', startMs: 147000, scene: 'kitchen-focus', ceoPose: 'engaged', lighting: 'resolve' },
  { id: 'conf-62', type: 'confidence', startMs: 147300, value: 62 },
  { id: 'dlg-legal-build', type: 'dialogue', startMs: 147100, endMs: 163075, speaker: 'legal', text: 'Gate one disappears with private deployment. No patient data leaves the enterprise. For denials, route the nine percent to named-clinician sign-off. That is not a workaround. That is the compliant product design.' },
  { id: 'blk-cloud-resolve', type: 'blocker', startMs: 149500, blockerId: 'blk_public_cloud', action: 'resolve', status: 'resolved' },
  { id: 'blk-denial-resolve', type: 'blocker', startMs: 154000, blockerId: 'blk_human_denial', action: 'resolve', status: 'resolved' },
  { id: 'conf-81', type: 'confidence', startMs: 163500, value: 81 },
  { id: 'dlg-cfo-build', type: 'dialogue', startMs: 163400, endMs: 179561, speaker: 'cfo', text: 'Phase one can fit beneath the March spending cap. Seven point four million dollars. Thursday is not a request for an undefined transformation budget. It is a governed launch plan with precedent attached.' },
  { id: 'ev-phase', type: 'evidence', startMs: 163800, endMs: 190000, evidenceId: 'phase_budget', action: 'show' },
  { id: 'blk-budget-resolve', type: 'blocker', startMs: 167000, blockerId: 'blk_budget_cap', action: 'resolve', status: 'resolved' },
  { id: 'conf-91', type: 'confidence', startMs: 180000, value: 91 },

  // ── THE PATTERN: six years of board minutes ──────────────────────────────
  { id: 'sfx-pattern', type: 'sound', startMs: 179900, soundId: 'pattern-detect' },
  { id: 'focus-evidence', type: 'visual-focus', startMs: 179900, target: 'evidence' },
  { id: 'dlg-buzz-pattern', type: 'dialogue', startMs: 179900, endMs: 190070, speaker: 'buzz', text: 'New institutional pattern detected. Reviewing six years of board minutes... Directors rejected every new initiative above eleven million dollars... except one.' },
  { id: 'ev-board', type: 'evidence', startMs: 180300, endMs: 208000, evidenceId: 'board_pattern', action: 'show' },
  { id: 'dlg-buzz-cyber', type: 'dialogue', startMs: 190400, endMs: 207676, speaker: 'buzz', text: 'Cybersecurity. Approval occurred because regulatory exposure was quantified before financial upside. Recommended board sequence: Risk. Governance. Human control. Then revenue. Estimated board approval confidence increases from sixty-two to ninety-one percent.' },
  { id: 'conf-91b', type: 'confidence', startMs: 206000, value: 91 },
  { id: 'blk-securities-mit', type: 'blocker', startMs: 205500, blockerId: 'blk_securities', action: 'resolve', status: 'mitigated' },

  // ── THE ARTIFACT: board package complete ─────────────────────────────────
  { id: 'music-silence-2', type: 'music', startMs: 207700, bed: 'silence' },
  { id: 'sc-upright', type: 'scene', startMs: 207800, scene: 'kitchen-resolved', ceoPose: 'upright', lighting: 'resolve' },
  { id: 'focus-deck', type: 'visual-focus', startMs: 207800, target: 'board-deck' },
  { id: 'sfx-board', type: 'sound', startMs: 208100, soundId: 'board-complete' },
  { id: 'dlg-buzz-package', type: 'dialogue', startMs: 208100, endMs: 227001, speaker: 'buzz', text: 'Board package complete. Slide fourteen updated. Financial appendix regenerated. Legal citations attached. Dissent preserved. Three anticipated board objections identified. Recommended responses prepared. Speaking notes generated. Consensus confidence: ninety-four percent.' },
  { id: 'conf-94', type: 'confidence', startMs: 208500, value: 94 },
  { id: 'art-1', type: 'artifact', startMs: 208900, artifactId: 'art_slide14', action: 'ready', title: 'Slide 14 updated' },
  { id: 'art-2', type: 'artifact', startMs: 210100, artifactId: 'art_financial', action: 'ready', title: 'Financial appendix regenerated' },
  { id: 'art-3', type: 'artifact', startMs: 211300, artifactId: 'art_legal', action: 'ready', title: 'Legal citations attached' },
  { id: 'art-4', type: 'artifact', startMs: 212500, artifactId: 'art_dissent', action: 'ready', title: 'Dissent preserved' },
  { id: 'art-5', type: 'artifact', startMs: 213700, artifactId: 'art_objections', action: 'ready', title: 'Three anticipated objections' },
  { id: 'art-6', type: 'artifact', startMs: 214900, artifactId: 'art_notes', action: 'ready', title: 'Speaking notes generated' },
  { id: 'art-7', type: 'artifact', startMs: 216100, artifactId: 'art_memo', action: 'ready', title: 'Board memo ready' },
  { id: 'dlg-ceo-sleep', type: 'dialogue', startMs: 227400, endMs: 230279, speaker: 'ceo', text: 'I can actually sleep tonight. Thank you.' },
  { id: 'sc-relieved', type: 'scene', startMs: 227400, scene: 'kitchen-resolved', ceoPose: 'relieved', lighting: 'resolve' },
  { id: 'dlg-buzz-close', type: 'dialogue', startMs: 230700, endMs: 238734, speaker: 'buzz', text: 'Executive Huddle ended. Duration: eight minutes, forty-two seconds. Equivalent scheduling delay avoided: nineteen days.' },
  { id: 'sfx-close', type: 'sound', startMs: 239200, soundId: 'huddle-close' },
  { id: 'room-complete', type: 'room-transition', startMs: 239200, room: 'complete', label: 'COMPLETE' },
  { id: 'music-lift', type: 'music', startMs: 239400, bed: 'lift', volume: 0.03 },

  // ── END CARDS ────────────────────────────────────────────────────────────
  { id: 'sc-end', type: 'scene', startMs: 239600, scene: 'end-card', ceoPose: 'relieved', lighting: 'resolve' },
  { id: 'focus-end', type: 'visual-focus', startMs: 239600, target: 'end-card' },
  { id: 'end-1', type: 'end-card', startMs: 240000, endMs: 246000, stage: 1, lines: ['The first generation of enterprise AI helped people find information.'] },
  { id: 'end-2', type: 'end-card', startMs: 246000, endMs: 252000, stage: 2, lines: ['The first generation of enterprise AI helped people find information.', 'The second preserved individual knowledge.'] },
  { id: 'end-3', type: 'end-card', startMs: 252000, endMs: 258000, stage: 3, lines: ['The first generation of enterprise AI helped people find information.', 'The second preserved individual knowledge.', 'WisdomTwin preserves institutional judgment.'] },
  { id: 'end-4', type: 'end-card', startMs: 258000, endMs: 266000, stage: 4, lines: ['Search finds documents.', 'Digital twins preserve people.', 'WisdomTwin preserves decisions.'], showInvestorContrast: true },
  { id: 'end-5', type: 'end-card', startMs: 266000, stage: 5, lines: ['WISDOMTWIN.AI', 'The Institutional Judgment Layer', 'On-premise. Air-gapped. Human-governed.'], showInvestorContrast: true },
];

export const FULL_TIMELINE: TimelineConfig = {
  id: 'full',
  label: 'Full boardroom (4:34)',
  durationMs: 274_000,
  events: sortTimeline(events),
};
