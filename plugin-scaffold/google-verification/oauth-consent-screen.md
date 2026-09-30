# OAuth consent screen

Prepare this in the Google Cloud Console. Do not mark verification as submitted or granted from this repository. Roman submits the form.

## App identity

- App name: WisdomTwin
- User support email: privacy@wisdomtwin.ai, or the Google account that can receive verification mail if the console requires a different mailbox. Use an address Roman controls.
- Application home page: https://wisdomtwin.ai
- Privacy policy URL: https://wisdomtwin.ai/privacy
- Authorized domain: wisdomtwin.ai
- Developer contact: privacy@wisdomtwin.ai

## Scopes to add

- `https://www.googleapis.com/auth/gmail.readonly`
- `https://www.googleapis.com/auth/drive.readonly`

Do not add send, modify, or full-drive scopes. The product stays read-only.

## Publishing status

Leave the app in testing until verification is granted. The connectors stay off in WisdomTwin until `GMAIL_CONNECTOR_ENABLED` and `DRIVE_CONNECTOR_ENABLED` are set. Flipping those variables does not require a code change, and it should wait until Google has accepted the scopes.

## Testing-mode limits

An unverified app in testing can have up to 100 test users. Google shows a warning on the consent screen that the app is not verified. Only the accounts listed as test users can complete the grant. Those limits are Google's, and they stay in place until verification is granted.
