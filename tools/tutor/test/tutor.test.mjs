// Runs without network or the Anthropic SDK: node --test tools/tutor/test/
import test from 'node:test';
import assert from 'node:assert/strict';
import { webcrypto } from 'node:crypto';
import {
  toLatin, splitLines, serbianOnly, trimCutoff, buildSystem, buildMessages, replyText,
  verifyFirebaseToken, handleTurn, handleSummary, START_TURN, CLAUDE_MODEL, HttpError,
} from '../src/tutor.js';

test('toLatin converts Serbian Cyrillic, including digraphs and all-caps words', () => {
  assert.equal(toLatin('Здраво! Како си? Љубав, њега, џеп.'), 'Zdravo! Kako si? Ljubav, njega, džep.');
  assert.equal(toLatin('ЉУБАВ Љубав'), 'LJUBAV Ljubav');
  assert.equal(toLatin('Latin stays: šta, đak.'), 'Latin stays: šta, đak.');
});

test('splitLines and serbianOnly separate English support lines', () => {
  const t = 'Šta radiš vikendom?\nEN: What do you do on weekends?\nIdem na pijacu.';
  assert.deepEqual(splitLines(t).map(l => l.lang), ['sr', 'en', 'sr']);
  assert.equal(serbianOnly(t), 'Šta radiš vikendom? Idem na pijacu.');
});

test('trimCutoff drops a half-finished last line', () => {
  assert.equal(trimCutoff('Zdravo!\nEN: Hello!\nKako s'), 'Zdravo!\nEN: Hello!');
  assert.equal(trimCutoff('Zdravo! Kako s'), 'Zdravo!');
});

test('buildSystem adds the English switch and at most 5 mistakes', () => {
  const m = Array.from({ length: 8 }, (_, i) => ({ said: 'x' + i, correct: 'y' + i, why: 'z' }));
  const on = buildSystem({ english: true, mistakes: m });
  assert.match(on, /English support is ON/);
  assert.equal((on.match(/- He said/g) || []).length, 5);
  assert.match(buildSystem({ english: false }), /English support is OFF/);
});

test('buildMessages starts with a user turn and merges same-role turns', () => {
  assert.deepEqual(buildMessages([]), [{ role: 'user', content: START_TURN }]);
  const msgs = buildMessages([{ role: 'assistant', text: 'Zdravo!' }, { role: 'user', text: 'Ćao' }, { role: 'user', text: 'Dobro' }]);
  assert.deepEqual(msgs.map(m => m.role), ['user', 'assistant', 'user']);
  assert.equal(msgs[2].content, 'Ćao\nDobro');
});

test('replyText handles refusal, max_tokens and Cyrillic', () => {
  assert.match(replyText({ stop_reason: 'refusal', content: [] }), /Izvini/);
  const r = replyText({ stop_reason: 'max_tokens', content: [{ type: 'text', text: 'Здраво!\nEN: Hello!\nКако с' }] });
  assert.equal(r, 'Zdravo!\nEN: Hello!');
});

// ── Firebase token check with a locally generated key ─────────────────
async function makeSigner() {
  const kp = await webcrypto.subtle.generateKey({ name: 'RSASSA-PKCS1-v1_5', modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: 'SHA-256' }, true, ['sign', 'verify']);
  const jwk = { ...(await webcrypto.subtle.exportKey('jwk', kp.publicKey)), kid: 'k1', alg: 'RS256', use: 'sig' };
  const enc = o => Buffer.from(JSON.stringify(o)).toString('base64url');
  const sign = async claims => {
    const h = enc({ alg: 'RS256', kid: 'k1', typ: 'JWT' }), p = enc(claims);
    const sig = await webcrypto.subtle.sign('RSASSA-PKCS1-v1_5', kp.privateKey, new TextEncoder().encode(h + '.' + p));
    return h + '.' + p + '.' + Buffer.from(sig).toString('base64url');
  };
  const fetchFn = async () => new Response(JSON.stringify({ keys: [jwk] }), { headers: { 'cache-control': 'max-age=60' } });
  return { sign, fetchFn };
}
const NOW = 1_800_000_000_000;
const good = { aud: 'zeka-4329b', iss: 'https://securetoken.google.com/zeka-4329b', sub: 'u1', iat: NOW / 1000 - 10, exp: NOW / 1000 + 3000, email: 'Rob@Example.com', email_verified: true };

test('verifyFirebaseToken accepts an allowed, valid token and rejects the rest', async () => {
  const { sign, fetchFn } = await makeSigner();
  const opts = { projectId: 'zeka-4329b', allowedEmails: 'rob@example.com', fetchFn, now: NOW };
  assert.deepEqual(await verifyFirebaseToken(await sign(good), opts), { uid: 'u1', email: 'rob@example.com' });
  const reject = async (claims, status) => {
    await assert.rejects(verifyFirebaseToken(await sign(claims), opts), e => e instanceof HttpError && e.status === status);
  };
  await reject({ ...good, email: 'someone@else.com' }, 403);
  await reject({ ...good, email_verified: false }, 403);
  await reject({ ...good, exp: NOW / 1000 - 1 }, 401);
  await reject({ ...good, aud: 'other-project' }, 401);
  const t = await sign(good);
  const tampered = t.split('.'); tampered[1] = Buffer.from(JSON.stringify({ ...good, email: 'x@y.z' })).toString('base64url');
  await assert.rejects(verifyFirebaseToken(tampered.join('.'), opts), e => e.status === 401);
  await assert.rejects(verifyFirebaseToken('', opts), e => e.status === 401);
});

