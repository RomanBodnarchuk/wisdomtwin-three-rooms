# Google consent-screen preparation — not submitted

Gmail and Drive remain disabled and unverified. The current code reads Gmail snippets/metadata and Drive names/descriptions, not full email/document bodies. Do not describe full-content indexing as complete in a review form or enable a connector simply because this preparation file exists.

In the Google Cloud project, confirm the application's actual publisher/operator identity, controlled support/developer mailbox, verified domain and a published hosted-plugin privacy page. Proposed name: WisdomTwin. Proposed contact: privacy@wisdomtwin.ai, subject to ownership verification. The existing on-premises `wisdomtwin.ai/privacy` page is not the hosted-plugin policy. The package's proposed privacy URL is currently a placeholder; replace it only after adoption and public hosting.

The implementation requests `openid email` for identity plus `https://www.googleapis.com/auth/gmail.readonly` or `https://www.googleapis.com/auth/drive.readonly`. Source account identity must match the provisioned Google subject and verified business domain. No send/modify/share/delete scopes are intended. The code rejects grants that contain unexpected scopes; review the exact issued scope set before any activation.

Keep the external app in testing and add only permitted managed business test accounts. Google's testing and verification restrictions must be checked in the current console. Public activation requires the applicable verification and any additional assessment/contract conditions, plus completed connector/provenance behavior. `GMAIL_CONNECTOR_ENABLED`, `DRIVE_CONNECTOR_ENABLED` and `GOOGLE_REVIEW_APPROVED` are activation gates, not evidence of a Google decision.

Google's review requires the application homepage and privacy policy on the same domain. Reconcile the hosted plugin landing page and policy before preparing a request; the current existing-site homepage and Railway policy placeholder do not establish that requirement.

Consult Google's primary [verification guidance](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification) before submitting. Record actual console state and decision evidence outside the public package.
