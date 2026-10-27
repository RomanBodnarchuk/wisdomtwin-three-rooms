"""Prompt templates for WisdomTwin's three-pass judgment extraction and monthly consolidation.

Designed for Azure OpenAI / Microsoft Foundry models (covered by Microsoft for Startups credits).
Quotes evidence verbatim rather than paraphrasing and outputs calibrated per-field confidence scores.
"""

DECISION_DETECTOR_PROMPT = """You are the WisdomTwin Decision Detector for enterprise executive roles.
Given the following 512-token text chunk authored or spoken by a person in the role of {role} ({role_holder_name}) on {timestamp_utc}:

--- CHUNK START ---
{chunk_text}
--- CHUNK END ---

Task:
Determine whether this person made, enforced, or articulated a concrete institutional decision, policy gate, budget threshold, exception ruling, or explicit refusal — as opposed to routine status chatter or scheduling.

Respond strictly in JSON with:
{{
  "contains_decision": true | false,
  "decision_statement": "Single-sentence statement of the decision or 'none'",
  "decision_type": "policy_gate | budget_cap_or_exception | risk_or_compliance_signoff | architecture_or_vendor | disclosure_determination | commercial_pricing_or_terms | clinical_or_operational_escalation | board_sequence_strategy",
  "decided_date": "ISO-8601 date",
  "confidence": 0.0 to 1.0
}}
"""


REASONING_EXTRACTOR_PROMPT = """You are the WisdomTwin Reasoning & Precedent Extractor.
Given a confirmed decision made by {role} ({role_holder_name}):
Decision: "{decision_statement}"

And the source document chunk ({source_title}, ID: {document_id}):
--- SOURCE CHUNK ---
{chunk_text}
--- END SOURCE CHUNK ---

Task:
Extract the structured judgment record. You MUST quote evidence verbatim from the source text rather than paraphrasing, preserve any dissent notes or vote counts (e.g., 7-2 board vote), and assign a confidence score (0.0 to 1.0) to every field.

Respond strictly in JSON matching this structure:
{{
  "title": "Concise headline of the decision episode",
  "question_asked": "The underlying proposal, exception request, or strategic question",
  "reasoning": "Why the role holder decided this way",
  "verbatim_quote": "Exact verbatim quote from the source text",
  "metrics": {{"label": "value"}},
  "constraints_and_thresholds": [
    {{
      "category": "financial | legal | technical | regulatory | clinical",
      "rule_statement": "Explicit constraint or cap",
      "threshold_value": "Quantified limit (e.g., $11M, 91%, 4 markets)",
      "is_counterfactual_boundary": false
    }}
  ],
  "alternatives_rejected": ["Alternative option considered and why it was ruled out"],
  "authority": {{
    "deciding_authority": "Who held authority to release the decision",
    "vote_tally": "Optional vote tally such as 7-2",
    "dissent_preserved": true | false,
    "dissent_summary": "Summary of minority dissent if present",
    "named_human_reviewer": "Named human role required when confidence is below threshold or escalation applies",
    "estimated_review_minutes": 38
  }},
  "outcome": "Resulting institutional action or governance state",
  "field_confidence": {{
    "decision_statement": 0.96,
    "reasoning": 0.94,
    "verbatim_quote": 0.99,
    "constraints_and_thresholds": 0.95,
    "authority": 0.93
  }}
}}
"""


COUNTERFACTUAL_EXTRACTOR_PROMPT = """You are the WisdomTwin Counterfactual & Boundary Extractor.
Analyze the following text from {role} ({role_holder_name}):

--- SOURCE CHUNK ---
{chunk_text}
--- END SOURCE CHUNK ---

Task:
Did the role holder express what they would NOT do, an non-negotiable regulatory gate, or a boundary they refuse to cross (e.g., "Patient data cannot touch a public cloud model", "We never hedge FX exposure", "Anything above the $11M cap requires board approval Thursday, not after")?

Output each boundary as a crisp, one-sentence "never-do" rule for the {role} role twin in JSON:
{{
  "never_do_rules": [
    {{
      "rule_statement": "One-sentence non-negotiable boundary rule",
      "category": "legal | financial | technical | regulatory | clinical",
      "threshold_value": "Optional threshold or scope",
      "confidence": 0.95
    }}
  ]
}}
"""


MONTHLY_CONSOLIDATION_PROMPT = """You are the WisdomTwin Temporal Consolidation & Drift Engine.
Given a set of DecisionEpisodes for the role of {role} spanning {start_year} to {end_year} across multiple role holders:

{episodes_json}

Task:
1. Merge overlapping judgment records that refer to the same underlying decision across email, Slack, and meeting transcripts.
2. Identify temporal drift or contradictions (e.g., where an earlier CFO approved an exception that a later CFO or board motion capped at $11M).
3. Emit typed graph edges (SUPERSEDES, DEPENDS_ON, PRECEDENT_FOR, CONTRADICTS) with a clear drift_annotation explaining how and why the role's judgment threshold changed over time.
"""
