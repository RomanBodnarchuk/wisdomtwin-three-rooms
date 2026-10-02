// Regression tests for the three defects found in the 2026-09-22 preflight review.
// Run: node tests/release_regression.mjs (needs @electric-sql/pglite for test 3; no network, no secrets)
import http from 'node:http';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
let failed = 0;
const ok = (c, m) => { console.log(`${c ? 'PASS' : 'FAIL'} ${m}`); if (!c) failed++; };

// ---- Defect 1: release order. Pre-release lint must not require attached tests; release lint must. ----
{
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'wt-'));
  fs.cpSync(root, tmp, { recursive: true, filter: (s) => !s.includes('node_modules') });
  const cfgP = path.join(tmp, 'agent_configs/WisdomTwinBuyerTwin.json');
  const cfg = JSON.parse(fs.readFileSync(cfgP, 'utf8'));
  let s = JSON.stringify(cfg).replaceAll('__POST_CALL_WEBHOOK_ID__', 'wh_test').replaceAll('https://__VOICE_BACKEND_URL__', 'https://example.test/fn');
  fs.writeFileSync(cfgP, s);
  const run = (a) => spawnSync('node', ['scripts/canon-lint.mjs', a], { cwd: tmp, encoding: 'utf8' }).status;
  ok(run('--pre-release') === 0, 'fresh config (0 tests attached) passes --pre-release');
  ok(run('--release') !== 0, 'same config fails --release until 7 tests are attached');
  const c2 = JSON.parse(fs.readFileSync(cfgP, 'utf8'));
  c2.platform_settings.testing = { attached_tests: Array.from({ length: 7 }, (_, i) => ({ test_id: 't' + i })) };
  fs.writeFileSync(cfgP, JSON.stringify(c2));
  ok(run('--release') === 0, 'passes --release after 7 tests are attached');
  const order = fs.readFileSync(path.join(root, 'scripts/release.sh'), 'utf8');
  const i = (k) => order.indexOf(k);
  ok(i('--pre-release') < i('elevenlabs tests push') && i('node scripts/attach-tests.mjs') < i('canon-lint.mjs --release')
    && i('canon-lint.mjs --release') < i('elevenlabs agents push --version'), 'release.sh order: pre-lint > tests push > attach > full lint > push');
}

// ---- Defect 2: verify-release must reject runs with missing version / draft evidence. ----
async function verifyWith(runPatch, invPatch = {}) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'wt-'));
  fs.cpSync(root, tmp, { recursive: true, filter: (s) => !s.includes('node_modules') });
  const ids = Array.from({ length: 7 }, (_, i) => 'test_' + i);
  fs.writeFileSync(path.join(tmp, 'agents.json'), JSON.stringify({ agents: [{ config: 'agent_configs/WisdomTwinBuyerTwin.json', id: 'agent_x' }] }));
  fs.writeFileSync(path.join(tmp, 'tests.json'), JSON.stringify({ tests: ids.map((id) => ({ config: 'x', id })) }));
  const cfgP = path.join(tmp, 'agent_configs/WisdomTwinBuyerTwin.json');
  const cfg = JSON.parse(fs.readFileSync(cfgP, 'utf8'));
  cfg.platform_settings.testing = { attached_tests: ids.map((test_id) => ({ test_id })) };
  fs.writeFileSync(cfgP, JSON.stringify(cfg));
  const runs = ids.map((id) => ({ test_id: id, test_name: id, status: 'passed', test_run_id: 'r' + id, agent_id: 'agent_x', version_id: 'v1', ran_against_draft: false, ...runPatch }));
  const srv = http.createServer((req, res) => {
    res.setHeader('content-type', 'application/json');
    if (req.url === '/v1/convai/agents/agent_x') return res.end(JSON.stringify({ version_id: 'v1', platform_settings: cfg.platform_settings, conversation_config: {} }));
    if (req.url.endsWith('/run-tests')) return res.end(JSON.stringify({ id: 'inv1' }));
    if (req.url === '/v1/convai/test-invocations/inv1') return res.end(JSON.stringify({ id: 'inv1', version_id: 'v1', ran_against_draft: false, ...invPatch, test_runs: runs }));
    res.statusCode = 404; res.end('{}');
  });
  await new Promise((r) => srv.listen(0, r));
  const env = { ...process.env, ELEVENLABS_API_KEY: 'x', ELEVENLABS_BASE_URL: `http://127.0.0.1:${srv.address().port}` };
  const out = await new Promise((resolve) => {
    import('node:child_process').then(({ spawn }) => {
      const c = spawn('node', ['scripts/verify-release.mjs'], { cwd: tmp, env });
      let err = ''; c.stderr.on('data', (d) => (err += d));
      c.on('close', (code) => resolve({ code, err }));
    });
  });
  srv.close();
  return out;
}
{
  ok((await verifyWith({})).code === 0, 'complete, matching evidence passes');
  const noVer = { version_id: undefined }; ok((await verifyWith(noVer)).code !== 0, 'run with MISSING version_id is rejected');
  ok((await verifyWith({ ran_against_draft: undefined })).code !== 0, 'run with MISSING ran_against_draft is rejected');
  ok((await verifyWith({ version_id: 'v0' })).code !== 0, 'run on a different version is rejected');
  ok((await verifyWith({ ran_against_draft: true })).code !== 0, 'run against a draft is rejected');
  ok((await verifyWith({}, { version_id: undefined })).code !== 0, 'invocation with MISSING version_id is rejected');
  ok((await verifyWith({ status: 'failed' })).code !== 0, 'a failed run is rejected');
}

// ---- Defect 3: a test grant authorizes exactly one call. ----
{
  let PGlite;
  try { ({ PGlite } = await import('@electric-sql/pglite')); } catch { console.log('SKIP grant test (npm i @electric-sql/pglite to run)'); }
  if (PGlite) {
    const db = new PGlite();
    await db.exec('create role anon; create role authenticated; create role service_role;');
    await db.exec(fs.readFileSync(path.join(root, 'supabase/migrations/20260922000000_wt_voice.sql'), 'utf8'));
    const dec = async () => (await db.query("insert into wt_voice_dial_decisions (hubspot_contact_id,to_number_sha256,dial_mode,eligible,gate_ok,failures,checked,policy,consent_snapshot,agent_id) values ('1','h','test',true,true,'[]','[]','{}','{}','a') returning id")).rows[0].id;
    const consume = async (h) => (await db.query('select wt_voice_consume_test_grant($1,$2) as g', [h, await dec()])).rows[0].g;
    await db.query("insert into wt_voice_test_grants (number_sha256, expires_at, authorized_by) values ('HASH', now() + interval '1 hour', 'Roman')");
    ok((await consume('HASH')) !== null, 'first call consumes the grant');
    ok((await consume('HASH')) === null, 'second call with the same grant is refused');
    ok((await consume('OTHER')) === null, 'a different number has no grant');
    await db.query("insert into wt_voice_test_grants (number_sha256, expires_at, authorized_by) values ('HASH', now() - interval '1 minute', 'Roman')");
    ok((await consume('HASH')) === null, 'an expired grant is refused');
  }
}
console.log(failed ? `\n${failed} FAILED` : '\nALL PASS');
process.exit(failed ? 1 : 0);
