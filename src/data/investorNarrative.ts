export interface InvestorChapter {
  id: string;
  eyebrow: string;
  headline: string;
  detail: string;
  metrics: Array<{ label: string; value: string }>;
  startMs: number;
  endMs: number;
}

export const INVESTOR_CHAPTERS: InvestorChapter[] = [
  {
    id: 'guardrail',
    eyebrow: '01 · Governed AI',
    headline: 'The moat is knowing when not to answer.',
    detail: 'WisdomTwin withholds low-confidence judgment and routes the exception to a named human.',
    metrics: [
      { label: 'Evidence', value: 'Linked' },
      { label: 'Low confidence', value: 'Declined' },
      { label: 'Human review', value: 'Named' },
    ],
    startMs: 0,
    endMs: 45_200,
  },
  {
    id: 'coordination',
    eyebrow: '02 · Coordination tax',
    headline: 'Three weeks of calendars become one button.',
    detail: 'Five role-specific Wisdom Twins convene with the policy, precedent, and context already attached.',
    metrics: [
      { label: 'Roles', value: 'Convened' },
      { label: 'Context', value: 'Attached' },
      { label: 'Activation', value: 'One press' },
    ],
    startMs: 45_200,
    endMs: 94_600,
  },
  {
    id: 'constraints',
    eyebrow: '03 · Enterprise constraints',
    headline: 'Policy and dissent enter the decision, not a prompt.',
    detail: 'The huddle preserves the board cap, the vote, the dissent, and the legal gates as governing inputs.',
    metrics: [
      { label: 'Policy', value: 'Applied' },
      { label: 'Decision history', value: 'Preserved' },
      { label: 'Dissent', value: 'Preserved' },
    ],
    startMs: 94_600,
    endMs: 135_200,
  },
  {
    id: 'engine',
    eyebrow: '04 · Decision engine',
    headline: 'Precedent turns constraints into a shippable plan.',
    detail: 'Private deployment, named-human control, and a phased budget resolve the blockers without erasing them.',
    metrics: [
      { label: 'Plan', value: 'Phased' },
      { label: 'Constraints', value: 'Resolved' },
      { label: 'Deployment', value: 'Private' },
    ],
    startMs: 135_200,
    endMs: 196_000,
  },
  {
    id: 'output',
    eyebrow: '05 · Board-ready output',
    headline: 'The meeting ends with artifacts, not a transcript.',
    detail: 'The board package, citations, objections, speaking notes, and audit record are generated in the flow of work.',
    metrics: [
      { label: 'Artifacts', value: 'Ready' },
      { label: 'Objections', value: 'Prepared' },
      { label: 'Audit trail', value: 'Complete' },
    ],
    startMs: 196_000,
    endMs: 224_200,
  },
  {
    id: 'economics',
    eyebrow: '06 · Decision economics',
    headline: 'WisdomTwin sells execution speed.',
    detail: 'An illustrative executive delay compresses into one governed huddle with judgment intact.',
    metrics: [
      { label: 'Delay', value: 'Compressed' },
      { label: 'Decision', value: 'Governed' },
      { label: 'Judgment', value: 'Preserved' },
    ],
    startMs: 224_200,
    endMs: 240_001,
  },
];

export function getInvestorChapter(timeMs: number): InvestorChapter {
  return (
    INVESTOR_CHAPTERS.find((chapter) => timeMs >= chapter.startMs && timeMs < chapter.endMs) ??
    INVESTOR_CHAPTERS[INVESTOR_CHAPTERS.length - 1]
  );
}
