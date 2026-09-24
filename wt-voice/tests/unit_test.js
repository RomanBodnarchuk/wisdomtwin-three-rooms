// Run: deno test tests/   (no network, no secrets)
import { evaluateEligibility, dialModeGate, policyFromEnv } from '../supabase/functions/_shared/eligibility.js';
import { verifyElevenLabs, verifyTwilio } from '../supabase/functions/_shared/security.js';

const assert = (c, m) => { if (!c) throw new Error(m); };
const env = { WT_CALLING_ENTITY: 'WisdomTwin, Inc.', WT_CALL_PURPOSE: 'product_follow_up', WT_ALLOWED_JURISDICTIONS: 'CA-ON',
  WT_ALLOWED_SEGMENTS: 'regulated_enterprise', WT_CAMPAIGN_ID: 'wt-voice-pilot-1', WT_CAMPAIGN_APPROVED: 'true' };
const policy = policyFromEnv(env);
const now = new Date('2026-09-23T14:00:00Z'); // Wednesday 10:00 in Toronto
const good = {
  firstname: 'Dana', mobilephone: '+1 (416) 555-0100', voice_consent: 'true', voice_consent_phone: '+14165550100',
  voice_consent_name: 'Dana Example', voice_consent_at: '2026-09-20T15:00:00Z', voice_consent_method: 'web_form',
  voice_consent_text: 'Yes, WisdomTwin.ai may call me at the number above for a short follow-up using an AI-generated voice.',
  voice_consent_evidence_ref: 'hubspot-form-submission:abc123', voice_consent_entity: 'WisdomTwin, Inc.',
  voice_consent_purpose: 'product_follow_up', voice_opt_out: 'false', voice_dnc_listed: 'false',
  voice_dnc_checked_at: '2026-09-21T00:00:00Z', voice_jurisdiction: 'CA-ON', voice_timezone: 'America/Toronto',
  voice_campaign_id: 'wt-voice-pilot-1', voice_segment: 'regulated_enterprise',
};
const ev = (p, extra = {}) => evaluateEligibility(p, policy, { now, suppressed: false, ...extra });

Deno.test('fully evidenced contact is eligible', () => {
  const r = ev(good); assert(r.eligible, r.failures.join('; ')); assert(r.to === '+14165550100', r.to);
});
Deno.test('default (empty contact) is not eligible', () => { assert(!ev({}).eligible, 'empty contact passed'); });
Deno.test('boolean consent without evidence fails', () => {
  const r = ev({ ...good, voice_consent_evidence_ref: '', voice_consent_text: '' });
  assert(!r.eligible && r.failures.some((f) => f.startsWith('consent_evidence_ref')), 'evidence not enforced');
});
Deno.test('consent for a different number fails', () => { assert(!ev({ ...good, voice_consent_phone: '+14165559999' }).eligible, 'number mismatch passed'); });
Deno.test('opt-out, suppression list, DNC listed, stale DNC each fail', () => {
  assert(!ev({ ...good, voice_opt_out: 'true' }).eligible, 'opt-out passed');
  assert(!ev(good, { suppressed: true }).eligible, 'suppressed passed');
  assert(!ev({ ...good, voice_dnc_listed: 'true' }).eligible, 'DNC listed passed');
  assert(!ev({ ...good, voice_dnc_checked_at: '2026-07-01T00:00:00Z' }).eligible, 'stale DNC passed');
});
Deno.test('jurisdiction, time window, campaign, segment each fail', () => {
  assert(!ev({ ...good, voice_jurisdiction: 'US-CA' }).eligible, 'disallowed jurisdiction passed');
  assert(!evaluateEligibility(good, policy, { now: new Date('2026-09-24T02:00:00Z'), suppressed: false }).eligible, '22:00 local passed');
  assert(!ev({ ...good, voice_campaign_id: 'other' }).eligible, 'wrong campaign passed');
  assert(!evaluateEligibility(good, { ...policy, campaignApproved: false }, { now, suppressed: false }).eligible, 'unapproved campaign passed');
  assert(!ev({ ...good, voice_segment: 'smb' }).eligible, 'wrong segment passed');
});
Deno.test('dial modes: disabled by default; test needs allowlist + unexpired authorization', () => {
  const r = ev(good);
  assert(!dialModeGate({}, r).ok, 'default mode dialed');
  assert(!dialModeGate({ WT_DIAL_MODE: 'test', WT_TEST_ALLOWLIST: '+14165550000', WT_TEST_AUTHORIZED_UNTIL: '2026-09-30T00:00:00Z' }, r, now).ok, 'non-allowlisted dialed');
  assert(!dialModeGate({ WT_DIAL_MODE: 'test', WT_TEST_ALLOWLIST: '+14165550100', WT_TEST_AUTHORIZED_UNTIL: '2026-09-01T00:00:00Z' }, r, now).ok, 'expired authorization dialed');
  assert(dialModeGate({ WT_DIAL_MODE: 'test', WT_TEST_ALLOWLIST: '+14165550100', WT_TEST_AUTHORIZED_UNTIL: '2026-09-30T00:00:00Z' }, r, now).ok, 'valid test blocked');
  assert(!dialModeGate({ WT_DIAL_MODE: 'test', WT_TEST_ALLOWLIST: '+14165550100', WT_TEST_AUTHORIZED_UNTIL: '2026-09-30T00:00:00Z' }, ev({}), now).ok, 'ineligible test dialed');
  assert(!dialModeGate({ WT_DIAL_MODE: 'production' }, r).ok, 'production without enable dialed');
});
Deno.test('ElevenLabs HMAC: valid, tampered, stale', async () => {
  const secret = 'wsec_test', body = '{"type":"post_call_transcription"}', t = Math.floor(now.getTime() / 1000);
  const k = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sig = Array.from(new Uint8Array(await crypto.subtle.sign('HMAC', k, new TextEncoder().encode(`${t}.${body}`)))).map((b) => b.toString(16).padStart(2, '0')).join('');
  assert((await verifyElevenLabs(body, `t=${t},v0=${sig}`, secret, now.getTime())).ok, 'valid rejected');
  assert(!(await verifyElevenLabs(body + ' ', `t=${t},v0=${sig}`, secret, now.getTime())).ok, 'tampered accepted');
  assert(!(await verifyElevenLabs(body, `t=${t},v0=${sig}`, secret, now.getTime() + 3600e3)).ok, 'stale accepted');
});
Deno.test('Twilio signature matches official library', async () => {
  // Expected value computed with the official twilio Node library (getExpectedTwilioSignature)
  const url = 'https://example.com/myapp';
  const params = { CallSid: 'CA1234567890ABCDE', Caller: '+12349013030', Digits: '1234', From: '+12349013030', To: '+18005551212' };
  assert(await verifyTwilio(url, params, 'NGAgWNhdnsLF8j385frvrQoi9sg=', '12345'), 'known-good signature rejected');
});
