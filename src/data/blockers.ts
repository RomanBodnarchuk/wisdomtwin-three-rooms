import type { BlockerItem, EscalationItem, BoardArtifact } from '../types/timeline';

export const INITIAL_BLOCKERS: BlockerItem[] = [
  {
    id: 'blk_public_cloud',
    title: 'Public cloud PHI restriction',
    category: 'legal',
    policy: 'Patient data cannot touch a public cloud model',
    precedent: 'Governance memos + external model rejection rationale (prior year)',
    owner: 'Chief Legal Officer Twin',
    decision: 'Private deployment only',
    status: 'open',
  },
  {
    id: 'blk_budget_cap',
    title: 'New-program spending cap',
    category: 'financial',
    policy: 'Board-capped new programs at $11M this fiscal year',
    precedent: 'March motion, vote 7–2, dissent preserved',
    owner: 'CFO Twin',
    decision: 'Phase one at $7.4M under cap',
    status: 'open',
  },
  {
    id: 'blk_scale_precedent',
    title: 'Peak-load throughput precedent',
    category: 'technical',
    policy: 'Confidence must meet governance threshold',
    precedent: 'No reliable peak-load precedent at proposed volume',
    owner: 'VP, Clinical Operations (human)',
    decision: 'Escalate; measure 90 days before expand',
    status: 'open',
  },
  {
    id: 'blk_human_denial',
    title: 'Named-human denial sign-off',
    category: 'regulatory',
    policy: 'Four state-records regimes require human sign-off on denials',
    precedent: 'State compliance requirements',
    owner: 'Chief Legal Officer Twin',
    decision: 'Route 9% clinical cases to named clinicians',
    status: 'open',
  },
  {
    id: 'blk_securities',
    title: 'Material revenue disclosure timing',
    category: 'legal',
    policy: 'Material revenue program triggers securities disclosure rules',
    precedent: 'Disclosure governance practice',
    owner: 'Chief Legal Officer Twin',
    decision: 'Announce correctly or not at all',
    status: 'open',
  },
];

export const INITIAL_ESCALATION: EscalationItem = {
  id: 'esc_vp_clinical',
  title: 'Peak-load throughput review',
  reason: 'Confidence below governance threshold — no sufficient precedent',
  reviewer: 'Vice President of Clinical Operations',
  estimatedMinutes: 38,
  status: 'pending-human',
  auditRecorded: true,
};

export const BOARD_ARTIFACTS: BoardArtifact[] = [
  { id: 'art_slide14', title: 'Slide 14 updated', detail: 'Board sequence reframed: risk, governance, human control, then revenue', status: 'pending' },
  { id: 'art_financial', title: 'Financial appendix regenerated', detail: 'Phase-one $7.4M plan under March spending cap', status: 'pending' },
  { id: 'art_legal', title: 'Legal citations attached', detail: 'Public-cloud prohibition + four-market human denial requirements', status: 'pending' },
  { id: 'art_dissent', title: 'Dissent preserved', detail: 'March 7–2 dissent notes retained in board package', status: 'pending' },
  { id: 'art_objections', title: 'Three anticipated objections', detail: 'Prepared responses for board Q&A', status: 'pending' },
  { id: 'art_notes', title: 'Speaking notes generated', detail: 'CEO talking points sequenced for Thursday session', status: 'pending' },
  { id: 'art_memo', title: 'Board memo ready', detail: 'Governed launch plan with precedent attached', status: 'pending' },
];

export const COMPLETION_SUMMARY = {
  durationLabel: '8:42',
  blockersResolved: '4 of 5',
  humanEscalation: 1,
  boardMemo: 'Ready',
  citations: 'Attached',
  dissent: 'Preserved',
  auditRecord: 'Complete',
  schedulingDelayAvoided: '19 days',
} as const;
