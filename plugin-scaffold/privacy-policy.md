# WisdomTwin hosted-plugin privacy policy — draft

**Status: draft, not adopted or effective.** This document describes the proposed hosted WisdomTwin plugin and its MCP service. It must be reviewed, reconciled with the deployed service and adopted before public use. It does not replace the existing WisdomTwin website's on-premises policy or govern separate customer engagements.

## Operator and contact

The proposed service operator and controller is **WisdomTwin, Inc.** The company's existence, authority to operate this service, relationship to the directory publisher and contact ownership have not been verified in this work. The proposed privacy contact is **privacy@wisdomtwin.ai**; confirm that it is controlled and monitored before adoption. No incorporation jurisdiction, date or corporate verification is asserted here.

The observed verified directory publisher is **ROMAN GREGORY BODNARCHUK**, using an individual developer identity. That observation does not verify WisdomTwin, Inc. as the directory publisher. The operator and publisher relationship must be stated accurately in the adopted public policy.

## Service and source access

WisdomTwin indexes business evidence for an assigned organizational role and answers business questions with source citations. The indexed role belongs to an authorized business organization; typing a domain or role title does not establish authority to access it. Corporate OIDC sign-in verifies the signed issuer, subject and email. An operator provisions allowed roles and exact source-account identity bindings.

Slack adapter code is present, but a real hosted Slack service and the necessary provider authorization have not been established by this candidate. Gmail and Google Drive remain disabled and unverified. Their current adapters retrieve Gmail snippets/metadata and Drive file names/descriptions; full email and document ingestion are incomplete.

Source scopes are read-only. The service does not send Slack messages or mail, or edit, share or delete source files. Connection setup and user-requested ingestion change WisdomTwin's internal connection/index state. Source authorization happens in the provider's sign-in flow; users should not enter passwords, one-time codes, API keys or bearer tokens in chat.

## Data processed

The intended hosted service processes:

- Verified identity identifiers, corporate email/domain, operator-assigned role permissions and source workspace/user or Google subject bindings.
- Role and tenure records, organizational metadata, source authorship identifiers and connection status.
- Authorized business source text transiently during ingestion and current-access retrieval, and the user's business question while answering it.
- Indexed vectors, source URIs, chunk positions/content hashes and hashed keywords under the protected role namespace. These remain protected data; hashing does not make business records anonymous.
- Encrypted source credentials and durable MCP authorization state, including limited-lived authorization transactions, grants and refresh-token state.
- Minimal audit events such as action, outcome/error code, organization/role identifiers and event time. Audit events do not intentionally include source text, raw provider payloads, tokens or full user questions. Operational hosting logs need separate configuration and retention confirmation before adoption.

Real source text is not intended to persist in the role index. A query re-fetches sources with the caller's current source grant, then checks content hash and authorship. Changed or inaccessible material is withheld. Citation snippets returned to ChatGPT are transient service output and may be retained by the user's ChatGPT environment under its own settings. Local synthetic fixtures can retain test text; that mode is restricted to explicit loopback local/test execution and is not the hosted data path.

## Purposes and recipients

Data is processed to authenticate and authorize the assigned business role, connect approved sources, perform user-confirmed ingestion, retrieve current source evidence, provide citations, apply quotas, secure the service and honor deletion requests. It is not intended for unrelated profiling, advertising or surveillance. The final operator must confirm the applicable legal basis and any business-customer responsibilities before adoption.

Intended recipients include authorized service personnel and the configured hosting, database and queue providers. Source providers receive the grants and API requests needed to retrieve authorized evidence. If paid model API use is explicitly enabled, authorized source text/query data is sent to the configured model provider for embeddings and, optionally, answer generation. The intended embedding model is `text-embedding-3-small`; optional generation uses the Responses API. Otherwise the service returns extractive evidence for ChatGPT to synthesize. No paid model API calls were made to prepare this candidate.

The deployed processors, contract terms, regional storage/transfers and provider retention/training settings must be confirmed and disclosed before publication. This draft makes no blanket promise about third-party retention or model training. The proposed operator does not intend to sell personal data.

## Retention and deletion

Role indexes are scheduled for removal after **30 days of inactivity**, or on an authorized deletion request. A daily retention task requires a functioning scheduler and worker. The cutoff establishes cleanup eligibility; actual execution and request turnaround have not been verified on a hosted deployment and must be tested before an effective policy promises timing.

Role deletion is intended to remove chunks, source credentials, connections, ingestion jobs/pending connection state, role and tenure records, and empty organizational records, and to revoke the user's MCP grants. Operator-provisioned membership/entitlement records are administered separately until the operator removes them. Minimal audit events have a separate **30-day** retention limit from their event time. Expired temporary OAuth state is swept by maintenance. Hosting/backup retention is not yet established and must be added to the adopted policy; a database deletion is not a claim that every provider's backup has been immediately erased.

This service does not delete original Slack messages, mail or files. Users may revoke source grants at their source provider. Changing or revoking current source access prevents that material from being used as new citation evidence.

## Security and user controls

Production authorization and source credentials use encrypted durable Postgres storage with operator-managed keys. Access checks bind the current verified identity, assigned role and source account. Fixture SQLite, memory and auth-disabled modes are local test facilities. These are code/test design statements, not certification or independently audited production claims.

After launch and contact verification, users can request access, correction, role-index deletion or questions about processing through the verified privacy contact. The service also provides authenticated role deletion at `DELETE /roles/{role_id}` for an authorized caller. Administrators manage role assignment and membership removal. Requests and any legally required response periods must be handled by the final operator under the applicable rules.

## Adoption and changes

Before adoption, confirm operator/contact identity, actual provider permission and configuration, access/deletion/retention behavior, processor locations and backup retention. Publish the adopted hosted-plugin policy at the exact HTTPS URL used in the package. Set an effective date only after adoption and update that public copy when actual practices change. The existing `wisdomtwin.ai/privacy` on-premises page is not evidence that this hosted draft is published or accepted.
