// Creates the AI_CALL_ELIGIBLE contact properties if they are missing.
// Properties only. This script never reads or writes a contact record and never sets voice_consent.
// Usage: HUBSPOT_SERVER_TOKEN=... node scripts/create-hubspot-properties.mjs
const token = process.env.HUBSPOT_SERVER_TOKEN;
if (!token) {
  console.error('HUBSPOT_SERVER_TOKEN is required. Do not put the token in a file.');
  process.exit(1);
}

const GROUP = 'wt_voice_consent';
const bool = (name, label, description) => ({
  name, label, description, type: 'enumeration', fieldType: 'booleancheckbox', groupName: GROUP,
  options: [
    { label: 'Yes', value: 'true', displayOrder: 0, hidden: false },
    { label: 'No', value: 'false', displayOrder: 1, hidden: false },
  ],
});
const text = (name, label, description) => ({
  name, label, description, type: 'string', fieldType: 'text', groupName: GROUP,
});
const longText = (name, label, description) => ({
  name, label, description, type: 'string', fieldType: 'textarea', groupName: GROUP,
});
const when = (name, label, description) => ({
  name, label, description, type: 'datetime', fieldType: 'date', groupName: GROUP,
});

const properties = [
  bool('voice_consent', 'Voice consent', 'True only when a real AI-voice consent record exists. Never backfill.'),
  text('voice_consent_phone', 'Voice consent phone', 'E.164 number the person consented to be called on.'),
  text('voice_consent_name', 'Voice consent name', 'Name of the person who consented.'),
  when('voice_consent_at', 'Voice consent at', 'When consent was given. ISO-8601.'),
  {
    name: 'voice_consent_method', label: 'Voice consent method', groupName: GROUP,
    description: 'How consent was captured.', type: 'enumeration', fieldType: 'select',
    options: [
      { label: 'Web form', value: 'web_form', displayOrder: 0, hidden: false },
      { label: 'Email reply, manual', value: 'email_reply_manual', displayOrder: 1, hidden: false },
    ],
  },
  longText('voice_consent_text', 'Voice consent text', 'Accepted wording. At least 40 characters.'),
  text('voice_consent_evidence_ref', 'Voice consent evidence ref', 'Pointer to the consent record. Not the consent itself.'),
  text('voice_consent_entity', 'Voice consent entity', 'Legal entity the consent names. Must match WT_CALLING_ENTITY.'),
  text('voice_consent_purpose', 'Voice consent purpose', 'Purpose covered. Must include WT_CALL_PURPOSE.'),
  bool('voice_opt_out', 'Voice opt out', 'True after any opt-out. Suppresses further calls.'),
  bool('voice_dnc_listed', 'Voice DNC listed', 'True if a do-not-call scrub listed this number.'),
  when('voice_dnc_checked_at', 'Voice DNC checked at', 'When the do-not-call scrub last ran. Must be within 31 days.'),
  text('voice_jurisdiction', 'Voice jurisdiction', 'Allowlisted code such as CA-ON. Must match the number.'),
  text('voice_timezone', 'Voice timezone', 'IANA timezone used for the local calling window.'),
  text('voice_campaign_id', 'Voice campaign id', 'Approved campaign this contact belongs to.'),
  text('voice_segment', 'Voice segment', 'Segment that must be on the campaign allowlist.'),
];

async function hs(method, path, body) {
  const r = await fetch('https://api.hubapi.com' + path, {
    method,
    headers: { authorization: `Bearer ${token}`, 'content-type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  const textBody = await r.text();
  if (!r.ok) throw new Error(`${method} ${path} ${r.status} ${textBody}`);
  return textBody ? JSON.parse(textBody) : null;
}

const groups = await hs('GET', '/crm/v3/properties/contacts/groups');
if (!groups.results?.some((g) => g.name === GROUP)) {
  await hs('POST', '/crm/v3/properties/contacts/groups', {
    name: GROUP, label: 'WisdomTwin voice consent', displayOrder: -1,
  });
  console.log('created group', GROUP);
} else {
  console.log('group exists', GROUP);
}

for (const property of properties) {
  const existing = await fetch(`https://api.hubapi.com/crm/v3/properties/contacts/${property.name}`, {
    headers: { authorization: `Bearer ${token}` },
  });
  if (existing.status === 200) {
    console.log('exists', property.name);
    continue;
  }
  if (existing.status !== 404) {
    throw new Error(`GET ${property.name} ${existing.status} ${await existing.text()}`);
  }
  await hs('POST', '/crm/v3/properties/contacts', property);
  console.log('created', property.name);
}
console.log('properties only. no contact values were written.');
