// Runs ALL tests in tests.json against the live agent and proves they passed on the exact deployed version.
// Writes release/evidence-<version_id>.json. Exits non-zero on any gap.
// Usage: op run --env-file=scripts/env.op -- node scripts/verify-release.mjs
import fs from 'node:fs';
import crypto from 'node:crypto';
const KEY = process.env.ELEVENLABS_API_KEY;
const api = async (method, path, body) => {
  const r = await fetch((process.env.ELEVENLABS_BASE_URL || 'https://api.elevenlabs.io') + path, { method, headers: { 'xi-api-key': KEY, 'content-type': 'application/json' }, body: body && JSON.stringify(body) });
  if (!r.ok) throw new Error(`${method} ${path} ${r.status} ${await r.text()}`);
  return r.json();
};
const fail = (m) => { console.error('RELEASE VERIFICATION FAILED: ' + m); process.exit(1); };
const EXPECTED = 7;
const agentId = JSON.parse(fs.readFileSync('agents.json', 'utf8')).agents[0].id || fail('no agent id in agents.json');
const testIds = JSON.parse(fs.readFileSync('tests.json', 'utf8')).tests.map((t) => t.id).filter(Boolean);
if (testIds.length !== EXPECTED) fail(`tests.json has ${testIds.length} registered tests, expected ${EXPECTED}`);
const cfgPath = 'agent_configs/WisdomTwinBuyerTwin.json';
const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
const attached = (cfg.platform_settings.testing?.attached_tests || []).map((t) => t.test_id).sort();
if (JSON.stringify(attached) !== JSON.stringify([...testIds].sort())) fail('attached_tests do not match tests.json');

const agent = await api('GET', `/v1/convai/agents/${agentId}`);
const liveAttached = (agent.platform_settings?.testing?.attached_tests || []).map((t) => t.test_id).sort();
if (JSON.stringify(liveAttached) !== JSON.stringify([...testIds].sort())) fail('live agent attached_tests differ from tests.json');
const version = agent.version_id || fail('live agent has no version_id');

const inv = await api('POST', `/v1/convai/agents/${agentId}/run-tests`, { tests: testIds.map((test_id) => ({ test_id })) });
let status;
for (let i = 0; i < 120; i++) {
  status = await api('GET', `/v1/convai/test-invocations/${inv.id}`);
  if (!Array.isArray(status.test_runs)) fail('invocation has no test_runs');
  if (status.test_runs.every((r) => r.status !== 'pending')) break;
  await new Promise((r) => setTimeout(r, 5000));
}
if (status.test_runs.some((r) => r.status === 'pending')) fail('test runs still pending after timeout');
if (status.version_id !== version || status.ran_against_draft !== false)
  fail(`invocation version ${status.version_id ?? 'MISSING'} / draft ${status.ran_against_draft ?? 'MISSING'} does not match live ${version}`);
const runs = status.test_runs;
if (runs.length !== EXPECTED) fail(`${runs.length} runs executed, expected ${EXPECTED}`);
const ranIds = runs.map((r) => r.test_id).sort();
if (JSON.stringify(ranIds) !== JSON.stringify([...testIds].sort())) fail('executed test set differs from registered set');
for (const r of runs) {
  if (r.status !== 'passed') fail(`${r.test_name}: ${r.status}`);
  // Evidence must be explicit: a missing field is a failure, not a pass.
  if (typeof r.version_id !== 'string' || r.version_id !== version) fail(`${r.test_name}: run version ${r.version_id ?? 'MISSING'}, live is ${version}`);
  if (r.ran_against_draft !== false) fail(`${r.test_name}: ran_against_draft is ${r.ran_against_draft ?? 'MISSING'}, must be false`);
  if (r.agent_id !== agentId) fail(`${r.test_name}: ran on agent ${r.agent_id ?? 'MISSING'}`);
}
const evidence = {
  agent_id: agentId, version_id: version, invocation_id: inv.id, verified_at: new Date().toISOString(),
  config_sha256: crypto.createHash('sha256').update(fs.readFileSync(cfgPath)).digest('hex'),
  llm: agent.conversation_config?.agent?.prompt?.llm, tts_model: agent.conversation_config?.tts?.model_id,
  runs: runs.map((r) => ({ test_id: r.test_id, name: r.test_name, status: r.status, test_run_id: r.test_run_id, version_id: r.version_id })),
};
fs.mkdirSync('release', { recursive: true });
fs.writeFileSync(`release/evidence-${version}.json`, JSON.stringify(evidence, null, 2));
console.log(version);
