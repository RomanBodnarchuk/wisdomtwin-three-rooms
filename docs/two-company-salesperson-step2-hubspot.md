# Two-company virtual salesperson: Step 2 HubSpot proof

Checked Tuesday, October 6, 2026. The private app access token and client secret are stored only as mode-600 files outside this repository. Neither value is printed here.

This step proves hosting, the scopes the token actually has, and one reversible owner test. It does not enroll anyone, send email or SMS, edit Calendly, edit ElevenLabs agents, or create schema.

Rollback for this step is complete. Every HubSpot record this run created was deleted. The owner contact was not deleted. An uncommitted worker directory already in the tree was not edited.

## Verdict

Portal `66868` is hosted in `na1`. That is a US location, which is what the ElevenLabs HubSpot integration requires. The token prefix was not treated as proof. `GET /account-info/v3/details` was.

The requested contact, company, and deal read and write scopes are present, and the matching CRM calls succeeded. Notes, calls, meetings, and tasks also succeeded, even though those scope names are absent from the token's scope list. Schema and pipeline create calls are authorized. No property and no pipeline was created.

A safe two-campaign record cannot be stored with the fields that already exist. The gap is documented below. One owner test deal and one owner test note were created, read back, rerun without a second copy, and then deleted.

The ElevenLabs native HubSpot integration still requires a dashboard paste. That paste was not done.

## Hosting

| Call | Result |
| --- | --- |
| `GET /account-info/v3/details` | 200. `portalId` 66868. `dataHostingLocation` `na1`. `accountType` `STANDARD`. `uiDomain` `app.hubspot.com`. `timeZone` `America/New_York`. `utcOffset` `-04:00`. `companyCurrency` `USD`. `additionalCurrencies` includes `CAD`. |
| `GET /account-info/2026-03/details` | 200. Same portal and `dataHostingLocation`. |
| `GET /account-info/2026-09/details` | 200. Same portal and `dataHostingLocation`. |
| `POST /oauth/v2/private-apps/get/access-token-info` | 200. Body field `tokenKey` only. The token was not placed in the URL. `hubId` 66868. `userId` 106421. `appId` 37893956. Scope array length 128. |

