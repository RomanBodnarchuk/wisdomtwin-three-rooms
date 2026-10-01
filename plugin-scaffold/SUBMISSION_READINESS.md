# Submission readiness: private candidate only

The current deliverable is an offline, deterministic **candidate NOT FOR SUBMISSION**. It preserves `https://REPLACE_WITH_RAILWAY_PUBLIC_URL/mcp`. No public service origin, real reviewer access, adopted hosted policy, completed provider approval or directory submission is established by this repository.

## Completed locally

| Item | Evidence and boundary |
| --- | --- |
| Existing prototype, four-tool contract | Original MVP fixture tests and the current test suite. Exact arguments/defaults are also checked without importing the server. |
| Portable package and two skills | Root `plugin.json`, `mcp.json`, `skills/query-twin/SKILL.md`, `skills/update-twin/SKILL.md`. No new scaffold or custom UI. |
| Offline full schema validation | `package_validator.py` uses complete vendored official schemas and pinned snapshot hashes; separate checks cover OpenAI metadata, safe paths, icon dimensions, skill frontmatter and the four-tool boundary. |
| Deterministic candidate build | `./package.sh --candidate` emits a fixed-order/timestamp/mode ZIP, `.sha256` and `.contents.json`. Parent integration records the final artifact hash and source commit. |
| Safer auth/index implementation | Corporate signed OIDC, assigned role/source identity, durable encrypted authorization state, current-access source revalidation and metadata-only real indexing are code/test results. Deployment behavior remains to be demonstrated. |
| Independent review follow-up | Membership-generation/issuance races, SDK refresh replay, deleted Slack threads and bounded 429 handling have synthetic regressions in [REVIEW_FOLLOWUP.md](REVIEW_FOLLOWUP.md). |
| Honest publisher/commerce metadata | Observed verified individual publisher `ROMAN GREGORY BODNARCHUK`; no invented verified company, subscription pitch, checkout or pricing in the listing/skills. |
| Hosted legal preparation | `privacy-policy.md`, `terms-of-service.md`, `terms.html` are unadopted drafts scoped only to this hosted plugin. Existing website/customer policies are not replaced. |

The original PR review used synthetic Slack fixtures: twelve MVP tests, four tools and ten chunks. It does not prove live Slack or production Postgres. Run the full current suite and record its actual output; no paid embedding or Responses requests were made for this candidate.

## Blocked until Roman completes these actions

| Requirement | Current status | Concrete next action |
| --- | --- | --- |
| Verified publisher identity | Individual observed; company verification not established | In the OpenAI developer dashboard, choose the exact verified identity. Match `author.name`, `interface.developerName` and internal `developer_organization` to it. Do not treat WisdomTwin, Inc. as verified. |
| Legal operator and contact | Proposed WisdomTwin, Inc.; mailbox/authority unverified | Verify entity status, authority, operator/publisher relationship and ownership of `privacy@wisdomtwin.ai`; adopt the hosted drafts and set their effective dates. |
| Hosted privacy, terms and support | Placeholder links; drafts not published/adopted | Publish the reviewed plugin-specific pages and replace the three placeholder listing URLs. The old `wisdomtwin.ai/privacy` on-premises policy is unsuitable for this hosted flow. Website/support must identify the same publisher. |
| Public HTTPS MCP deployment | Railway private project exists; no verified service/host | Create the service rooted at `plugin-scaffold`, Postgres with pgvector, Redis, web/worker/beat; configure secrets outside Git and verify `/health` and `/mcp`. |
| Corporate and MCP authorization | Code/tests only | Configure corporate OIDC, operator-assigned role/provider identities and exact OAuth callbacks. Test signed login, PKCE/resource validation, current entitlement, restart persistence and revocation against real HTTPS. |
| Slack real/commercial use | Adapter/fixtures only | Obtain applicable Slack/Salesforce commercial authorization; configure the app and matching workspace/user grant; demonstrate real current-access retrieval before setting activation gates. This PKCE adapter requires a PKCE-enabled Slack app; enabling that setting is one-way without Slack support and needs Roman's explicit approval. A blanket `search.messages` prohibition has not been established. |
| Model API operation | Spend opt-in remains off | Only with explicit authorization, configure key/embedding model and exercise the real indexed path. Optional Responses mode omits temperature for reasoning. Fixture results do not prove real API availability or cost. |
| Cleanup and deletion | Code and local behavior; operator execution unverified | Run authenticated role deletion and daily retention on deployed Postgres/worker/beat; verify data/state removal and MCP grant revocation. Distinguish 30-day inactivity eligibility from observed task execution. |
| MCP domain verification | Challenge unconfigured | In the MCP connection flow, use the portal's actual challenge, configure `OPENAI_APPS_CHALLENGE`, and verify its exact public response. Do not commit it. |
| Demo/reviewer access | No recording URL or reviewer credentials established | Record the five positive scenarios in a permitted sample workspace. Set `review.demo_recording_url`; enter reviewer access securely in the portal, outside the ZIP. |
| Google completeness and scope review | Both connectors disabled/unverified | Finish full-content ingestion and provenance, confirm identity/read-only scopes and required Google review. `google-verification/` is preparation, not a request or approval record. |
| Portal scans/upload/submission | Not performed | Upload the production ZIP only after prerequisites, inspect Metadata & Skills/MCP tool findings and required scans, then explicitly submit. Publication is a separate later dashboard action. |

