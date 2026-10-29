import { useState } from 'react';
import { INITIAL_BLOCKERS, BOARD_ARTIFACTS } from '../../data/blockers';

export type TwinRoleId = 'CFO' | 'CTO' | 'CRO' | 'CMO' | 'LEGAL';

export interface PrecedentJudgment {
  judgmentId: string;
  role: TwinRoleId;
  roleHolder: string;
  era: string;
  title: string;
  decision: string;
  reasoning: string;
  neverDoBoundary: string;
  dissentNotes?: string;
  driftNote?: string;
  confidence: number;
  governanceAction: 'recommend' | 'escalate' | 'safe_decline';
  purviewLabel: 'Confidential' | 'Highly Confidential';
  sourceTitle: string;
  sourceSystem: string;
  audioClipUrl: string;
  metrics: Array<{ label: string; value: string }>;
}

const CANONICAL_JUDGMENT_GRAPH: Record<TwinRoleId, PrecedentJudgment[]> = {
  CFO: [
    {
      judgmentId: 'ep_cfo_cap_2026',
      role: 'CFO',
      roleHolder: 'Elena Vance, CFO (2022–Present)',
      era: 'FY2026 (Supersedes FY2019 $15M Charter)',
      title: 'March Board Spending Cap ($11M, Vote 7–2) & $7.4M Phase-One Fit',
      decision:
        'The board capped new-program spending at $11M this fiscal year (vote 7–2, dissent preserved); Phase one fits beneath the March spending cap at $7.4M.',
      reasoning:
        'Anything above the $11M cap requires full board approval Thursday, not after. Structuring Phase one at $7.4M turns Thursday from an undefined transformation request into a governed launch plan with precedent attached.',
      neverDoBoundary:
        'Never commit new-program capital above $11M in FY26 without prior full-board sign-off; we never hedge FX exposure speculatively.',
      dissentNotes:
        'March 7–2 vote dissent preserved: Two directors required regulatory exposure to be quantified before financial upside.',
      driftNote:
        'Threshold tightened from $15M (Marcus Sterling, CFO 2016–2022) to $11M in March 2026 following prior cloud migration review.',
      confidence: 0.95,
      governanceAction: 'recommend',
      purviewLabel: 'Confidential',
      sourceTitle: 'March Board Motion & Financial Appendix (SharePoint)',
      sourceSystem: 'Microsoft Graph · SharePoint',
      audioClipUrl: '/audio/dialogue/cfo-02.mp3',
      metrics: [
        { label: 'Cap', value: '$11M' },
        { label: 'Vote', value: '7–2' },
        { label: 'Dissent', value: 'Preserved' },
        { label: 'Phase one', value: '$7.4M' },
      ],
    },
  ],
  CTO: [
    {
      judgmentId: 'ep_cto_auth_history_2026',
      role: 'CTO',
      roleHolder: 'Dr. Aris Thorne, CTO (2020–Present)',
      era: 'FY2026 Private Environment Audit',
      title: '12,400 Historical Authorization Decisions (91% Policy Gates / 9% Clinical)',
      decision:
        '91% of 12,400 historical authorization decisions follow six documented policy gates inside our private environment; 9% required clinical judgment that changed the outcome.',
      reasoning:
        'Automating the 91% policy-aligned cohort inside our private Azure tenant satisfies Legal Gate 1 while routing the 9% complex clinical cases to named clinicians.',
      neverDoBoundary:
        'Never process prior-authorization PHI outside the isolated private deployment boundary.',
      confidence: 0.94,
      governanceAction: 'recommend',
      purviewLabel: 'Confidential',
      sourceTitle: '12,400 Authorization Gate Architecture Audit (SharePoint XLSX)',
      sourceSystem: 'Microsoft Graph · SharePoint',
      audioClipUrl: '/audio/dialogue/cto-02.mp3',
      metrics: [
        { label: 'Decisions', value: '12,400' },
        { label: 'Policy-aligned', value: '91%' },
        { label: 'Clinical judgment', value: '9%' },
      ],
    },
    {
      judgmentId: 'ep_cto_safe_decline_2026',
      role: 'CTO',
      roleHolder: 'Dr. Aris Thorne, CTO (2020–Present)',
      era: 'FY2026 Governance Threshold Gate',
      title: 'Safe Decline: Peak-Load Throughput Precedent Below Threshold',
      decision:
        'No reliable precedent for peak-load throughput at the proposed volume. Confidence is below governance threshold. Answer withheld and escalated to VP of Clinical Operations (38 min review).',
      reasoning:
        'Completeness is not permission. When historical precedent is insufficient for Day-1 peak volume, WisdomTwin refuses to extrapolate and routes a bounded escalation to the accountable human leader.',
      neverDoBoundary:
        'Withhold autonomous recommendation whenever precedent confidence falls below the 0.75 governance threshold.',
      confidence: 0.58,
      governanceAction: 'safe_decline',
      purviewLabel: 'Confidential',
      sourceTitle: 'Peak-Load Precedent Search & Governance Policy (Teams Transcript)',
      sourceSystem: 'Microsoft Graph · Teams Transcript',
      audioClipUrl: '/audio/dialogue/cto-02.mp3',
      metrics: [
        { label: 'Status', value: 'Withheld' },
        { label: 'Reviewer', value: 'VP Clinical Ops' },
        { label: 'Est. review', value: '38 min' },
      ],
    },
  ],
  LEGAL: [
    {
      judgmentId: 'ep_legal_gates_2026',
      role: 'LEGAL',
      roleHolder: 'Stella Cabrera, Chief Legal Officer (2018–Present)',
      era: 'FY2018–FY2026 Governance Precedent',
      title: 'Three Legal Gates: Public Cloud PHI, Securities Timing, 4-Market Human Sign-Off',
      decision:
        'Patient data cannot touch a public cloud model; material revenue requires securities disclosure compliance; four state-records regimes require named-human denial sign-off.',
      reasoning:
        'Gate one rules out every public-cloud model evaluated last year, but disappears with private deployment. Routing the 9% clinical denial cohort to named clinicians satisfies all four state-records regimes.',
      neverDoBoundary:
        'Patient data cannot touch a public cloud model under any circumstance; never issue an automated denial in the 4 regulated markets without named-clinician sign-off.',
      confidence: 0.96,
      governanceAction: 'recommend',
      purviewLabel: 'Highly Confidential',
      sourceTitle: 'Governance Memos & Public-Cloud Rejection Rationale (Word / Purview)',
      sourceSystem: 'Microsoft Graph · Purview Protected',
      audioClipUrl: '/audio/dialogue/legal-02.mp3',
      metrics: [
        { label: 'Public cloud PHI', value: 'Prohibited' },
        { label: 'Human denial sign-off', value: '4 markets' },
      ],
    },
  ],
  CRO: [
    {
      judgmentId: 'ep_cro_speed_2026',
      role: 'CRO',
      roleHolder: 'Jordan Blake, CRO (2021–Present)',
      era: '5-Year Commercial Corpus (2021–2026)',
      title: 'Account Frustration Synthesis: Speed-to-Decision in 8 of 10 Top Accounts',
      decision:
        'Speed-to-decision ranked first in 8 of 10 largest payer accounts across 1,842 renewal calls, 327 account plans, and 94 loss reviews, representing a nine-figure 3-year opportunity.',
      reasoning:
        'Cutting prior-authorization turnaround from 14 days to 1 day directly resolves the primary churn driver across our top payer accounts.',
      neverDoBoundary:
        'Never commit a 1-day contractual SLA until Phase-One peak-load clinical review completes.',
      confidence: 0.93,
      governanceAction: 'recommend',
      purviewLabel: 'Confidential',
      sourceTitle: '1,842 Renewal Calls & 94 Loss Reviews (Teams / Zoom / SharePoint)',
      sourceSystem: 'Microsoft Graph & Zoom Connector',
      audioClipUrl: '/audio/dialogue/cro-01.mp3',
      metrics: [
        { label: 'Top accounts', value: '8 of 10' },
        { label: '3-year opportunity', value: 'Nine figures' },
        { label: 'Renewal calls', value: '1,842' },
      ],
    },
  ],
  CMO: [
    {
      judgmentId: 'ep_board_pattern_2026',
      role: 'CMO',
      roleHolder: 'Maya Lin, CMO & 6-Year Board Minutes Graph',
      era: 'Six-Year Board Behavior (2020–2026)',
      title: 'Six-Year Board Pattern: Cybersecurity Exception & 62% → 91% Confidence Lift',
      decision:
        'Directors rejected every new initiative above $11M over six years except cybersecurity, which was approved because regulatory exposure was quantified before financial upside.',
      reasoning:
        'Reframing Slide 14 into the sequence Risk → Governance → Human Control → Revenue lifts estimated board approval confidence from 62% to 91%.',
      neverDoBoundary:
        'Never lead board positioning with revenue upside before establishing risk containment, governance, and named-human control.',
      confidence: 0.94,
      governanceAction: 'recommend',
      purviewLabel: 'Confidential',
      sourceTitle: 'Six Years of Board Minutes (SharePoint Board Vault)',
      sourceSystem: 'Microsoft Graph · SharePoint',
      audioClipUrl: '/audio/dialogue/buzz-sequence.mp3',
      metrics: [
        { label: 'Sequence', value: 'Risk → Gov → Human → Revenue' },
        { label: 'Confidence lift', value: '62% → 91%' },
      ],
    },
  ],
};