// ── A whole turn with stand-ins for ElevenLabs and Claude ─────────────
function fakeDeps({ sttText = 'Zdravo, ja sam Rob', claudeText = 'Драго ми је, Робе!\nEN: Nice to meet you, Rob!', stop = 'end_turn' } = {}) {
  const calls = { stt: 0, tts: [], claude: [] };
  const fetchFn = async (url, init) => {
    if (url.includes('speech-to-text')) {
      calls.stt++;
      assert.equal(init.body.get('model_id'), 'scribe_v2');
      assert.equal(init.body.get('language_code'), 'sr');
      return new Response(JSON.stringify({ text: sttText }));
    }
    if (url.includes('text-to-speech/voice123')) {
      const b = JSON.parse(init.body); calls.tts.push(b);
      assert.equal(b.model_id, 'eleven_v3');
      return new Response(new Uint8Array([1, 2, 3]));
    }
    throw new Error('unexpected fetch ' + url);
  };
  const claude = {
    messages: {
      create: async req => { calls.claude.push(req); return { stop_reason: stop, content: [{ type: 'text', text: claudeText }], usage: { input_tokens: 500, output_tokens: 40 } }; },
      parse: async req => { calls.claude.push(req); return { parsed_output: { summary: 'Добро!', corrections: [{ said: 'ja si', correct: 'ja sam', why: 'sam goes with ja' }] }, usage: {} }; },
    },
  };
  return { calls, deps: { claude, fetchFn, env: { ELEVENLABS_API_KEY: 'k', ELEVENLABS_VOICE_ID: 'voice123' }, summarySchemaFormat: { type: 'json_schema' } } };
}
function form(payload, bytes) {
  const f = new FormData();
  f.append('payload', JSON.stringify(payload));
  if (bytes) f.append('audio', new Blob([new Uint8Array(bytes)], { type: 'audio/webm' }), 'speech.webm');
  return f;
}

test('handleTurn: speech in, Latin text and Serbian-only audio out', async () => {
  const { calls, deps } = fakeDeps();
  const out = await handleTurn(form({ history: [{ role: 'assistant', text: 'Zdravo!' }], english: true, mistakes: [{ said: 'a', correct: 'b', why: 'c' }] }, 2000), deps);
  assert.equal(out.user_text, 'Zdravo, ja sam Rob');
  assert.equal(out.tutor_text, 'Drago mi je, Robe!\nEN: Nice to meet you, Rob!');
  assert.equal(calls.tts[0].text, 'Drago mi je, Robe!');           // English line not voiced, Cyrillic gone
  assert.equal(out.tts_chars, 'Drago mi je, Robe!'.length);
  assert.equal(out.audio_b64, 'AQID');
  const req = calls.claude[0];
  assert.equal(req.model, CLAUDE_MODEL);
  assert.equal(req.max_tokens, 160);
  assert.deepEqual(req.thinking, { type: 'disabled' });
  assert.match(req.system, /He said "a"/);
  assert.deepEqual(req.messages.map(m => m.role), ['user', 'assistant', 'user']);
  assert.equal(req.messages[2].content, 'Zdravo, ja sam Rob');
});

test('handleTurn: session start needs no audio; empty or huge audio is handled', async () => {
  const { calls, deps } = fakeDeps();
  const out = await handleTurn(form({ start: true, history: [] }), deps);
  assert.equal(calls.stt, 0);
  assert.equal(calls.claude[0].messages[0].content, START_TURN);
  assert.ok(out.tutor_text);
  await assert.rejects(handleTurn(form({ history: [] }), deps), e => e.status === 400);
  await assert.rejects(handleTurn(form({ history: [] }, 100), deps), e => e.status === 400);
  await assert.rejects(handleTurn(form({ history: [] }, 2_600_000), deps), e => e.status === 413);
  const silent = fakeDeps({ sttText: '' });
  const s = await handleTurn(form({ history: [] }, 2000), silent.deps);
  assert.equal(s.empty, true);
  assert.equal(silent.calls.claude.length, 0);
});

test('handleTurn: English support off reaches the prompt', async () => {
  const { calls, deps } = fakeDeps({ claudeText: 'Kako si?' });
  await handleTurn(form({ history: [], english: false }, 2000), deps);
  assert.match(calls.claude[0].system, /English support is OFF/);
});

test('handleSummary returns Latin summary and corrections', async () => {
  const { calls, deps } = fakeDeps();
  const out = await handleSummary({ history: [{ role: 'assistant', text: 'Zdravo' }, { role: 'user', text: 'ja si Rob' }] }, deps);
  assert.equal(out.summary, 'Dobro!');
  assert.deepEqual(out.corrections[0], { said: 'ja si', correct: 'ja sam', why: 'sam goes with ja' });
  const req = calls.claude[0];
  assert.equal(req.output_config.format.type, 'json_schema');
  assert.equal(req.messages.at(-1).role, 'user');
});
