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
      { label: 'Decisions reviewed', value: '12,400' },
      { label: 'Human judgment', value: '9%' },
      { label: 'Review estimate', value: '38 min' },
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
      { label: 'Senior officers', value: '5' },
      { label: 'Calendar delay', value: '3 weeks' },
      { label: 'Activation', value: '1 press' },
    ],
    startMs: 45_200,
    endMs: 94_600,
  },
  {
    id: 'constraints',
    eyebrow: '03 · Enterprise constraints',
    headline: 'Policy and dissent enter the decision—not a prompt.',
    detail: 'The huddle preserves the board cap, the vote, the dissent, and the legal gates as governing inputs.',
    metrics: [
      { label: 'Board cap', value: '$11M' },
      { label: 'Recorded vote', value: '7–2' },
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
      { label: 'Phase one', value: '$7.4M' },
      { label: 'Confidence', value: '62→91%' },
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
      { label: 'Ready artifacts', value: '7' },
      { label: 'Consensus', value: '94%' },
      { label: 'Audit trail', value: 'Complete' },
    ],
    startMs: 196_000,
    endMs: 224_200,
  },
  {
    id: 'economics',
    eyebrow: '06 · Decision economics',
    headline: 'WisdomTwin sells execution speed.',
    detail: 'An illustrative nineteen-day executive delay compresses into one governed huddle—with judgment intact.',
    metrics: [
      { label: 'Delay avoided', value: '19 days' },
      { label: 'Huddle', value: '8:42' },
      { label: 'Execution value', value: '≈$400K' },
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
