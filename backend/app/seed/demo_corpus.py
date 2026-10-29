"""Seeds the TemporalContextGraph with the canonical WisdomTwin Healthcare Enterprise dataset.

Preserves all non-negotiable numbers and governance beats from src/data/evidence.ts and src/data/blockers.ts:
- $11M board spending cap (March motion, vote 7-2, dissent preserved)
- $7.4M Phase-One governed launch plan beneath the March cap
- 12,400 historical authorization decisions (91% follow 6 policy gates, 9% clinical judgment)
- Safe decline on peak-load throughput (VP Clinical Operations, 38-minute human review)
- 3 legal gates: no patient data on public cloud, material revenue securities disclosure, 4-market human denial sign-off
- CRO account frustration analysis (1,842 renewal calls, 327 account plans, 94 loss reviews, 8 of 10 top accounts)
- 6-year board behavior pattern (Cybersecurity exception: Risk -> Governance -> Human control -> Revenue, 62% -> 91% confidence)
- Historical CFO precedent from 2019 showing threshold drift (why the board tightened the cap to $11M in 2026)
"""

from __future__ import annotations

from datetime import datetime

from ..extraction.deduplicator import HistoricalEntityResolver
from ..graph.context_graph import TemporalContextGraph
from ..schemas.decision_episode import (
    AclSnapshot,
    AuthorityRecord,
    ConstraintOrThreshold,
    DecisionEpisode,
    DecisionType,
    EdgeType,
    EvidenceQuote,
    GovernanceAction,
    RoleTag,
    SensitivityClassification,
    SensitivityLabel,
    SourceSystem,
    TemporalGraphEdge,
    TemporalValidity,
)


