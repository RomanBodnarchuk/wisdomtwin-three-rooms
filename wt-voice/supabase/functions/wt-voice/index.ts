// WisdomTwin outbound voice backend (Supabase Edge Function, Deno).
// Deploy with --no-verify-jwt: every route authenticates itself (trigger secret, HMAC, Twilio signature,
// or a conversation that this backend itself dialed).
//
// Routes (all under /functions/v1/wt-voice/):
//   POST dial                 one consent-gated call     auth: x-wt-trigger-secret
//   POST opt-out              agent tool                 attributed to our dial or the live conversation
//   POST scheduling-request   agent tool                 auth: conversation dialed by us
//   POST outcome              agent tool                 auth: conversation dialed by us
//   POST elevenlabs-webhook   post-call + AMD events     auth: HMAC + replay window + idempotency
//   POST inbound-optout       Twilio voice webhook       auth: X-Twilio-Signature
//   GET  health
import { createClient } from 'npm:@supabase/supabase-js@2';
import { CONTACT_PROPS, evaluateEligibility, dialModeGate, policyFromEnv, normalizePhone } from '../_shared/eligibility.js';
import { verifyElevenLabs, verifyTwilio, timingSafeEqual, sha256Hex } from '../_shared/security.js';

const env = Deno.env.toObject();
const db = createClient(env.SUPABASE_URL, env.SUPABASE_SERVICE_ROLE_KEY, { auth: { persistSession: false } });
const bg = (p: PromiseLike<unknown>) => {
  const guarded = Promise.resolve(p).catch((e) => console.error("[bg]", e?.message ?? e));
  // @ts-ignore EdgeRuntime is provided by the Supabase runtime
  if (globalThis.EdgeRuntime?.waitUntil) globalThis.EdgeRuntime.waitUntil(guarded);
};
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } });

