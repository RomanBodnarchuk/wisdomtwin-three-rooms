// Deterministic pre-push gate for the agent config. Exit 1 on any failure.
// This validates STORED text only. Runtime enforcement is the blocking custom guardrail plus the 7 remote tests.
import fs from 'node:fs';
const cfg = JSON.parse(fs.readFileSync('agent_configs/WisdomTwinBuyerTwin.json', 'utf8'));
const cc = cfg.conversation_config, a = cc.agent, ps = cfg.platform_settings;
const prompt = a.prompt.prompt;
const quoted = [...prompt.matchAll(/"([^"]+)"/g)].map((m) => m[1]); // every exact line the agent is told to say
const spoken = { max_conversation_duration_message: a.max_conversation_duration_message, ...Object.fromEntries(quoted.map((q, i) => [`scripted_line_${i + 1}`, q])) };
const BANNED = [/\bclone/i, /digital twin of/i, /wisdomclone/i, /10x club/i, /\bn5r\b/i, /valuation/i, /\bcap\b/i,
  /revenue/i, /\busers?\b/i, /\bcustomers?\b/i, /\bzoom\b/i, /\bfirst\b/i, /\bonly\b/i, /\b3x\b/i, /\bsafe\b/i,
  /\braise\b/i, /investor/i, /pricing|\$\d/i, /https?:|www\.|dot com/i, /\bsent\b|\bemailed\b|\bbooked\b/i, /—/];
const errs = [];
for (const [k, v] of Object.entries(spoken)) for (const re of BANNED) if (re.test(v)) errs.push(`${k}: banned ${re} in "${v}"`);
const check = (ok, msg) => { if (!ok) errs.push(msg); };
check(a.first_message === '', 'first_message must be empty: agent waits for a human before speaking (voicemail off)');
check(/AI voice twin/i.test(quoted.find((q) => q.startsWith('Hi {{contact_name}}')) || ''), 'opener lacks AI disclosure');
check(/opt out/i.test(a.max_conversation_duration_message), 'timeout message lacks opt-out');
check(quoted.some((q) => /opt out, say stop, or call \{\{callback_number\}\}/.test(q)), 'scripted close lacks opt-out + callback');
check(!a.prompt.built_in_tools?.voicemail_detection, 'voicemail_detection must be absent (voicemail off)');
check(cc.conversation.max_duration_seconds === 60, 'max_duration_seconds must be 60 (ElevenLabs platform minimum; the 45 s target is enforced by script length)');
check(cc.tts.voice_id === 'OtTgp0gIgmfhqSXfyakl', 'wrong voice_id');
check(ps.privacy.record_voice === false, 'record_voice must be false unless recording is approved');
check(!/recorded/i.test(prompt) || ps.privacy.record_voice === true, 'recording notice without recording');
check(ps.guardrails?.custom?.config?.configs?.some((g) => g.is_enabled && g.execution_mode === 'blocking'), 'blocking custom guardrail missing');
check(ps.call_limits?.agent_concurrency_limit === 1, 'agent_concurrency_limit must be 1');
const tools = (a.prompt.tools || []).map((t) => t.name).sort().join(',');
check(tools === 'log_outcome,record_opt_out,request_scheduling_link', `unexpected tool set: ${tools}`);
const pre = process.argv.includes('--pre-release'), rel = process.argv.includes('--release');
if (pre || rel) check(!/__[A-Z_]+__/.test(JSON.stringify(cfg)), 'unresolved __PLACEHOLDER__ in config');
if (rel) check((ps.testing?.attached_tests || []).length === 7, 'exactly 7 attached tests required');
if (errs.length) { console.error('CANON LINT FAILED\n' + errs.join('\n')); process.exit(1); }
console.log('canon-lint: pass');
