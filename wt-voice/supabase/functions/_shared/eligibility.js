// AI_CALL_ELIGIBLE: pure, dependency-free, runs in Deno (edge function) and Node (unit tests).
// Default is NOT eligible. Every check must pass; every failure is reported.
// Policy inputs come from env (see policyFromEnv); contact evidence comes from HubSpot properties.

export const CONTACT_PROPS = [
  'firstname', 'lastname', 'company', 'phone', 'mobilephone',
  // consent evidence
  'voice_consent', 'voice_consent_phone', 'voice_consent_name', 'voice_consent_at', 'voice_consent_method',
  'voice_consent_text', 'voice_consent_evidence_ref', 'voice_consent_entity', 'voice_consent_purpose',
  // suppression
  'voice_opt_out', 'voice_dnc_listed', 'voice_dnc_checked_at',
  // jurisdiction, local time, campaign, segment
  'voice_jurisdiction', 'voice_timezone', 'voice_campaign_id', 'voice_segment',
];

const E164 = /^\+[1-9]\d{7,14}$/;
const METHODS = new Set(['web_form', 'email_reply_manual']);
const DAY = 86400000;

// Conservative combined window for CA and US until counsel sets per-jurisdiction rules:
// weekdays 09:00-21:00, weekends 10:00-18:00, recipient local time.
const DEFAULT_WINDOWS = { weekday: [9 * 60, 21 * 60], weekend: [10 * 60, 18 * 60] };

export function normalizePhone(p) {
  return String(p || '').replace(/[^\d+]/g, '');
}

function localMinutes(now, tz) {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: tz, hour12: false, weekday: 'short', hour: '2-digit', minute: '2-digit',
  }).formatToParts(now);
  const get = (t) => parts.find((x) => x.type === t)?.value;
  const h = Number(get('hour')) % 24;
  return { minutes: h * 60 + Number(get('minute')), weekend: ['Sat', 'Sun'].includes(get('weekday')) };
}

export function policyFromEnv(env) {
  const list = (k) => String(env[k] || '').split(',').map((s) => s.trim()).filter(Boolean);
  return {
    callingEntity: env.WT_CALLING_ENTITY || '',
    purpose: env.WT_CALL_PURPOSE || '',
    allowedJurisdictions: list('WT_ALLOWED_JURISDICTIONS'),
    allowedSegments: list('WT_ALLOWED_SEGMENTS'),
    campaignId: env.WT_CAMPAIGN_ID || '',
    campaignApproved: env.WT_CAMPAIGN_APPROVED === 'true',
    consentMaxAgeDays: Number(env.WT_CONSENT_MAX_AGE_DAYS || 365),
    dncMaxAgeDays: Number(env.WT_DNC_MAX_AGE_DAYS || 31),
  };
}

/**
 * @param {object} props      HubSpot contact properties (strings)
 * @param {object} policy     from policyFromEnv
 * @param {object} ctx        { now: Date, suppressed: boolean (from the durable suppression table) }
 * @returns {{eligible: boolean, to: string, failures: string[], checked: string[]}}
 */