Auth for the account and CRM calls was `Authorization: Bearer`, read from the local file inside the script. Docs checked the same day: [Account information](https://developers.hubspot.com/docs/api-reference/legacy/account/account-information/guide) and [Legacy private apps](https://developers.hubspot.com/docs/apps/legacy-apps/private-apps/overview).

## Scopes this token actually has

Scope names below come from the access-token-info response. A name is listed only when that response included it. HTTP results are from the same day against `https://api.hubapi.com`. CRM object calls used the `2026-09` paths in the current deals, notes, and calls guides.

| Capability | Scope name on the token | Probe | HTTP |
| --- | --- | --- | --- |
| Contacts read | `crm.objects.contacts.read` | `GET /crm/objects/2026-09/contacts?limit=1` and email search | 200 |
| Contacts write | `crm.objects.contacts.write` | `POST /crm/objects/2026-09/contacts` with an empty body | 400, missing `hs_legal_basis`. No contact was created. |
| Companies read | `crm.objects.companies.read` | `GET /crm/objects/2026-09/companies?limit=1` | 200 |
| Companies write | `crm.objects.companies.write` | `POST /crm/objects/2026-09/companies` with an empty body | 201. See the accidental company under Rollback. |
| Deals read | `crm.objects.deals.read` | `GET /crm/objects/2026-09/deals?limit=1` | 200 |
| Deals write | `crm.objects.deals.write` | Empty `POST` was 400, missing `dealname`, `pipeline`, and `dealstage`. The labeled test deal was then created. | 400, then 201 |
| Contact property definitions | `crm.schemas.contacts.read` and `crm.schemas.contacts.write` | `GET` one property was 200. Empty `POST /crm/properties/2026-09/contacts` was 400, missing `name`, `label`, `type`, `fieldType`, and `groupName`. | 200 and 400 |
| Company property definitions | `crm.schemas.companies.read` and `crm.schemas.companies.write` | Present on the token. Not used to create a property. | Not created |
| Deal property definitions | `crm.schemas.deals.read` and `crm.schemas.deals.write` | `GET /crm/properties/2026-09/deals/brand_pipeline` was 200. Empty `POST /crm/properties/2026-09/deals` was 400 for the same missing fields. | 200 and 400 |
| Deal pipelines | `crm.pipelines.deals.read` and `crm.pipelines.deals.write` are absent | `GET /crm/pipelines/2026-09/deals` still returned 200. Empty `POST` on both `/crm/pipelines/2026-09/deals` and `/crm/pipelines/2026-03/deals` returned 400, missing `label` and `displayOrder`. | 200 and 400. No pipeline was created. |
| Owners | `crm.objects.owners.read` | `GET /crm/v3/owners?limit=1` | 200 |
| Notes | `crm.objects.notes.read` and `crm.objects.notes.write` are absent | `GET /crm/objects/2026-09/notes?limit=1` was 200. Empty `POST` was 400, not 403. The labeled test note was then created. | 200, 400, then 201 |
| Calls | `crm.objects.calls.read` and `crm.objects.calls.write` are absent | `GET /crm/objects/2026-09/calls?limit=1` was 200. Empty `POST` was 400, not 403. No call was created. | 200 and 400 |
| Meetings | `crm.objects.meetings.read` and `crm.objects.meetings.write` are absent | `GET /crm/objects/2026-09/meetings?limit=1` was 200. Empty `POST` was 400, not 403. No meeting was created. | 200 and 400 |
| Tasks | `crm.objects.tasks.read` and `crm.objects.tasks.write` are absent | `GET /crm/objects/2026-09/tasks?limit=1` was 200. Empty `POST` was 400, not 403. No task was created. | 200 and 400 |
| Associations | No separate scope name was assumed | `GET /crm/associations/2026-09/notes/contacts/labels` and `GET /crm/associations/2026-09/deals/contacts/labels` | 200 |

Object write does not have to be assumed for schema. Schema write is its own pair of scope names, and those names are on this token. The empty property create returned validation 400, which shows the create endpoint is authorized. It was not used to add a field.

The same token also includes scopes this salesperson must not use. They were not called. Examples: `automation.sequences.enrollments.write`, `crm.export`, `crm.import`, `conversations.write`, `conversations.read`, and `settings.users.write`. Connecting this token to an agent would grant those powers to the integration.

## Owner contact

Email search `EQ roman@n5r.com` on `POST /crm/objects/2026-09/contacts/search` returned total 1. The record is `143893597452`. Direct `GET` of that id returned the same email. `lead_owned_by_company` is `Sociable Living`. `lead_source_campaign` is null. `hubspot_owner_id` is `20`. The phone property is present and is not copied here. The send-domain contact `223451166888` was not read or written.

After every create and delete, the contact still existed, the email was unchanged, `lead_owned_by_company` was still `Sociable Living`, and `lead_source_campaign` was still null.

One deal was already associated, `59949721483`, name `Internal Test - Roman`, pipeline `874015340` (Wisdom Clone - Lead Generation), stage `1309257651` (Video Sent). It was not modified. It is an existing test record, not sales traction.

## Campaign fields already on the portal

Read with `GET /crm/properties/2026-09/{objectType}/{propertyName}` before any test write.

| Field | Object | Shape | What it can store |
| --- | --- | --- | --- |
| `lead_owned_by_company` | Contact | Single-select. Options `N5R` and `Sociable Living`. | One company. WisdomTwin is absent. The owner contact already has `Sociable Living`. |
| `lead_source_campaign` | Contact | Single free-text field. | One string. A second campaign would overwrite the first. |
| `brand_pipeline` | Deal | Single-select. Values `n5r_agency`, `wisdomclone`, `10x_mastermind`, `ai_training`. Labels on those options name N5R.ai Agency, WisdomClone.ai, 10X Mastermind, and AI Training Course. | One of those four values per deal. WisdomTwin is absent. |
| `dealname` and `description` | Deal | Free text, one value per deal. | Can label a test deal. They are not a constrained campaign key. |
| Deal pipelines | Deal | Ten pipelines. None is named WisdomTwin. | A deal has one pipeline. |

One person can be associated with more than one deal. Each deal can hold only one `brand_pipeline` value, and none of the current values is WisdomTwin. Contact fields are single-value, so they cannot represent both campaigns without destroying the other value.

Judgment: do not add a property or a pipeline option in this run. The missing piece is a deal-level value for WisdomTwin that can sit beside a separate N5R deal. The token can create schema (`crm.schemas.deals.write`, and empty `POST /crm/properties/2026-09/deals` returned 400 rather than 403). Creating that field would be an account change, and the existing fields cannot do it safely. No property was invented.

## Test note and test deal

Both records used contact `143893597452` only.

Note body: `OWNER TEST 2026-10-06. Private-app scope check for the two-company salesperson. This note is a test. It is not a sales interaction.`

Deal name: `OWNER TEST 2026-10-06 two-company salesperson`.

The deal was placed in the existing default pipeline, label Sales Pipeline, stage `31011fcf-ec64-48db-9ec2-dcb255012882`, label Prospects. That stage is first, open, probability 0.1, and not closed. Amount was `0`. Owner was `20`. `brand_pipeline` was left empty so the test did not claim N5R, WisdomClone, 10X, or AI Training. This is not sales traction.

Association types were read before the writes. Note to contact is HubSpot-defined type `202`. Deal to contact is HubSpot-defined type `3`. A user-defined Decision Maker label, type `2`, was not used.

CRM search does not index a new record immediately. A first pass searched `dealname` and `hs_note_body` right after create, received total 0, and created a second note and a second deal. Those duplicates were deleted in this same run:

| Record | Id | Delete | Following GET |
| --- | --- | --- | --- |
| Duplicate test deal | `65779542710` | 204 | 404 |
| Duplicate test deal | `65762692981` | 204 | 404 |
| Duplicate test note | `118128056197` | 204 | 404 |
| Duplicate test note | `118128011701` | 204 | 404 |

The proof pass did not trust search. It read the contact's associations and batch-read those records.

| Step | Result |
| --- | --- |
| Deal pass 1 | 201. Id `65756344379`. Associated to `143893597452`. |
| Deal pass 2 | Same id. `PATCH` 200. Association read still found one match. |
| Deal read back | Name, pipeline `default`, stage Prospects, amount `0`, and contact `143893597452`. |
| Note pass 1 | 201. Id `118138674717`. Associated with type `202`. |
| Note pass 2 | Same id. No second note. |
| Note read back | Body matched. Associated contact was `143893597452`. |

A deal search during that proof returned total 1 while the results array was empty, so search was not used to decide idempotency.

## Rollback

Deleted only records this run created.

| Record | Id | Delete | Following GET |
| --- | --- | --- | --- |
| Proof test deal | `65756344379` | 204 | 404 |
| Proof test note | `118138674717` | 204 | 404 |
| Accidental empty company | `59092256629` | 204 | 404 |
| The four duplicates above | listed above | 204 | 404 |

The empty company was created because `POST /crm/objects/2026-09/companies` with `{}` is a valid create. It had no name. It was deleted before the proof deal was created.

After rollback, contact `143893597452` remained, and its only associated deal was the pre-existing `59949721483`. A later deal search for the test name did not return the deleted test deals.

## ElevenLabs

Docs rechecked October 6, 2026: [HubSpot integration](https://elevenlabs.io/docs/eleven-agents/customization/integrations/hubspot).

The native integration authenticates with the private app token. The documented UI step is to paste it into the Private App Access Token field in the ElevenLabs integration setup. US hosting through `api.hubapi.com` is supported. Tokens that start with `pat-eu1-` are not. This portal is `na1`, so the hosting block is cleared. The paste was not performed, and the token was not placed in an agent prompt or on a live branch.

A workspace secret API also exists: `POST https://api.elevenlabs.io/v1/convai/secrets` with header `xi-api-key` and body `type` `new`, `name`, and `value`. The documented 200 response returns `secret_id` and `name`, not the value. Reference: [Create secret](https://elevenlabs.io/docs/eleven-agents/api-reference/workspace/secrets/create). That call was not made. `ELEVENLABS_API_KEY` is unset. The connected agent tools can list secret names and do not expose a create-secret tool. Putting the HubSpot token into a tool argument would log it. The HubSpot integration page does not say a workspace secret replaces the Private App Access Token field.

Secret names already stored, values not returned: `twilio_basic_auth_628` and one Twilio account token used by phone `phnum_9801m3aewp7zfa2vsjwtg3jemg5h`. No HubSpot secret name is stored.

## Client secret

The client secret is not required for these CRM calls. HubSpot's private-app webhook docs say the client secret builds `X-HubSpot-Signature`. Checked October 6, 2026: [Validate requests](https://developers.hubspot.com/docs/apps/legacy-apps/authentication/validating-requests). No worker was added here, so no env template was edited. A later worker should use the name `HUBSPOT_PRIVATE_APP_TOKEN` and should add `HUBSPOT_CLIENT_SECRET` only if it verifies webhook signatures. Neither file should contain a value in git.

## Documentation log

Checked October 6, 2026. Auth for HubSpot calls was the bearer token unless the row says the body field.

| Topic | URL | Method and path | Scopes relied on |
| --- | --- | --- | --- |
| Account details | `https://developers.hubspot.com/docs/api-reference/legacy/account/account-information/guide` | `GET /account-info/v3/details`, also `2026-03` and `2026-09` | Not named in that guide. All three returned 200. |
| Token scopes | `https://developers.hubspot.com/docs/apps/legacy-apps/private-apps/overview` | `POST /oauth/v2/private-apps/get/access-token-info` with body `tokenKey` | The response is the scope list. |
| Deals | `https://developers.hubspot.com/docs/api-reference/latest/crm/objects/deals/guide` | `POST` and `GET /crm/objects/2026-09/deals` | `crm.objects.deals.read` and `crm.objects.deals.write` are on the token. |
| Notes | `https://developers.hubspot.com/docs/api-reference/latest/crm/activities/notes/guide` | `POST` and `GET /crm/objects/2026-09/notes`. Contact association type `202`. | Those scope names are absent. Calls returned 200 and 201, not 403. |
| Calls | `https://developers.hubspot.com/docs/api-reference/latest/crm/activities/calls/guide` | `GET` and empty `POST /crm/objects/2026-09/calls` | Those scope names are absent. Result 200 and 400, not 403. No call created. |
| Properties | Live `GET` and empty `POST /crm/properties/2026-09/{objectType}` | Read and the empty create probe | `crm.schemas.contacts.read`, `crm.schemas.contacts.write`, `crm.schemas.deals.read`, `crm.schemas.deals.write`. |
| Pipelines | `https://developers.hubspot.com/docs/api-reference/latest/crm/pipelines/guide` | Guide text shows `GET /crm/pipelines/2026-03/{objectType}`. Live `2026-09` also returned 200. | `crm.pipelines.deals.read` is absent. The GET still returned 200. |
| Associations | Deals and notes guides, plus `GET /crm/associations/2026-09/{from}/{to}/labels` | Labels read before create | Not assumed as a separate scope. Both label reads returned 200. |
| ElevenLabs HubSpot | `https://elevenlabs.io/docs/eleven-agents/customization/integrations/hubspot` | Dashboard paste. Not called. | Private app token. US only. |
| ElevenLabs secret create | `https://elevenlabs.io/docs/eleven-agents/api-reference/workspace/secrets/create` | `POST /v1/convai/secrets`. Not called. | `xi-api-key`. Response omits the value. |
| Webhook client secret | `https://developers.hubspot.com/docs/apps/legacy-apps/authentication/validating-requests` | Not called | Client secret for signature checks, not for CRM bearer calls. |

## Single next action

Do not paste this token into ElevenLabs until the private app scopes are narrowed. The salesperson needs contact, company, and deal read and write. It does not need sequence enrollment, export, import, conversations, or user administration. After that cut, the remaining UI step is the Private App Access Token field on the ElevenLabs HubSpot integration. Do not paste the token into an agent prompt.

The WisdomTwin campaign value is still missing on `brand_pipeline`. Add it only after an explicit decision, using the property API, and leave the existing options in place.
