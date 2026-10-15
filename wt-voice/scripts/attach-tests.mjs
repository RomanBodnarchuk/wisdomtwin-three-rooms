// Writes every test id from tests.json into the agent config's attached_tests.
import fs from 'node:fs';
const tests = JSON.parse(fs.readFileSync('tests.json', 'utf8')).tests.filter((t) => t.id);
if (tests.length !== 7) { console.error(`Only ${tests.length} tests have ids; need exactly 7`); process.exit(1); }
const p = 'agent_configs/WisdomTwinBuyerTwin.json';
const cfg = JSON.parse(fs.readFileSync(p, 'utf8'));
cfg.platform_settings.testing = { attached_tests: tests.map((t) => ({ test_id: t.id })) };
fs.writeFileSync(p, JSON.stringify(cfg, null, 2) + '\n');
console.log(`attached ${tests.length} tests`);