## Package commands and release evidence

```bash
./package.sh --check
./package.sh --candidate --output-dir /workspace/wisdomtwin-plugin-artifacts
```

These modes are offline. The ZIP has exactly five files: `plugin.json`, `mcp.json`, `assets/logo.svg`, and the two skill documents. No fixture data, server code, reviewer credentials, schema snapshots or legal drafts are uploaded in it.

`./package.sh --release` (also the default command) refuses placeholder hosts. Once the real URLs and publisher are reconciled, supply `MCP_SERVER_URL` if staging an endpoint, `PACKAGE_RELEASE_EVIDENCE` as the path to a private JSON evidence record, and `PACKAGE_MCP_ACCESS_TOKEN` in the environment for read-only `tools/list`. Do not place tokens in the evidence file or Git.

The evidence object must contain `mcp_url`, `publisher`, `privacy_url`, `terms_url` matching the staged package; `package_files_sha256` for every staged ZIP member; and `published_pages_sha256` keyed by `websiteURL`, `supportURL`, `privacyPolicyURL`, `termsOfServiceURL`. Its `checks` object must contain these factual operator records:

- `verified_publisher`
- `hosted_legal_adoption`
- `oauth_end_to_end`
- `source_revalidation`
- `deletion_and_retention`
- `third_party_authorization`
- `reviewer_access`

Each check has `result: "passed"`, `path` to its nonempty supporting record (relative to the evidence file is supported), and that file's `sha256`. These records document completed work; changing a flag or writing "passed" does not establish it. The validator binds their hashes and exact metadata, checks live page hashes, rejects draft legal pages, verifies health/OAuth discovery and an anonymous 401 challenge, and scans the authenticated four-tool contract. It cannot independently certify corporate authority, contract permission, legal adoption or recorded cleanup outcomes. Those facts require Roman's review of the records. It never submits or publishes a package.

## Primary requirements checked October 1, 2026

Portable `plugin.json`, root MCP configuration and automatic skill discovery follow [OpenAI packaging guidance](https://developers.openai.com/plugins/build/plugins); full schema snapshots and normalized hashes are documented in [schema provenance](schemas/PROVENANCE.md). Inline OpenAI extension metadata is canonical when present; compatibility fallback remains supported.

OAuth discovery, resource binding, PKCE and per-tool authentication follow [OpenAI authentication guidance](https://developers.openai.com/plugins/build/auth). Required listing links, skill scans, review scenarios, demo and dashboard actions follow the [submission field reference](https://developers.openai.com/plugins/deploy/submission). Source permissions, accurate metadata, published privacy disclosure and restrictions on subscription promotion follow [plugin guidelines](https://developers.openai.com/plugins/plugin-guidelines). Passing local checks is not a promise of acceptance or review timing.

[Slack's current PKCE guidance](https://docs.slack.dev/authentication/using-pkce/) requires enabling PKCE on the app and omitting `client_secret` from its PKCE code exchange. No Slack app settings or real grants were changed here. [Slack rate-limit guidance](https://docs.slack.dev/apis/web-api/rate-limits/) requires respecting `Retry-After`; the adapter permits one bounded short-delay retry and otherwise returns safe retry guidance. Applicable history/replies commercial rate limits and search pagination still need authorized live validation; the current ingestion adapters fetch at most one provider page (up to 100 items), even when `max_items` is larger. See [PRODUCTION_LAYOUT.md](PRODUCTION_LAYOUT.md) for the exact intended services and configuration names.