export function evaluateEligibility(props, policy, ctx) {
  const p = props || {};
  const now = ctx.now || new Date();
  const failures = [];
  const checked = [];
  const need = (name, ok, why) => { checked.push(name); if (!ok) failures.push(`${name}: ${why}`); };

  const to = normalizePhone(p.mobilephone || p.phone);
  need('phone_e164', E164.test(to), `dial number not E.164 (${to || 'empty'})`);

  // Consent evidence
  need('consent_flag', p.voice_consent === 'true', `voice_consent=${p.voice_consent ?? 'unset'}`);
  need('consent_number_match', normalizePhone(p.voice_consent_phone) === to && to !== '',
    'consented number does not match dial number');
  need('consent_who', !!(p.voice_consent_name || '').trim(), 'no record of who consented');
  const at = Date.parse(p.voice_consent_at || '');
  need('consent_when', Number.isFinite(at) && at <= now.getTime(), 'consent timestamp missing or in the future');
  need('consent_age', Number.isFinite(at) && now.getTime() - at <= policy.consentMaxAgeDays * DAY,
    `consent older than ${policy.consentMaxAgeDays} days`);
  need('consent_method', METHODS.has(p.voice_consent_method), `method=${p.voice_consent_method ?? 'unset'}`);
  need('consent_wording', (p.voice_consent_text || '').trim().length >= 40, 'accepted wording not stored');
  need('consent_evidence_ref', !!(p.voice_consent_evidence_ref || '').trim(), 'no evidence reference');
  need('consent_entity', !!policy.callingEntity && p.voice_consent_entity === policy.callingEntity,
    'consent not given to this calling entity');
  need('consent_purpose', !!policy.purpose && String(p.voice_consent_purpose || '').split(/[;,]/).map((s) => s.trim()).includes(policy.purpose),
    'consent does not cover this purpose');

  // Suppression
  need('not_opted_out', p.voice_opt_out !== 'true', 'contact opted out');
  need('not_suppressed', ctx.suppressed === false, 'number or contact is on the suppression list');
  need('dnc_clear', p.voice_dnc_listed === 'false', `voice_dnc_listed=${p.voice_dnc_listed ?? 'unset'}`);
  const dncAt = Date.parse(p.voice_dnc_checked_at || '');
  need('dnc_fresh', Number.isFinite(dncAt) && now.getTime() - dncAt <= policy.dncMaxAgeDays * DAY,
    `DNC check missing or older than ${policy.dncMaxAgeDays} days`);

  // Jurisdiction
  const j = p.voice_jurisdiction || '';
  need('jurisdiction_allowed', policy.allowedJurisdictions.includes(j), `jurisdiction ${j || 'unset'} not allowed`);
  const nanp = to.startsWith('+1');
  need('jurisdiction_matches_number', (/^(US|CA)-/.test(j) ? nanp : !nanp) && j !== '', 'jurisdiction does not match number');

  // Local time
  let tzOk = false;
  try { if (p.voice_timezone) { localMinutes(now, p.voice_timezone); tzOk = true; } } catch { tzOk = false; }
  need('timezone_known', tzOk, `timezone ${p.voice_timezone || 'unset'} invalid`);
  if (tzOk) {
    const { minutes, weekend } = localMinutes(now, p.voice_timezone);
    const [a, b] = weekend ? DEFAULT_WINDOWS.weekend : DEFAULT_WINDOWS.weekday;
    need('local_time_window', minutes >= a && minutes < b, 'outside permitted local calling hours');
  }

  // Campaign authorization and segment
  need('campaign_approved', policy.campaignApproved && !!policy.campaignId, 'campaign not approved');
  need('campaign_match', !!policy.campaignId && p.voice_campaign_id === policy.campaignId, 'contact not in this campaign');
  need('segment_allowed', policy.allowedSegments.includes(p.voice_segment || ''), `segment ${p.voice_segment || 'unset'} not allowed`);

  return { eligible: failures.length === 0, to, failures, checked };
}

/**
 * Dial-mode gate, applied after eligibility.
 * disabled (default): nothing dials. test: eligible AND number on allowlist AND unexpired test window;
 * the backend additionally consumes one single-use grant per call (wt_voice_consume_test_grant).
 * production: eligible AND WT_PRODUCTION_ENABLED=true.
 */
export function dialModeGate(env, result, now = new Date()) {
  const mode = env.WT_DIAL_MODE || 'disabled';
  if (!result.eligible) return { ok: false, mode, reason: 'AI_CALL_ELIGIBLE=false' };
  if (mode === 'test') {
    const allow = String(env.WT_TEST_ALLOWLIST || '').split(',').map(normalizePhone).filter(Boolean);
    if (!allow.includes(result.to)) return { ok: false, mode, reason: 'number not on test allowlist' };
    const until = Date.parse(env.WT_TEST_AUTHORIZED_UNTIL || '');
    if (!Number.isFinite(until) || until < now.getTime()) return { ok: false, mode, reason: 'test authorization missing or expired' };
    return { ok: true, mode, reason: 'test allowlist' };
  }
  if (mode === 'production') {
    if (env.WT_PRODUCTION_ENABLED !== 'true') return { ok: false, mode, reason: 'production not enabled' };
    return { ok: true, mode, reason: 'production' };
  }
  return { ok: false, mode: 'disabled', reason: 'dialing disabled' };
}
