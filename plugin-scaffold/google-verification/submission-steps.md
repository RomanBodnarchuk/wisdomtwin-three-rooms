# Verification steps for Roman

Stop when the form is ready to send. This repository does not submit it and does not record a Google decision.

1. Open the Google Cloud Console for the WisdomTwin project.
2. Open APIs & Services, then the OAuth consent screen.
3. If the console asks for a user type, choose External and keep the app in testing.
4. Set the app name to WisdomTwin.
5. Set the user support email and the developer contact email. Use privacy@wisdomtwin.ai if that mailbox is on the account, otherwise use the mailbox the console will accept and that Roman reads.
6. Set the privacy policy URL to https://wisdomtwin.ai/privacy. Confirm the page loads before you continue. The page source is `public/privacy/index.html` in this repository and is public only after that site deploy.
7. Add the two scopes listed in `oauth-consent-screen.md`. Do not add write scopes.
8. Add test users from `test-users.md`. Stay within the 100-user testing limit.
9. Open the verification request for the two restricted scopes when you are ready. Paste the matching paragraphs from `scope-justifications.md`.
10. Review the consent-screen warning testers will see, then stop. Submit the verification request yourself in the console. Come back to the connectors only after Google grants the scopes, and then set `GMAIL_CONNECTOR_ENABLED` and `DRIVE_CONNECTOR_ENABLED`.

If a label in the console has moved, follow the consent-screen wizard for an external app that is still in testing. The values above are what to enter. The click path can differ by console revision.