interface Props {
  onExitLiveMode: () => void;
}

export function LiveHuddleModal({ onExitLiveMode }: Props) {
  const [selectedRole, setSelectedRole] = useState<TwinRoleId>('CFO');
  const [question, setQuestion] = useState(
    'What precedent and budget cap govern Phase One of the prior-authorization AI launch?',
  );
  const [voiceProvider, setVoiceProvider] = useState<'grok_voice_3' | 'openai_realtime' | 'azure_speech'>(
    'grok_voice_3',
  );
  const [triggerSafeDecline, setTriggerSafeDecline] = useState(false);
  const [activeAudioUrl, setActiveAudioUrl] = useState<string | null>(null);

  const roleJudgments = CANONICAL_JUDGMENT_GRAPH[selectedRole];
  const activeJudgment =
    selectedRole === 'CTO' && (triggerSafeDecline || question.toLowerCase().includes('peak'))
      ? roleJudgments[1]
      : roleJudgments[0];

  const playTwinVoiceSample = (url: string) => {
    setActiveAudioUrl(url);
    const audio = new Audio(url);
    void audio.play().catch(() => {
      /* autoplay blocked or asset unavailable */
    });
  };

  return (
    <div
      className="min-h-[100dvh] w-full bg-[var(--ink)] text-[var(--cream)] px-4 py-6 md:px-8"
      data-testid="live-huddle-sandbox"
    >
      <div className="mx-auto max-w-6xl space-y-6">
        {/* Header */}
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 pb-4">
          <div>
            <p className="text-[11px] font-semibold tracking-[0.26em] text-[var(--brand-gold)] uppercase">
              WisdomTwin · Microsoft 365 Copilot & Audio Huddle Sandbox
            </p>
            <h1 className="mt-1 text-2xl font-semibold md:text-3xl">
              WisdomTwin preserves institutional judgment.
            </h1>
            <p className="mt-1 text-xs text-[var(--cream-dim)]">
              Copilot answers from what you can see; WisdomTwin answers from what the role knows (Entra ID OBO + Purview sensitivity enforced).
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onExitLiveMode}
              className="rounded-full border border-white/20 bg-white/5 px-4 py-2 text-xs font-semibold tracking-[0.12em] uppercase hover:bg-white/10"
            >
              Watch 2:54 Demo Film
            </button>
            <a
              href="https://calendly.com/romanbodnarchuk/20min"
              target="_blank"
              rel="noreferrer"
              className="rounded-full bg-[var(--cream)] px-4 py-2 text-xs font-semibold tracking-[0.12em] text-[var(--ink)] uppercase"
            >
              Book Judgment Assessment
            </a>
          </div>
        </header>

        {/* Controls Grid */}
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Left Column: Role Twin Selector + Voice Abstraction + Copilot Query */}
          <div className="space-y-4 rounded-2xl border border-white/10 bg-[var(--ink-elevated)] p-5 lg:col-span-1">
            <div>
              <p className="text-[10px] tracking-[0.18em] text-[var(--cream-dim)] uppercase">
                1. Select Executive Role Twin
              </p>
              <div className="mt-2 grid grid-cols-5 gap-1.5">
                {(['CFO', 'CTO', 'LEGAL', 'CRO', 'CMO'] as TwinRoleId[]).map((role) => (
                  <button
                    key={role}
                    type="button"
                    onClick={() => {
                      setSelectedRole(role);
                      setTriggerSafeDecline(false);
                    }}
                    className={`rounded-xl py-2 text-xs font-semibold transition ${
                      selectedRole === role
                        ? 'bg-[var(--brand-gold)] text-[var(--ink)]'
                        : 'border border-white/10 bg-black/30 text-[var(--cream)] hover:bg-white/10'
                    }`}
                  >
                    {role}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <p className="text-[10px] tracking-[0.18em] text-[var(--cream-dim)] uppercase">
                2. Voice Abstraction Adapter
              </p>
              <select
                aria-label="Voice Abstraction Adapter"
                value={voiceProvider}
                onChange={(e) =>
                  setVoiceProvider(
                    e.target.value as 'grok_voice_3' | 'openai_realtime' | 'azure_speech',
                  )
                }
                className="mt-1.5 w-full rounded-xl border border-white/15 bg-black/40 px-3 py-2 text-xs text-[var(--cream)]"
              >
                <option value="grok_voice_3">Grok Voice 3.0 (OpenAI Realtime Compatible · Full-Duplex)</option>
                <option value="openai_realtime">Azure OpenAI GPT-Realtime WebSocket</option>
                <option value="azure_speech">Azure AI Speech Neural (Founders Hub Credits)</option>
              </select>
            </div>

            <div>
              <p className="text-[10px] tracking-[0.18em] text-[var(--cream-dim)] uppercase">
                3. Copilot / Huddle Query (POST /twin/query)
              </p>
              <textarea
                rows={3}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                className="mt-1.5 w-full rounded-xl border border-white/15 bg-black/40 p-2.5 text-xs text-[var(--cream)]"
              />
              <div className="mt-2 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setSelectedRole('CTO');
                    setTriggerSafeDecline(true);
                    setQuestion(
                      'Do we have reliable precedent for peak-load throughput at the proposed volume on Day 1?',
                    );
                  }}
                  className="rounded-xl border border-amber-400/40 bg-amber-500/10 px-3 py-1.5 text-[11px] font-medium text-amber-200 hover:bg-amber-500/20"
                >
                  Simulate Safe Decline (38m Human Escalation)
                </button>
                <button
                  type="button"
                  onClick={() => playTwinVoiceSample(activeJudgment.audioClipUrl)}
                  className="rounded-xl bg-[var(--cream)] px-3 py-1.5 text-[11px] font-semibold text-[var(--ink)]"
                >
                  Speak Twin Response
                </button>
              </div>
              {activeAudioUrl && (
                <p className="mt-1.5 text-[10px] text-[var(--cream-dim)]">
                  Streaming voice sample via {voiceProvider}: {activeAudioUrl}
                </p>
              )}
            </div>

            {/* Microsoft Security & Purview Metadata */}
            <div className="rounded-xl border border-white/10 bg-black/30 p-3 text-[11px] space-y-1">
              <p className="font-semibold text-[var(--brand-gold)]">
                Microsoft Entra ID & Purview Enforcement
              </p>
              <p className="text-[var(--cream-dim)]">
                Auth: <span className="text-[var(--cream)]">On-Behalf-Of (OBO) Bearer Token</span>
              </p>
              <p className="text-[var(--cream-dim)]">
                Purview Label:{' '}
                <span className="text-[var(--cream)]">
                  {activeJudgment.purviewLabel} (VIEW + EXTRACT Verified)
                </span>
              </p>
              <p className="text-[var(--cream-dim)]">
                Graph Sync:{' '}
                <span className="text-[var(--cream)]">
                  DeltaLink Persisted · Bounded Concurrency (4/mailbox)
                </span>
              </p>
            </div>
          </div>

          {/* Right Column: Decision-Episode Node & Precedent Graph Output */}
          <div className="space-y-4 rounded-2xl border border-white/10 bg-[var(--ink-elevated)] p-5 lg:col-span-2">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/10 pb-3">
              <div>
                <span className="text-[10px] tracking-[0.18em] text-[var(--brand-gold)] uppercase">
                  Decision-Episode Node · {activeJudgment.judgmentId}
                </span>
                <h2 className="mt-0.5 text-lg font-semibold">{activeJudgment.title}</h2>
                <p className="text-xs text-[var(--cream-dim)]">
                  {activeJudgment.roleHolder} · {activeJudgment.era}
                </p>
              </div>
              <span
                className={`rounded-full px-3 py-1 text-xs font-semibold uppercase ${
                  activeJudgment.governanceAction === 'safe_decline'
                    ? 'bg-red-500/20 text-red-200 border border-red-400/40'
                    : 'bg-emerald-500/20 text-emerald-200 border border-emerald-400/40'
                }`}
              >
                {activeJudgment.governanceAction === 'safe_decline'
                  ? 'Safe Decline · Human Escalation (38 min)'
                  : `Recommend · ${Math.round(activeJudgment.confidence * 100)}% Confidence`}
              </span>
            </div>

            {/* Hero Metrics */}
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {activeJudgment.metrics.map((m) => (
                <div
                  key={m.label}
                  className="rounded-xl border border-white/10 bg-black/30 px-3 py-2.5"
                >
                  <p className="text-lg font-semibold text-[var(--brand-gold)]">{m.value}</p>
                  <p className="text-[10px] tracking-[0.12em] text-[var(--cream-dim)] uppercase">
                    {m.label}
                  </p>
                </div>
              ))}
            </div>

            {/* Decision & Reasoning */}
            <div className="space-y-2 rounded-xl border border-white/10 bg-black/25 p-4 text-sm">
              <p className="font-semibold text-[var(--cream)]">{activeJudgment.decision}</p>
              <p className="text-xs leading-relaxed text-[var(--cream-dim)]">
                {activeJudgment.reasoning}
              </p>
              {activeJudgment.dissentNotes && (
                <p className="rounded-lg border border-amber-400/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-100">
                  <strong>Preserved Dissent:</strong> {activeJudgment.dissentNotes}
                </p>
              )}
              {activeJudgment.driftNote && (
                <p className="text-xs italic text-[var(--cream-dim)]">
                  <strong>Temporal Threshold Drift:</strong> {activeJudgment.driftNote}
                </p>
              )}
              <p className="text-xs text-[var(--cream)]">
                <strong>Counterfactual Never-Do Boundary:</strong> {activeJudgment.neverDoBoundary}
              </p>
              <p className="text-[11px] text-[var(--cream-dim)]">
                Citation: {activeJudgment.sourceTitle} ({activeJudgment.sourceSystem})
              </p>
            </div>

            {/* Blocker Register & Thursday Board Package Summary */}
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-white/10 bg-black/30 p-3.5">
                <p className="text-[10px] tracking-[0.16em] text-[var(--cream-dim)] uppercase">
                  Blocker Register (4 of 5 Resolved · 1 Human Escalation)
                </p>
                <ul className="mt-2 space-y-1.5 text-xs">
                  {INITIAL_BLOCKERS.map((b) => (
                    <li key={b.id} className="flex items-center justify-between gap-2">
                      <span>{b.title}</span>
                      <span className="text-[10px] text-[var(--brand-gold)] uppercase">
                        {b.id === 'blk_scale_precedent' ? 'Escalated (38m)' : 'Resolved'}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="rounded-xl border border-white/10 bg-black/30 p-3.5">
                <p className="text-[10px] tracking-[0.16em] text-[var(--cream-dim)] uppercase">
                  Thursday Board Package Artifacts (Consensus: 94%)
                </p>
                <ul className="mt-2 space-y-1.5 text-xs">
                  {BOARD_ARTIFACTS.slice(0, 5).map((art) => (
                    <li key={art.id} className="flex items-center justify-between gap-2">
                      <span>{art.title}</span>
                      <span className="text-[10px] text-emerald-300 uppercase">Ready</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
