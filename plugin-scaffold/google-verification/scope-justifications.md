# Scope review notes — current adapter limitations

These are preparation notes, not approved or ready-to-paste full-product justifications. Roman must reconcile scopes with the completed implementation, least-privilege requirements, hosted privacy disclosure and Google's actual review process.

## Gmail

Intended role use: a permitted business account's current user asks questions about work communications. The requested source scope is `https://www.googleapis.com/auth/gmail.readonly`, with identity scopes `openid email`. Current retrieval uses `format=metadata` and message snippets. It does not decode complete message bodies or attachments. Do not tell a reviewer that full messages are indexed or quoteable in this build.

Before claiming full-content support, implement and test body extraction, source authorship and current-access revalidation, then establish why the requested scope is the minimum needed. Real index storage is vectors/source hashes and hashed keywords; source text is transient, not persistently saved as citation excerpts. User-confirmed ingestion is limited to the chosen query and item count. The account must match the operator-provisioned Google subject/business role. No send, modify or delete action is part of this plugin.

## Drive

Requested source scope: `https://www.googleapis.com/auth/drive.readonly`, plus identity scopes. Current retrieval indexes file names and descriptions and checks metadata authorship; it does not export or download document bodies. Do not claim metadata is already full document text, or assert that this implementation demonstrates the need for broad full-content scope.

Before activation, finish permitted file-content extraction and provenance, evaluate narrower access options for the actual workflow, test re-fetch under current permissions and disclose the resulting data flow. The role index retains vectors and source metadata; no source edit, share or delete action is intended.

## Reviewer evidence still needed

Provide a permitted managed test account, actual query/ingestion/re-fetch demonstration, exact granted scopes, realistic retention/deletion behavior, adopted hosted privacy disclosure and applicable Google review/assessment records. Both connectors remain disabled. No verification request, decision or assessment is evidenced by this repository.
