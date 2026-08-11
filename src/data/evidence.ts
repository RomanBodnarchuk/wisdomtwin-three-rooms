import type { EvidenceCard } from '../types/timeline';

export const EVIDENCE_CARDS: Record<string, EvidenceCard> = {
  cro_speed: {
    id: 'cro_speed',
    title: 'Account frustration analysis',
    role: 'cro',
    sources: ['1,842 renewal calls', '327 account plans', '94 loss reviews', 'Five-year period'],
    finding: 'Speed-to-decision ranked first in 8 of 10 largest accounts.',
    metrics: [
      { label: 'Top accounts', value: '8 of 10' },
      { label: '3-year opportunity', value: 'Nine figures' },
    ],
  },
  cfo_cap: {
    id: 'cfo_cap',
    title: 'Board spending cap',
    role: 'cfo',
    sources: ['March board motion', 'New-program spending vote', 'Dissent notes preserved'],
    finding: 'Board capped new-program spending at $11M this fiscal year. Vote 7–2.',
    metrics: [
      { label: 'Cap', value: '$11M' },
      { label: 'Vote', value: '7–2' },
      { label: 'Dissent', value: 'Preserved' },
    ],
  },
  cto_history: {
    id: 'cto_history',
    title: 'Historical authorization review',
    role: 'cto',
    sources: ['12,400 authorization decisions', 'Six documented policy gates', 'Private environment analysis'],
    finding: '91% follow six policy gates. 9% required clinical judgment that changed the outcome.',
    metrics: [
      { label: 'Policy-aligned', value: '91%' },
      { label: 'Clinical judgment', value: '9%' },
    ],
  },
  legal_gates: {
    id: 'legal_gates',
    title: 'Governance gates',
    role: 'legal',
    sources: ['Governance memos', 'Public-cloud rejection rationale', 'State-records regimes'],
    finding: 'Patient data cannot touch public cloud. Material revenue requires correct disclosure. Four markets require named-human denial sign-off.',
    metrics: [
      { label: 'Public cloud PHI', value: 'Prohibited' },
      { label: 'Human denial sign-off', value: '4 markets' },
    ],
  },
  safe_decline: {
    id: 'safe_decline',
    title: 'Confidence below governance threshold',
    role: 'cto',
    sources: ['Peak-load precedent search', 'Throughput history', 'Governance threshold policy'],
    finding: 'No reliable precedent for peak-load throughput at the proposed volume. Answer withheld. Human escalation created.',
    metrics: [
      { label: 'Status', value: 'Withheld' },
      { label: 'Reviewer', value: 'VP Clinical Ops' },
      { label: 'Est. review', value: '38 min' },
    ],
  },
  board_pattern: {
    id: 'board_pattern',
    title: 'Six-year board behavior',
    role: 'buzz',
    sources: ['Six years of board minutes', 'Initiatives above $11M', 'Cybersecurity approval exception'],
    finding: 'Directors rejected every new initiative above $11M except cybersecurity. It was approved because regulatory exposure was quantified before financial upside.',
    metrics: [
      { label: 'Sequence', value: 'Risk → Gov → Human → Revenue' },
      { label: 'Confidence lift', value: '62% → 91%' },
    ],
  },
  phase_budget: {
    id: 'phase_budget',
    title: 'Phase-one budget fit',
    role: 'cfo',
    sources: ['March spending cap', 'Phased launch model'],
    finding: 'Phase one can fit beneath the March spending cap at $7.4M.',
    metrics: [{ label: 'Phase one', value: '$7.4M' }],
  },
};

export const EVIDENCE_LIST = Object.values(EVIDENCE_CARDS);
