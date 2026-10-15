// Signature checks. Web Crypto only, so this runs in Deno and Node 20+.

const enc = new TextEncoder();
const hex = (buf) => Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, '0')).join('');

export function timingSafeEqual(a, b) {
  const x = enc.encode(String(a)), y = enc.encode(String(b));
  let diff = x.length ^ y.length;
  for (let i = 0; i < Math.max(x.length, y.length); i++) diff |= (x[i] ?? 0) ^ (y[i] ?? 0);
  return diff === 0;
}

async function hmac(alg, key, msg) {
  const k = await crypto.subtle.importKey('raw', enc.encode(key), { name: 'HMAC', hash: alg }, false, ['sign']);
  return crypto.subtle.sign('HMAC', k, enc.encode(msg));
}

/**
 * ElevenLabs webhook: header "t=<unix>,v0=<hex hmac-sha256(secret, `${t}.${rawBody}`)>".
 * Mirrors @elevenlabs/elevenlabs-js constructEvent (2.68.0), plus a future-skew bound.
 * Returns { ok, t, reason }.
 */
export async function verifyElevenLabs(rawBody, header, secret, nowMs = Date.now(), toleranceSec = 1800) {
  if (!header || !secret) return { ok: false, reason: 'missing header or secret' };
  const parts = header.split(',');
  const t = parts.find((e) => e.startsWith('t='))?.slice(2);
  const v0 = parts.find((e) => e.startsWith('v0='));
  if (!t || !v0) return { ok: false, reason: 'bad header' };
  const ts = Number(t) * 1000;
  if (!Number.isFinite(ts) || ts < nowMs - toleranceSec * 1000 || ts > nowMs + 300000)
    return { ok: false, reason: 'timestamp outside tolerance' };
  const want = 'v0=' + hex(await hmac('SHA-256', secret, `${t}.${rawBody}`));
  return timingSafeEqual(want, v0) ? { ok: true, t } : { ok: false, reason: 'signature mismatch' };
}

/**
 * Twilio request validation: base64(HMAC-SHA1(authToken, url + sorted(key+value) of POST params)).
 */
export async function verifyTwilio(url, params, header, authToken) {
  if (!header || !authToken) return false;
  const data = url + Object.keys(params).sort().map((k) => k + params[k]).join('');
  const sig = btoa(String.fromCharCode(...new Uint8Array(await hmac('SHA-1', authToken, data))));
  return timingSafeEqual(sig, header);
}

export async function sha256Hex(s) {
  return hex(await crypto.subtle.digest('SHA-256', enc.encode(s)));
}
