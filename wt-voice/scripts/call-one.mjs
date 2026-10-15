// Ask the backend to place ONE call. All checks run server-side; this script cannot bypass them.
// Usage: op run --env-file=scripts/env.op -- node scripts/call-one.mjs <hubspot_contact_id>
const id = process.argv[2];
if (!id || process.argv.length > 3 || !/^\d+$/.test(id)) {
  console.error('Usage: node scripts/call-one.mjs <numeric hubspot_contact_id>   (one contact, no batch mode)');
  process.exit(2);
}
const r = await fetch(`${process.env.WT_BACKEND_URL}/dial`, {
  method: 'POST',
  headers: { 'content-type': 'application/json', 'x-wt-trigger-secret': process.env.WT_TRIGGER_SECRET },
  body: JSON.stringify({ hubspot_contact_id: id }),
});
console.log(r.status, JSON.stringify(await r.json(), null, 2));
process.exit(r.ok ? 0 : 1);
