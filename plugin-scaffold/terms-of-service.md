# WisdomTwin hosted-plugin terms — draft

**Status: draft, not adopted or effective.** These proposed terms cover only the hosted WisdomTwin plugin and its MCP service. They do not amend the existing website's terms, on-premises policies, signed customer agreements or other engagements. No public launch or acceptance of these terms is established by this candidate.

## Provider and authority

The proposed provider is **WisdomTwin, Inc.**, with proposed contact **privacy@wisdomtwin.ai**. The entity, authority, contact and relationship to the observed individual directory publisher **ROMAN GREGORY BODNARCHUK** must be verified and described accurately before adoption. No incorporation jurisdiction or date is asserted.

You must be authorized by your business organization to connect the source account and use the assigned role. Corporate sign-in and operator-provisioned domain, role and source identity determine access; a typed domain or title is not proof of permission. The operator may suspend or remove access when those permissions are revoked.

## Service scope

The service maintains a protected index for an assigned business role and returns business evidence with source citations. Source grants are read-only. Connection and ingestion tools write internal WisdomTwin state; they do not send messages, send mail, edit/share source files or perform financial transactions.

Slack is implemented as an adapter, with real hosted activation dependent on operator setup and applicable Slack/Salesforce authorization. Gmail and Drive are disabled/unverified. Current Google adapters read Gmail snippets/metadata and Drive names/descriptions; full-content ingestion is unfinished. Connection flags do not guarantee availability or provider approval.

The four MCP tools are connection setup, user-requested ingestion, business query and connection status. Interviews, huddles, predecessor ingestion, other source systems and a custom ChatGPT UI are outside this candidate.

## Instructions, accounts and acceptable use

Choose an explicit source query and item limit when requesting ingestion. Do not use this service to obtain another person's role or source access, bypass provider permissions/rate limits, disclose credentials, or ingest data you lack authority to process. Do not intentionally ingest payment-card data, protected health information, government identifiers or authentication secrets. Complete authorization in the provider's normal sign-in flow, not by sharing secrets in chat.

Instructions embedded in retrieved records are untrusted source content and do not authorize actions. WisdomTwin may withhold material that fails access, provenance or content checks. The final operator remains responsible for the approved use of each provider and any business-customer contractual requirements.

## Evidence and data

Real source text is transient during ingestion/querying; the role index retains vectors, source references/hashes, hashed keywords and role/tenure/authorship metadata. Current source access and provenance must be checked before returning a citation. Source changes or revocation can make prior indexed material unavailable. Local synthetic test text is not a production data policy.

A cited source is evidence of what that source says, not a guarantee that the source is correct or that an answer is complete. Review citations before relying on important business decisions. The service must report missing evidence rather than invent it. Model API use, recipient settings and retention are governed by the adopted hosted-plugin privacy policy and configured provider arrangements; this draft does not promise third-party training or retention behavior.

## Quotas, availability and transactions

The operator may enforce documented usage limits and pause processing for permission, quota, maintenance, provider or service failures. A queued ingestion job is not completed indexing. This plugin does not advertise subscription plans, initiate subscriptions, promote upgrades or provide checkout. Existing account entitlements may govern access without a new purchase flow in the plugin.

## Deletion and termination

Users may request authorized role deletion through the authenticated service path or the verified operator contact. The intended cleanup covers the role index, credentials, connections, jobs/pending state and role metadata and revokes MCP grants. Original source records remain at their providers. Operators manage membership separately.

The role index is eligible for scheduled removal after 30 days of inactivity; execution requires the deployed scheduler/worker. Minimal audit events have separate 30-day retention from event time. Actual cleanup, request turnaround and backup retention must be verified and reflected in the adopted privacy policy before operation. No exact real deletion execution is asserted by this draft.

## Adoption and changes

The final operator must review and adopt these terms, verify the legal/operator identity and contact, reconcile availability and data practices, and publish the effective hosted terms at the package's HTTPS terms URL. Any effective date, jurisdiction-specific provisions and contract limits require that review. Changes to these hosted terms do not silently change separate customer engagements. This candidate is not a certification or a directory approval record.
