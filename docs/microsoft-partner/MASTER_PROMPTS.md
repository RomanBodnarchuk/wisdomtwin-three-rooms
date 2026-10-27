# WisdomTwin — Six-Stage Master Engineering Prompts

These six sequential prompts capture the exact architectural blueprint implemented in `backend/` and `copilot/`.

---

## Prompt 1: Canonical Decision-Episode & Temporal Graph Schema
> You are a senior AI engineer and Microsoft Graph specialist building WisdomTwin, a role-specific digital twin for Microsoft shops. WisdomTwin ingests Microsoft 365 data via Microsoft Graph (mail, SharePoint, OneDrive, Teams, calendar) using delta queries for incremental sync, change notifications as push triggers, and a daily delta sweep backstop. It extracts Decision Episodes from all ingested text using an LLM pass and stores them in a temporal context graph with typed edges (`DEPENDS_ON`, `SUPERSEDES`, `PRECEDENT_FOR`, `CONTRADICTS`, `EVIDENCE_FROM`, `DECIDED_BY`, `GOVERNED_BY`). It replicates Microsoft Entra ID access control lists and Microsoft Purview sensitivity labels at the chunk level.
>
> Design the canonical `NormalizedDocument` and `DecisionEpisode` schemas as Pydantic v2 models in `backend/app/schemas/decision_episode.py` including: question asked, decision statement, verbatim evidence considered, constraints and counterfactual "never-do" boundaries, rejected alternatives, authority that decided (with vote tallies and preserved dissent), outcome, temporal validity with threshold drift annotations, Purview sensitivity label, Entra ACL snapshot, per-field confidence scores, and governance action (`recommend`, `escalate`, `safe_decline`).

---

## Prompt 2: Microsoft Graph Delta Ingestion & Structure-Preserving Parser
> Using the confirmed WisdomTwin `NormalizedDocument` and `DecisionEpisode` schemas, implement the Microsoft Graph ingestion layer in `backend/app/ingestion/ms_graph.py` and `backend/app/ingestion/parser.py`:
> 1. Least-privilege application scopes (`Mail.Read`, `Sites.Read.All`, `Files.Read.All`, `ChannelMessage.Read.All`, `OnlineMeetingTranscript.Read.All`, `InformationProtectionPolicy.Read.All`).
> 2. Delta query support with durable `deltaLink` persistence that commits the token strictly AFTER downstream raw-store and normalization succeed.
> 3. Webhook change notifications acknowledging within `<3s` plus a daily delta sweep before the 30-day token expiry.
> 4. First-class Purview sensitivity label and Entra ID group role resolution.
> 5. Raw byte staging store (`RawByteStore`) + structure-preserving Office parser (`StructurePreservingParser`) that preserves Word headings, PowerPoint slide titles, Excel sheet/column headers, and speaker turns in 512-token overlapping chunks.
> 6.Bounded concurrency of 4 requests per mailbox/site with exponential backoff on HTTP 429.

---

## Prompt 3: Three-Pass Judgment Extraction, Entity Resolution & Human Validation Loop
> Implement the Decision-Episode Extraction Engine in `backend/app/extraction/`:
> 1. Three specialized prompt templates (`DECISION_DETECTOR_PROMPT`, `REASONING_EXTRACTOR_PROMPT`, `COUNTERFACTUAL_EXTRACTOR_PROMPT`) plus `MONTHLY_CONSOLIDATION_PROMPT`.
> 2. Cross-source deduplication (`CrossSourceDeduplicator`) collapsing identical decisions across email, SharePoint decks, and Teams/Zoom transcripts into one episode with merged evidence chains.
> 3. Historical entity resolution (`HistoricalEntityResolver`) mapping email aliases, display names, and role tenures across up to 25 years against Entra ID.
> 4. Human validation queue (`HumanValidationQueue`) flagging low-confidence extractions (`<0.75`) or `safe_decline` episodes for a named human reviewer and storing corrections as few-shot examples.

---

## Prompt 4: Temporal Context Graph & Precedent Search API
> Implement the Temporal Context Graph in `backend/app/graph/context_graph.py`:
> 1. Node and typed temporal edge storage (`DEPENDS_ON`, `SUPERSEDES`, `PRECEDENT_FOR`, `CONTRADICTS`, `GOVERNED_BY`).
> 2. Point-in-time historical querying and 1-hop precedent/supersedes edge traversal so queries surface how CFO/CTO thresholds drifted across role holders.
> 3. Governed Safe-Decline enforcement: when precedent confidence is below the governance threshold (such as peak-load throughput at proposed volume), withhold the answer and return the named human reviewer (`Vice President of Clinical Operations`) and estimated review duration (`38 minutes`).
> 4. Seed the graph in `backend/app/seed/demo_corpus.py` with the canonical healthcare enterprise dataset (`$11M` cap, `7–2` vote, dissent preserved, `12,400` decisions, `91/9` split, `$7.4M` phase one, `38` min review, `62% -> 91%` board sequence confidence lift).

---

## Prompt 5: Entra ACL & Purview Permission Enforcement + Voice Huddle Abstraction
> Implement the permission-aware retrieval plane in `backend/app/security/permissions.py` and the Audio Executive Huddle orchestrator in `backend/app/huddle/`:
> 1. Enforce Entra ID ACLs and Purview `VIEW` + `EXTRACT` rights before any chunk or episode is synthesized.
> 2. Record every query and surfaced chunk in an immutable `ComplianceAuditLogger` with SHA-256 pseudonymized requester hashes.
> 3. Implement the 3-operation `VoiceAbstractionLayer` (`start_session`, `stream_audio`, `end_session`) with concrete adapters for Grok Voice 3.0 (`grok_voice_3`), OpenAI Realtime (`openai_realtime`), Azure AI Speech (`azure_speech`), and a future Dessa adapter stub (`dessa_preview_stub`).

---

## Prompt 6: Microsoft 365 Copilot Plugin Package & GTM Kit
> Generate the OpenAPI 3.1 specification (`copilot/openapi.yaml`), Teams/M365 app manifest (`copilot/manifest.json`), declarative agent (`copilot/declarativeAgent.json`), and AI plugin definition (`copilot/ai-plugin.json`) exposing `queryTwin`, `listRoles`, `getJudgment`, and `startHuddle` with On-Behalf-Of (OBO) Entra authentication. Include the complete Microsoft for Startups, ISV Success, Partner Center checklist, and 90-day CFO Design Partner Pilot package in `docs/microsoft-partner/PLAYBOOK.md`.