// ---------------- HubSpot ----------------
async function hs(method: string, path: string, body?: unknown) {
  const r = await fetch('https://api.hubapi.com' + path, {
    method,
    headers: { authorization: `Bearer ${env.HUBSPOT_SERVER_TOKEN}`, 'content-type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) throw new Error(`HubSpot ${method} ${path} ${r.status} ${await r.text()}`);
  return r.status === 204 ? null : r.json();
}
const getContact = (id: string) =>
  hs('GET', `/crm/v3/objects/contacts/${encodeURIComponent(id)}?properties=${CONTACT_PROPS.join(',')}`);
const setOptOut = (id: string) =>
  hs('PATCH', `/crm/v3/objects/contacts/${encodeURIComponent(id)}`, { properties: { voice_opt_out: 'true', voice_consent: 'false' } });
const addNote = (id: string, text: string) =>
  hs('POST', '/crm/v3/objects/notes', {
    properties: { hs_timestamp: new Date().toISOString(), hs_note_body: text },
    associations: [{ to: { id }, types: [{ associationCategory: 'HUBSPOT_DEFINED', associationTypeId: 202 }] }],
  });
const addTask = (id: string, subject: string, body: string) =>
  hs('POST', '/crm/v3/objects/tasks', {
    properties: { hs_timestamp: new Date().toISOString(), hs_task_subject: subject, hs_task_body: body,
      hs_task_status: 'NOT_STARTED', hs_task_priority: 'HIGH' },
    associations: [{ to: { id }, types: [{ associationCategory: 'HUBSPOT_DEFINED', associationTypeId: 204 }] }],
  });

// ---------------- ElevenLabs / Twilio ----------------
async function el(method: string, path: string, body?: unknown) {
  const r = await fetch('https://api.elevenlabs.io' + path, {
    method, headers: { 'xi-api-key': env.ELEVENLABS_API_KEY, 'content-type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  const t = await r.text();
  if (!r.ok) throw new Error(`ElevenLabs ${method} ${path} ${r.status} ${t}`);
  return t ? JSON.parse(t) : null;
}
async function twilioHangup(callSid: string) {
  const auth = btoa(`${env.TWILIO_API_KEY}:${env.TWILIO_API_SECRET}`);
  const r = await fetch(`https://api.twilio.com/2010-04-01/Accounts/${env.TWILIO_ACCOUNT_SID}/Calls/${callSid}.json`, {
    method: 'POST', headers: { authorization: `Basic ${auth}`, 'content-type': 'application/x-www-form-urlencoded' },
    body: 'Status=completed',
  });
  if (!r.ok) throw new Error(`Twilio hangup ${r.status} ${await r.text()}`);
}

// ---------------- Durable state ----------------
const ledger = (row: Record<string, unknown>) => db.from('wt_voice_ledger').insert(row).then(({ error }) => { if (error) throw error; });
async function isSuppressed(numberHash: string, contactId: string) {
  const { data, error } = await db.from('wt_voice_suppression').select('id')
    .or(`number_sha256.eq.${numberHash},hubspot_contact_id.eq.${contactId}`).limit(1);
  if (error) throw error; // fail closed: an error blocks dialing
  return (data?.length ?? 0) > 0;
}
async function suppress(row: { number_sha256?: string | null; hubspot_contact_id?: string | null; source: string; conversation_id?: string }) {
  const { error } = await db.from('wt_voice_suppression').insert(row);
  if (error) throw error;
}
async function decisionFor(conversationId: string) {
  const { data } = await db.from('wt_voice_dial_decisions').select('*').eq('conversation_id', conversationId).maybeSingle();
  return data;
}
const releaseLock = (conversationId?: string) =>
  conversationId ? db.from('wt_voice_dial_lock').delete().eq('conversation_id', conversationId) : Promise.resolve();

// ---------------- Routes ----------------
async function dial(req: Request) {
  if (!timingSafeEqual(req.headers.get('x-wt-trigger-secret') ?? '', env.WT_TRIGGER_SECRET ?? '\u0000'))
    return json({ error: 'unauthorized' }, 401);
  const { hubspot_contact_id: contactId } = await req.json().catch(() => ({}));
  if (typeof contactId !== 'string' || !/^\d{1,20}$/.test(contactId)) return json({ error: 'numeric hubspot_contact_id required' }, 400);

  // Release gate: the live agent must be exactly the version that passed all tests.
  const agent = await el('GET', `/v1/convai/agents/${env.WT_AGENT_ID}`);
  const releaseOk = !!env.WT_RELEASED_AGENT_VERSION && agent?.version_id === env.WT_RELEASED_AGENT_VERSION;

  const contact = await getContact(contactId);
  const props = contact?.properties ?? {};
  const to = normalizePhone(props.mobilephone || props.phone);
  const numberHash = await sha256Hex(to);
  const suppressed = await isSuppressed(numberHash, contactId);
  const policy = policyFromEnv(env);
  const result = evaluateEligibility(props, policy, { now: new Date(), suppressed });
  let gate = dialModeGate(env, result);
  if (gate.ok && !releaseOk) gate = { ok: false, mode: gate.mode, reason: 'agent version has not passed release tests' };

  const snapshot = Object.fromEntries(CONTACT_PROPS.filter((k) => k.startsWith('voice_')).map((k) => [k, props[k] ?? null]));
  const { data: decision, error } = await db.from('wt_voice_dial_decisions').insert({
    hubspot_contact_id: contactId, to_number_sha256: numberHash, dial_mode: gate.mode,
    eligible: result.eligible, gate_ok: gate.ok, failures: result.failures, checked: result.checked,
    policy, consent_snapshot: snapshot, agent_id: env.WT_AGENT_ID, agent_version_id: agent?.version_id ?? null,
  }).select('id').single();
  if (error) throw error;

  if (!gate.ok) {
    await ledger({ event: 'dial_refused', hubspot_contact_id: contactId, detail: { decision_id: decision.id, reason: gate.reason, failures: result.failures } });
    return json({ dialed: false, decision_id: decision.id, reason: gate.reason, failures: result.failures }, 409);
  }

  const { data: locked, error: lockErr } = await db.rpc('wt_voice_try_lock', { p_decision_id: decision.id });
  if (lockErr) throw lockErr;
  if (!locked) {
    await ledger({ event: 'dial_refused', hubspot_contact_id: contactId, detail: { decision_id: decision.id, reason: 'another call is active' } });
    return json({ dialed: false, decision_id: decision.id, reason: 'another call is active' }, 409);
  }

  // Test mode: one call per operator-issued grant. Consumed atomically after the lock, before dialing.
  if (gate.mode === 'test') {
    const { data: grantId, error: grantErr } = await db.rpc('wt_voice_consume_test_grant', { p_number_sha256: numberHash, p_decision_id: decision.id });
    if (grantErr || !grantId) {
      await db.from('wt_voice_dial_lock').delete().eq('decision_id', decision.id);
      await ledger({ event: 'dial_refused', hubspot_contact_id: contactId, detail: { decision_id: decision.id, reason: 'no unused test grant', error: grantErr?.message ?? null } });
      return json({ dialed: false, decision_id: decision.id, reason: 'no unused test grant for this number' }, 409);
    }
  }

  try {
    const res = await el('POST', '/v1/convai/twilio/outbound-call', {
      agent_id: env.WT_AGENT_ID,
      agent_phone_number_id: env.WT_AGENT_PHONE_NUMBER_ID,
      to_number: to,
      call_recording_enabled: false,
      conversation_initiation_client_data: {
        user_id: contactId,
        dynamic_variables: {
          contact_name: props.firstname || 'there',
          company: props.company || 'your organization',
          callback_number: env.WT_CALLBACK_SPOKEN,
          hubspot_contact_id: contactId,
        },
      },
      telephony_call_config: {
        ringing_timeout_secs: 30,
        twilio_call_recording_enabled: false,
        twilio_machine_detection: { mode: 'enable' }, // early verdict; machines are hung up (voicemail is off)
      },
    });
    const u1 = await db.from('wt_voice_dial_decisions').update({ conversation_id: res.conversation_id, call_sid: res.callSid }).eq('id', decision.id);
    const u2 = await db.from('wt_voice_dial_lock').update({ conversation_id: res.conversation_id }).eq('id', 1);
    if (u1.error || u2.error) console.error('[dial] post-dial bookkeeping failed', u1.error?.message, u2.error?.message);
    await ledger({ event: 'call_placed', hubspot_contact_id: contactId, conversation_id: res.conversation_id, call_sid: res.callSid, detail: { decision_id: decision.id, mode: gate.mode } });
    return json({ dialed: true, decision_id: decision.id, conversation_id: res.conversation_id, callSid: res.callSid });
  } catch (e) {
    await db.from('wt_voice_dial_lock').delete().eq('decision_id', decision.id);
    await ledger({ event: 'dial_error', hubspot_contact_id: contactId, detail: { decision_id: decision.id, error: String(e) } });
    return json({ dialed: false, decision_id: decision.id, reason: 'outbound call request failed' }, 502);
  }
}

// Agent tools are trusted only for conversations this backend dialed, with a matching contact.
async function ownedConversation(conversationId: string, contactId: string) {
  const d = conversationId ? await decisionFor(conversationId) : null;
  return d && d.hubspot_contact_id === String(contactId) && d.gate_ok ? d : null;
}

async function optOut(req: Request) {
  const { conversation_id, hubspot_contact_id } = await req.json().catch(() => ({}));
  if (typeof conversation_id !== 'string' || !conversation_id) return json({ ok: false }, 400);
  // Attribute the request before writing, so an unauthenticated caller cannot suppress arbitrary contacts.
  // 1) our own dial record; 2) fallback for the first seconds of a call: the live conversation on our agent.
  let d = await decisionFor(conversation_id);
  let contact = d?.hubspot_contact_id ?? null;
  if (!d) {
    const conv = await el('GET', `/v1/convai/conversations/${encodeURIComponent(conversation_id)}`).catch(() => null);
    if (conv?.agent_id !== env.WT_AGENT_ID) return json({ ok: false }, 404);
    contact = conv?.conversation_initiation_client_data?.dynamic_variables?.hubspot_contact_id ?? null;
  }
  if (hubspot_contact_id && contact && String(hubspot_contact_id) !== String(contact)) return json({ ok: false }, 409);
  await suppress({ hubspot_contact_id: contact, number_sha256: d?.to_number_sha256 ?? null, source: 'in_call', conversation_id });
  bg((async () => {
    await ledger({ event: 'opt_out', hubspot_contact_id: contact, conversation_id, opted_out: true, detail: { source: 'in_call', attributed_by: d ? 'dial_record' : 'live_conversation' } });
    if (contact) await setOptOut(String(contact));
  })());
  return json({ ok: true });
}

async function schedulingRequest(req: Request) {
  const { conversation_id, hubspot_contact_id } = await req.json().catch(() => ({}));
  const d = await ownedConversation(conversation_id, hubspot_contact_id);
  if (!d) return json({ ok: false });
  try {
    // Roman sends the link himself. No agent sends email (standing rule).
    await addTask(String(hubspot_contact_id), 'Voice follow-up: send 20-minute scheduling link',
      `Contact agreed on voice call ${conversation_id} to a 20-minute call with Roman. Send the scheduling link personally.`);
    await ledger({ event: 'scheduling_requested', hubspot_contact_id, conversation_id });
    return json({ ok: true });
  } catch (e) {
    await ledger({ event: 'scheduling_request_failed', hubspot_contact_id, conversation_id, detail: { error: String(e) } });
    return json({ ok: false });
  }
}

async function outcome(req: Request) {
  const { outcome, conversation_id, hubspot_contact_id } = await req.json().catch(() => ({}));
  const d = await ownedConversation(conversation_id, hubspot_contact_id);
  if (!d) return json({ ok: false });
  bg(ledger({ event: 'in_call_outcome', hubspot_contact_id, conversation_id, outcome }));
  return json({ ok: true });
}

async function elevenlabsWebhook(req: Request) {
  const raw = await req.text();
  const v = await verifyElevenLabs(raw, req.headers.get('elevenlabs-signature') ?? '', env.ELEVENLABS_WEBHOOK_SECRET);
  if (!v.ok) return json({ error: 'invalid signature' }, 401);
  const event = JSON.parse(raw);
  const d = event.data ?? {};
  if (d.agent_id && d.agent_id !== env.WT_AGENT_ID) return json({ ignored: true });

  const key = await sha256Hex(`${event.type}|${d.conversation_id ?? ''}|${event.event_timestamp ?? v.t}`);
  const { error: dupErr } = await db.from('wt_voice_webhook_events').insert({ event_key: key, event_type: event.type, conversation_id: d.conversation_id ?? null });
  if (dupErr) return json({ duplicate: true }); // unique violation = already processed

  try {
    await processEvent(event, d);
  } catch (e) {
    await db.from('wt_voice_webhook_events').delete().eq('event_key', key); // allow a retry to reprocess
    throw e;
  }
  return json({ received: true });
}

// deno-lint-ignore no-explicit-any
async function processEvent(event: any, d: any) {
  const decision = d.conversation_id ? await decisionFor(d.conversation_id) : null;
  const contactId = decision?.hubspot_contact_id ?? d.conversation_initiation_client_data?.dynamic_variables?.hubspot_contact_id;

  if (event.type === 'post_call_transcription') {
    const dc = d.analysis?.data_collection_results ?? {};
    const out = dc.call_outcome?.value ?? 'unknown';
    const optedOut = dc.opted_out?.value === true || dc.opted_out?.value === 'true';
    if (optedOut) {
      await suppress({ hubspot_contact_id: contactId ?? null, number_sha256: decision?.to_number_sha256 ?? null, source: 'post_call', conversation_id: d.conversation_id });
      if (contactId) bg(setOptOut(contactId));
    }
    await ledger({ event: 'post_call', hubspot_contact_id: contactId, conversation_id: d.conversation_id, outcome: out, opted_out: optedOut,
      detail: { decision_id: decision?.id ?? null, eligible_at_dial: decision?.gate_ok ?? null, duration_secs: d.metadata?.call_duration_secs,
        termination_reason: d.metadata?.termination_reason, ai_disclosure_given: dc.ai_disclosure_given?.value ?? null } });
    if (contactId) bg(addNote(contactId, `WisdomTwin voice call ${d.conversation_id}. Outcome: ${out}. Opted out: ${optedOut}. ` +
      `Eligibility decision #${decision?.id ?? 'none'} recorded at dial time.`));
    await releaseLock(d.conversation_id);
  } else if (event.type === 'call_initiation_failure') {
    await ledger({ event: 'call_failed', hubspot_contact_id: contactId, conversation_id: d.conversation_id, detail: { reason: d.failure_reason ?? null } });
    await releaseLock(d.conversation_id);
  } else if (event.type === 'answering_machine_detection') {
    const verdict = JSON.stringify(d).match(/"(?:answered_by|AnsweredBy|result|verdict)"\s*:\s*"([^"]+)"/)?.[1] ?? 'unknown';
    const machine = /machine|fax/i.test(verdict);
    if (machine && decision?.call_sid) bg(twilioHangup(decision.call_sid));
    await ledger({ event: 'amd', hubspot_contact_id: contactId, conversation_id: d.conversation_id, call_sid: decision?.call_sid ?? null,
      outcome: machine ? 'machine' : verdict, detail: { hung_up: machine && !!decision?.call_sid } });
  }
}

async function inboundOptOut(req: Request) {
  const form = Object.fromEntries(new URLSearchParams(await req.text()));
  const url = `${env.WT_PUBLIC_BASE_URL}/inbound-optout`;
  if (!(await verifyTwilio(url, form, req.headers.get('x-twilio-signature') ?? '', env.TWILIO_AUTH_TOKEN)))
    return new Response('forbidden', { status: 403 });
  const from = normalizePhone(form.From);
  if (from) {
    await suppress({ number_sha256: await sha256Hex(from), source: 'inbound_line' });
    bg(ledger({ event: 'opt_out', opted_out: true, detail: { source: 'inbound_line' } }));
  }
  const twiml = `<?xml version="1.0" encoding="UTF-8"?><Response><Say>` +
    `You have been opted out of calls from WisdomTwin dot A I. You will not receive another call from us. Goodbye.` +
    `</Say><Hangup/></Response>`;
  return new Response(twiml, { headers: { 'content-type': 'text/xml' } });
}

Deno.serve(async (req) => {
  const route = new URL(req.url).pathname.split('/').filter(Boolean).pop();
  try {
    if (req.method === 'GET' && route === 'health') return json({ ok: true });
    if (req.method !== 'POST') return json({ error: 'not found' }, 404);
    switch (route) {
      case 'dial': return await dial(req);
      case 'opt-out': return await optOut(req);
      case 'scheduling-request': return await schedulingRequest(req);
      case 'outcome': return await outcome(req);
      case 'elevenlabs-webhook': return await elevenlabsWebhook(req);
      case 'inbound-optout': return await inboundOptOut(req);
      default: return json({ error: 'not found' }, 404);
    }
  } catch (e) {
    console.error(`[${route}]`, e);
    return json({ error: 'internal error' }, 500);
  }
});