def seed_canonical_demo_graph(graph: TemporalContextGraph) -> TemporalContextGraph:
    resolver = HistoricalEntityResolver()
    cfo_current = resolver.resolve("elena.vance@enterprise.local", RoleTag.CFO)
    cfo_former = resolver.resolve("marcus.sterling@enterprise.local", RoleTag.CFO)
    cto_current = resolver.resolve("aris.thorne@enterprise.local", RoleTag.CTO)
    cro_current = resolver.resolve("jordan.blake@enterprise.local", RoleTag.CRO)
    cmo_current = resolver.resolve("maya.lin@enterprise.local", RoleTag.CMO)
    legal_current = resolver.resolve("stella.cabrera@enterprise.local", RoleTag.LEGAL)
    ceo_current = resolver.resolve("daniel.mercer@enterprise.local", RoleTag.CEO)

    default_acl = AclSnapshot(
        tenant_id="00000000-0000-0000-0000-000000000001",
        allowed_user_ids=[
            "daniel.mercer@enterprise.local",
            "elena.vance@enterprise.local",
            "aris.thorne@enterprise.local",
            "jordan.blake@enterprise.local",
            "maya.lin@enterprise.local",
            "stella.cabrera@enterprise.local",
        ],
        allowed_group_ids=["grp-exec-officers", "grp-board-packet-readers"],
        allowed_roles=[
            RoleTag.CEO,
            RoleTag.CFO,
            RoleTag.CTO,
            RoleTag.CRO,
            RoleTag.CMO,
            RoleTag.LEGAL,
            RoleTag.BOARD,
        ],
        sharepoint_site_id="sp-site-exec-board",
    )

    confidential_label = SensitivityLabel(
        label_id="purview-confidential-board",
        name=SensitivityClassification.CONFIDENTIAL,
        is_encrypted=False,
    )

    # 1. CFO: March Board Spending Cap ($11M, Vote 7-2, Dissent Preserved) + Phase-One $7.4M fit
    ep_cfo_cap = DecisionEpisode(
        episode_id="ep_cfo_cap_2026",
        role=RoleTag.CFO,
        role_holder=cfo_current,
        decision_type=DecisionType.BUDGET_CAP_OR_EXCEPTION,
        title="Board spending cap & Phase-One $7.4M allocation",
        question_asked="What is the spending threshold for launching the AI prior-authorization program without triggering an unbudgeted transformation vote?",
        decision_statement="The board capped new-program spending at $11M this fiscal year (vote 7–2, dissent preserved); Phase one fits beneath the March spending cap at $7.4M.",
        reasoning=(
            "The board capped new-program spending at eleven million dollars this fiscal year. "
            "That motion passed seven to two in March. I preserved the dissent notes. Anything above "
            "the cap requires board approval Thursday, not after. Phase one can fit beneath the March "
            "spending cap at seven point four million dollars so Thursday is a governed launch plan "
            "with precedent attached rather than an undefined transformation budget."
        ),
        evidence_considered=[
            EvidenceQuote(
                source_document_id="ms_graph_sharepoint:board-motion-2026-03",
                source_title="March Board Motion & New-Program Spending Vote",
                source_system=SourceSystem.MS_GRAPH_SHAREPOINT,
                deep_link_url="https://enterprise.sharepoint.com/sites/Board/Shared%20Documents/2026-03-Spending-Cap-Motion.pptx",
                verbatim_quote="Board capped new-program spending at $11M this fiscal year. Vote 7–2. Dissent notes preserved. Phase one fits beneath the March spending cap at $7.4M.",
                metrics={"Cap": "$11M", "Vote": "7–2", "Dissent": "Preserved", "Phase one": "$7.4M"},
            )
        ],
        constraints_and_thresholds=[
            ConstraintOrThreshold(
                constraint_id="con_cfo_11m_cap",
                category="financial",
                rule_statement="Never commit new-program capital above $11M in FY26 without prior full-board sign-off.",
                threshold_value="$11M",
                is_counterfactual_boundary=True,
            ),
            ConstraintOrThreshold(
                constraint_id="con_cfo_phase1_74m",
                category="financial",
                rule_statement="Structure Phase-One AI deployment within $7.4M envelope gated on 90-day clinical and financial milestones.",
                threshold_value="$7.4M",
                is_counterfactual_boundary=False,
            ),
        ],
        alternatives_rejected=[
            "$18.5M single-tranche enterprise-wide transformation request",
            "Deferring board budget review until Q3 post-launch",
        ],
        authority=AuthorityRecord(
            deciding_authority="Board of Directors & Elena Vance (CFO)",
            vote_tally="7–2",
            dissent_preserved=True,
            dissent_summary="Two directors dissented, requiring that any AI capital request quantify regulatory risk exposure before projecting revenue upside.",
        ),
        outcome="Phase-One budgeted at $7.4M beneath the $11M cap; financial appendix regenerated with 7–2 dissent preserved.",
        temporal_validity=TemporalValidity(
            decided_at=datetime(2026, 3, 18, 16, 0, 0),
            valid_from=datetime(2026, 3, 18, 16, 0, 0),
            era_label="FY2026",
            drift_annotation="Tightened from the 2019 $15M discretionary CFO threshold after the 2022 multi-year cloud migration overrun.",
        ),
        sensitivity_label=confidential_label,
        acl_snapshot=default_acl,
        confidence_score=0.95,
        field_confidence={"decision_statement": 0.97, "reasoning": 0.95, "authority": 0.98},
        governance_action=GovernanceAction.RECOMMEND,
        verified_by_human=True,
    )

    # 2. Historical CFO Precedent (2019) showing temporal drift across role holders
    ep_cfo_2019 = DecisionEpisode(
        episode_id="ep_cfo_cap_2019",
        role=RoleTag.CFO,
        role_holder=cfo_former,
        decision_type=DecisionType.BUDGET_CAP_OR_EXCEPTION,
        title="2019 Discretionary Program Cap ($15M) — Superseded in March 2026",
        question_asked="What was the historical CFO discretionary ceiling for new clinical IT programs prior to 2026?",
        decision_statement="Between 2019 and 2025, the CFO held authority to approve up to $15M for multi-year clinical modernization without a special board motion.",
        reasoning=(
            "Under former CFO Marcus Sterling, new clinical automation initiatives up to $15M were "
            "approved at the Executive Committee level, provided FX exposure was never hedged speculatively."
        ),
        evidence_considered=[
            EvidenceQuote(
                source_document_id="ms_graph_mail:cfo-charter-2019-11",
                source_title="2019 Audit & Finance Committee Charter Memo",
                source_system=SourceSystem.MS_GRAPH_MAIL,
                deep_link_url="https://outlook.office365.com/owa/?ItemID=cfo-charter-2019-11",
                verbatim_quote="Executive capital threshold set at $15M; we never hedge FX exposure outside board-approved treasury bounds.",
                metrics={"2019 Cap": "$15M", "Superseded By": "$11M (March 2026)"},
            )
        ],
        constraints_and_thresholds=[
            ConstraintOrThreshold(
                constraint_id="con_cfo_no_fx_hedge",
                category="financial",
                rule_statement="We never hedge currency exposure speculatively.",
                threshold_value="0% speculative FX",
                is_counterfactual_boundary=True,
            )
        ],
        alternatives_rejected=["Uncapped business-unit self-funding"],
        authority=AuthorityRecord(
            deciding_authority="Marcus Sterling (Former CFO, 2016–2022)",
            vote_tally="Unanimous Finance Committee",
            dissent_preserved=False,
        ),
        outcome="Superseded by the March 2026 7–2 Board motion lowering the cap to $11M.",
        temporal_validity=TemporalValidity(
            decided_at=datetime(2019, 11, 12, 10, 0, 0),
            valid_from=datetime(2019, 11, 12, 10, 0, 0),
            valid_until=datetime(2026, 3, 18, 16, 0, 0),
            era_label="FY2019-FY2025",
            drift_annotation="Superseded on 2026-03-18 when the Board lowered the cap from $15M to $11M (7–2 vote).",
        ),
        sensitivity_label=confidential_label,
        acl_snapshot=default_acl,
        confidence_score=0.92,
        governance_action=GovernanceAction.RECOMMEND,
        verified_by_human=True,
    )

    # 3. CTO: 12,400 Historical Authorization Decisions (91% / 9% Split)
    ep_cto_history = DecisionEpisode(
        episode_id="ep_cto_auth_history_2026",
        role=RoleTag.CTO,
        role_holder=cto_current,
        decision_type=DecisionType.ARCHITECTURE_OR_VENDOR,
        title="Historical authorization review: 12,400 decisions (91% policy gates / 9% clinical)",
        question_asked="Can prior-authorization decisions be automated inside our private environment without compromising clinical outcomes?",
        decision_statement="91% of 12,400 historical authorization decisions follow six documented policy gates in a private environment; the remaining 9% required clinical judgment that changed the outcome.",
        reasoning=(
            "I reviewed 12,400 historical authorization decisions. Ninety-one percent follow six "
            "documented policy gates and can be processed inside our private environment. The remaining "
            "nine percent are exactly where clinical judgment changed the outcome and must route to named clinicians."
        ),
        evidence_considered=[
            EvidenceQuote(
                source_document_id="ms_graph_sharepoint:cto-auth-audit-12400",
                source_title="12,400 Historical Authorization Architecture Audit",
                source_system=SourceSystem.MS_GRAPH_SHAREPOINT,
                deep_link_url="https://enterprise.sharepoint.com/sites/Architecture/Shared%20Documents/12400-Authorization-Gate-Audit.xlsx",
                verbatim_quote="91% follow six policy gates. 9% required clinical judgment that changed the outcome.",
                metrics={"Decisions analyzed": "12,400", "Policy-aligned": "91%", "Clinical judgment": "9%"},
            )
        ],
        constraints_and_thresholds=[
            ConstraintOrThreshold(
                constraint_id="con_cto_private_env",
                category="technical",
                rule_statement="Never process prior-authorization PHI outside the isolated private deployment boundary.",
                threshold_value="91% automated / 9% human clinical routing",
                is_counterfactual_boundary=True,
            )
        ],
        alternatives_rejected=["100% autonomous end-to-end denial automation", "External multi-tenant public LLM API"],
        authority=AuthorityRecord(
            deciding_authority="Dr. Aris Thorne (CTO)",
            dissent_preserved=False,
        ),
        outcome="Private environment architecture approved for the 91% policy-gate cohort; 9% clinical cohort routed to named clinicians.",
        temporal_validity=TemporalValidity(
            decided_at=datetime(2026, 8, 1, 9, 0, 0),
            valid_from=datetime(2026, 8, 1, 9, 0, 0),
            era_label="FY2026",
        ),
        sensitivity_label=confidential_label,
        acl_snapshot=default_acl,
        confidence_score=0.94,
        governance_action=GovernanceAction.RECOMMEND,
        verified_by_human=True,
    )

    # 4. CTO: Safe Decline on Peak-Load Throughput (The Moat)
    ep_cto_safe_decline = DecisionEpisode(
        episode_id="ep_cto_safe_decline_2026",
        role=RoleTag.CTO,
        role_holder=cto_current,
        decision_type=DecisionType.CLINICAL_OR_OPERATIONAL_ESCALATION,
        title="Confidence below governance threshold: Peak-load throughput safe decline",
        question_asked="Can our infrastructure guarantee one-day turnaround under peak-load payer volume across all regions on Day 1?",
        decision_statement="No reliable precedent for peak-load throughput at the proposed volume; answer withheld and escalated to the Vice President of Clinical Operations (38-minute review).",
        reasoning=(
            "One warning. I found no reliable precedent for peak-load throughput at the proposed volume. "
            "Confidence is below governance threshold. I am declining to answer. Recommended human reviewer: "
            "Vice President of Clinical Operations. Estimated review time: thirty-eight minutes."
        ),
        evidence_considered=[
            EvidenceQuote(
                source_document_id="ms_graph_teams_transcript:cto-peak-load-review",
                source_title="Peak-Load Precedent Search & Governance Threshold Policy",
                source_system=SourceSystem.MS_GRAPH_TEAMS_TRANSCRIPT,
                deep_link_url="https://teams.microsoft.com/l/meetup-join/peak-load-throughput-audit",
                verbatim_quote="No reliable precedent for peak-load throughput at the proposed volume. Answer withheld. Human escalation created.",
                metrics={"Status": "Withheld", "Reviewer": "VP Clinical Ops", "Est. review": "38 min"},
            )
        ],
        constraints_and_thresholds=[
            ConstraintOrThreshold(
                constraint_id="con_cto_gov_threshold",
                category="technical",
                rule_statement="Withhold autonomous recommendation whenever precedent confidence falls below the 0.75 governance threshold.",
                threshold_value="38 min human review",
                is_counterfactual_boundary=True,
            )
        ],
        alternatives_rejected=["Extrapolating synthetic benchmark numbers without live clinical ops validation"],
        authority=AuthorityRecord(
            deciding_authority="Governance Policy Gate (Escalated to Human)",
            named_human_reviewer="Vice President of Clinical Operations",
            estimated_review_minutes=38,
        ),
        outcome="Safe decline triggered; 90-day staged volume measurement assigned to VP of Clinical Operations.",
        temporal_validity=TemporalValidity(
            decided_at=datetime(2026, 8, 10, 21, 40, 0),
            valid_from=datetime(2026, 8, 10, 21, 40, 0),
            era_label="FY2026",
        ),
        sensitivity_label=confidential_label,
        acl_snapshot=default_acl,
        confidence_score=0.58,
        governance_action=GovernanceAction.SAFE_DECLINE,
        verified_by_human=False,
    )

    # 5. LEGAL: Three Governance Gates (Public Cloud Prohibition, Securities Disclosure, 4-Market Human Denial)
    ep_legal_gates = DecisionEpisode(
        episode_id="ep_legal_gates_2026",
        role=RoleTag.LEGAL,
        role_holder=legal_current,
        decision_type=DecisionType.POLICY_GATE,
        title="Three Legal & Regulatory Gates: Public Cloud PHI, Securities Timing, 4-Market Human Sign-Off",
        question_asked="What legal and regulatory gates govern deploying and announcing an AI prior-authorization offering?",
        decision_statement="Patient data cannot touch a public cloud model; material revenue requires securities disclosure compliance; four state-records regimes require named-human denial sign-off.",
        reasoning=(
            "Three gates. One: patient data cannot touch a public cloud model. That rules out every "
            "external model evaluated last year. I have the governance memos and the rejection rationale. "
            "Two: material revenue program triggers securities disclosure rules. Three: four state-records "
            "regimes require named-human sign-off on denials. Gate one disappears with private deployment, "
            "and routing the 9% clinical cases to named-clinician sign-off is the compliant product design."
        ),
        evidence_considered=[
            EvidenceQuote(
                source_document_id="ms_graph_sharepoint:legal-governance-gates-2026",
                source_title="Governance Memos & Public-Cloud Rejection Rationale",
                source_system=SourceSystem.MS_GRAPH_SHAREPOINT,
                deep_link_url="https://enterprise.sharepoint.com/sites/Legal/Shared%20Documents/Public-Cloud-PHI-Rejection-Memo.docx",
                verbatim_quote="Patient data cannot touch public cloud. Material revenue requires correct disclosure. Four markets require named-human denial sign-off.",
                metrics={"Public cloud PHI": "Prohibited", "Human denial sign-off": "4 markets"},
            )
        ],
        constraints_and_thresholds=[
            ConstraintOrThreshold(
                constraint_id="con_legal_no_public_cloud_phi",
                category="legal",
                rule_statement="Patient data cannot touch a public cloud model under any circumstance.",
                threshold_value="0 bytes public egress",
                is_counterfactual_boundary=True,
            ),
            ConstraintOrThreshold(
                constraint_id="con_legal_4_markets_human",
                category="regulatory",
                rule_statement="Never issue an automated clinical denial in the four regulated state-records markets without named-clinician sign-off.",
                threshold_value="4 markets",
                is_counterfactual_boundary=True,
            ),
        ],
        alternatives_rejected=[
            "BAA-wrapped public multi-tenant foundation model endpoint",
            "Post-hoc audit sampling instead of pre-release human denial sign-off",
        ],
        authority=AuthorityRecord(
            deciding_authority="Stella Cabrera (Chief Legal Officer)",
            dissent_preserved=False,
        ),
        outcome="Private deployment mandated; 9% clinical cases routed to named clinicians; securities disclosure sequenced with board packet.",
        temporal_validity=TemporalValidity(
            decided_at=datetime(2026, 7, 22, 14, 0, 0),
            valid_from=datetime(2026, 7, 22, 14, 0, 0),
            era_label="FY2026",
        ),
        sensitivity_label=SensitivityLabel(
            label_id="purview-legal-highly-confidential",
            name=SensitivityClassification.HIGHLY_CONFIDENTIAL,
            is_encrypted=True,
        ),
        acl_snapshot=default_acl,
        confidence_score=0.96,
        governance_action=GovernanceAction.RECOMMEND,
        verified_by_human=True,
    )

    # 6. CRO: Account Frustration & Commercial Demand Analysis
    ep_cro_speed = DecisionEpisode(
        episode_id="ep_cro_speed_2026",
        role=RoleTag.CRO,
        role_holder=cro_current,
        decision_type=DecisionType.COMMERCIAL_PRICING_OR_TERMS,
        title="Account frustration analysis: Speed-to-decision in 8 of 10 largest accounts",
        question_asked="What is the commercial demand and retention impact of cutting authorization turnaround from 14 days to 1 day?",
        decision_statement="Across 1,842 renewal calls, 327 account plans, and 94 loss reviews over five years, speed-to-decision ranked first in 8 of 10 largest payer accounts, representing a nine-figure 3-year opportunity.",
        reasoning=(
            "Reviewing five years of commercial evidence (1,842 renewal calls, 327 account plans, and "
            "94 loss reviews) proves that authorization turnaround latency is the #1 churn driver in "
            "8 of our 10 largest accounts. Positioning governed turnaround speed unlocks a nine-figure "
            "three-year expansion opportunity."
        ),
        evidence_considered=[
            EvidenceQuote(
                source_document_id="zoom:cro-renewal-loss-synthesis-5yr",
                source_title="5-Year Renewal Call & Loss Review Synthesis (1,842 Calls)",
                source_system=SourceSystem.ZOOM,
                deep_link_url="https://enterprise.sharepoint.com/sites/Revenue/Shared%20Documents/Renewal-Loss-Synthesis.pptx",
                verbatim_quote="Speed-to-decision ranked first in 8 of 10 largest accounts across 1,842 renewal calls, 327 account plans, and 94 loss reviews.",
                metrics={"Top accounts": "8 of 10", "3-year opportunity": "Nine figures", "Renewal calls": "1,842"},
            )
        ],
        constraints_and_thresholds=[
            ConstraintOrThreshold(
                constraint_id="con_cro_sla_commitment",
                category="commercial",
                rule_statement="Never sign a 1-day turnaround SLA in commercial contracts until Phase-One peak-load clinical review completes.",
                threshold_value="Phase-1 gated SLA",
                is_counterfactual_boundary=True,
            )
        ],
        alternatives_rejected=["Discounting core platform seats without addressing authorization latency"],
        authority=AuthorityRecord(
            deciding_authority="Jordan Blake (CRO)",
            dissent_preserved=False,
        ),
        outcome="Commercial rollout sequenced behind Phase-One private deployment for top 8 payer accounts.",
        temporal_validity=TemporalValidity(
            decided_at=datetime(2026, 7, 30, 11, 0, 0),
            valid_from=datetime(2026, 7, 30, 11, 0, 0),
            era_label="FY2026",
        ),
        sensitivity_label=confidential_label,
        acl_snapshot=default_acl,
        confidence_score=0.93,
        governance_action=GovernanceAction.RECOMMEND,
        verified_by_human=True,
    )

    # 7. CMO & BOARD: Six-Year Board Behavior Pattern (Risk -> Governance -> Human -> Revenue, 62% -> 91%)
    ep_board_pattern = DecisionEpisode(
        episode_id="ep_board_pattern_2026",
        role=RoleTag.CMO,
        role_holder=cmo_current,
        decision_type=DecisionType.BOARD_SEQUENCE_STRATEGY,
        title="Six-year board behavior pattern: Risk -> Governance -> Human Control -> Revenue (62% to 91%)",
        question_asked="How should the Thursday board presentation and market narrative be sequenced to win board approval?",
        decision_statement="Across six years of board minutes, directors rejected every new initiative above $11M except cybersecurity, which succeeded because regulatory exposure was quantified before financial upside (lifting approval confidence from 62% to 91%).",
        reasoning=(
            "Reviewing six years of board minutes shows directors rejected every new initiative above "
            "eleven million dollars except cybersecurity. Approval occurred because regulatory exposure "
            "was quantified before financial upside. Sequencing the narrative as Risk -> Governance -> "
            "Human control -> Revenue increases estimated board approval confidence from 62% to 91%."
        ),
        evidence_considered=[
            EvidenceQuote(
                source_document_id="ms_graph_sharepoint:board-minutes-6yr-pattern",
                source_title="Six-Year Board Minutes & Cybersecurity Exception Analysis",
                source_system=SourceSystem.MS_GRAPH_SHAREPOINT,
                deep_link_url="https://enterprise.sharepoint.com/sites/Board/Shared%20Documents/6Yr-Board-Minutes-Pattern.pdf",
                verbatim_quote="Directors rejected every new initiative above $11M except cybersecurity. It was approved because regulatory exposure was quantified before financial upside.",
                metrics={"Sequence": "Risk → Gov → Human → Revenue", "Confidence lift": "62% → 91%"},
            )
        ],
        constraints_and_thresholds=[
            ConstraintOrThreshold(
                constraint_id="con_cmo_no_unverified_claims",
                category="regulatory",
                rule_statement="Never lead board or payer positioning with autonomous AI speed before establishing private governance and named-human clinical control.",
                threshold_value="Risk -> Gov -> Human -> Revenue",
                is_counterfactual_boundary=True,
            )
        ],
        alternatives_rejected=["Leading Slide 1 with nine-figure revenue upside before addressing PHI and budget gates"],
        authority=AuthorityRecord(
            deciding_authority="Board of Directors Precedent & Maya Lin (CMO)",
            dissent_preserved=True,
            dissent_summary="March 7–2 dissent notes addressed directly by leading with regulatory risk containment.",
        ),
        outcome="Slide 14 updated to Risk -> Governance -> Human Control -> Revenue; consensus confidence reaches 94%.",
        temporal_validity=TemporalValidity(
            decided_at=datetime(2026, 8, 10, 21, 46, 0),
            valid_from=datetime(2020, 1, 1, 0, 0, 0),
            era_label="FY2020-FY2026",
        ),
        sensitivity_label=confidential_label,
        acl_snapshot=default_acl,
        confidence_score=0.94,
        governance_action=GovernanceAction.RECOMMEND,
        verified_by_human=True,
    )

    # 8. CEO: Executive Synthesis & Thursday Board Package Release
    ep_ceo_package = DecisionEpisode(
        episode_id="ep_ceo_board_package_2026",
        role=RoleTag.CEO,
        role_holder=ceo_current,
        decision_type=DecisionType.BOARD_SEQUENCE_STRATEGY,
        title="Thursday Board Package Lock: Governed $7.4M Phase-One Prior-Authorization Launch",
        question_asked="How do we unify CFO, CTO, CRO, CMO, and Legal constraints into Thursday's board packet?",
        decision_statement="Lock Thursday's board packet around a $7.4M private-cloud Phase-One rollout (91% policy-automated, 9% clinician-signed), escalating peak-load throughput to VP Clinical Ops (38 min) and sequencing Slide 14 as Risk -> Governance -> Human Control -> Revenue.",
        reasoning=(
            "Resolves 4 of 5 blockers with precedent attached, preserves the March 7–2 dissent notes, "
            "and routes the single low-confidence throughput question to a named human reviewer."
        ),
        evidence_considered=[
            EvidenceQuote(
                source_document_id="ms_graph_sharepoint:thursday-board-packet-vFinal",
                source_title="Thursday Board Memo & Slide 14 Package",
                source_system=SourceSystem.MS_GRAPH_SHAREPOINT,
                deep_link_url="https://enterprise.sharepoint.com/sites/Board/Shared%20Documents/Thursday-Board-Packet-Final.pptx",
                verbatim_quote="Board package complete. 4 of 5 blockers resolved, 1 named human escalation (38 min), consensus confidence 94%.",
                metrics={"Blockers resolved": "4 of 5", "Human escalation": "1 (38 min)", "Confidence": "94%"},
            )
        ],
        constraints_and_thresholds=[],
        alternatives_rejected=["Delaying board decision by 3 weeks while waiting for five executive calendars"],
        authority=AuthorityRecord(
            deciding_authority="Daniel Mercer (CEO)",
            dissent_preserved=True,
            dissent_summary="March 7–2 dissent notes retained in the board package.",
        ),
        outcome="Board memo, Slide 14, financial appendix, legal citations, 3 anticipated objections, and speaking notes ready.",
        temporal_validity=TemporalValidity(
            decided_at=datetime(2026, 8, 10, 21, 48, 0),
            valid_from=datetime(2026, 8, 10, 21, 48, 0),
            era_label="FY2026",
        ),
        sensitivity_label=confidential_label,
        acl_snapshot=default_acl,
        confidence_score=0.94,
        governance_action=GovernanceAction.RECOMMEND,
        verified_by_human=True,
    )

    for episode in [
        ep_cfo_cap,
        ep_cfo_2019,
        ep_cto_history,
        ep_cto_safe_decline,
        ep_legal_gates,
        ep_cro_speed,
        ep_board_pattern,
        ep_ceo_package,
    ]:
        graph.upsert_episode(episode)

    # Typed temporal edges showing precedent chains and threshold drift
    edges = [
        TemporalGraphEdge(
            edge_id="edge_cfo_supersedes_2019",
            source_node_id="ep_cfo_cap_2026",
            target_node_id="ep_cfo_cap_2019",
            edge_type=EdgeType.SUPERSEDES,
            rationale="March 2026 Board vote (7–2) tightened new-program spending cap from $15M (2019 charter) to $11M.",
            valid_from=datetime(2026, 3, 18),
        ),
        TemporalGraphEdge(
            edge_id="edge_cto_depends_legal",
            source_node_id="ep_cto_auth_history_2026",
            target_node_id="ep_legal_gates_2026",
            edge_type=EdgeType.GOVERNED_BY,
            rationale="Private environment deployment satisfies Legal Gate 1 (no public cloud PHI) and routes 9% denials to named clinicians.",
            valid_from=datetime(2026, 8, 1),
        ),
        TemporalGraphEdge(
            edge_id="edge_board_precedent_cfo",
            source_node_id="ep_board_pattern_2026",
            target_node_id="ep_cfo_cap_2026",
            edge_type=EdgeType.PRECEDENT_FOR,
            rationale="6-year board cybersecurity precedent guides how the $7.4M Phase-One plan is sequenced to address the 7–2 dissent.",
            valid_from=datetime(2026, 8, 10),
        ),
        TemporalGraphEdge(
            edge_id="edge_ceo_depends_all",
            source_node_id="ep_ceo_board_package_2026",
            target_node_id="ep_cto_safe_decline_2026",
            edge_type=EdgeType.DEPENDS_ON,
            rationale="Thursday board package explicitly incorporates the CTO safe-decline escalation to VP Clinical Operations.",
            valid_from=datetime(2026, 8, 10),
        ),
    ]
    for edge in edges:
        graph.add_edge(edge)

    return graph
