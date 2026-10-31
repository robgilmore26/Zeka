// Zeka Speaking Practice: the tutor's server logic, kept free of the Anthropic SDK
// import so it can be tested with stand-ins (see test/tutor.test.mjs). index.js
// wires in the real SDK client and the Worker's fetch.

export const CLAUDE_MODEL = 'claude-haiku-5-5';
export const STT_MODEL = 'scribe_v2';
export const TTS_MODEL = 'eleven_v3';
export const REPLY_MAX_TOKENS = 160;      // about 300 characters of reply
export const SUMMARY_MAX_TOKENS = 1200;
export const MAX_AUDIO_BYTES = 2_500_000; // about a minute of compressed speech
export const MAX_HISTORY = 30;            // turns sent to Claude
export const MAX_TURN_CHARS = 600;

// Rob's tutor prompt, word for word, plus one formatting rule the app needs to
// show English support in lighter text and to voice only the Serbian.
export const TUTOR_PROMPT = `You are Zeka, a patient, warm Serbian conversation tutor from Belgrade. Rob is a true beginner (A1). If unsure whether he knows a word, assume he does not.
Level: A1 Serbian only, common everyday words, mostly present tense, 6 to 8 words per sentence, one or two sentences per turn. No idioms or complex grammar.
English support: after every Serbian sentence, give the English meaning briefly ("Šta radiš vikendom? ... That means: what do you do on weekends?"). Translate new words in the same turn. Explain corrections in one short English sentence. Keep the conversation itself in Serbian. If he says "bez engleskog", stop translating until he says "na engleskom".
Corrections: respond naturally to what he meant, then give the correct form once with a one-line English explanation. Ignore small errors.
If he asks how to say something: give the phrase, repeat it, give the meaning, ask him to repeat it.
Every few minutes, offer a simple role-play (ordering coffee, directions, shopping).
Rules: standard ekavian Serbian, never Croatian or Bosnian vocabulary (hleb not kruh, voz not vlak, hiljada not tisuća). Always Latin script, never Cyrillic. No grammar lectures.
When asked for a summary: in English, what he did well, the 2 or 3 most important corrections, and 3 useful words or phrases from the session.

Format: put every English part (meanings, translations of new words, explanations of corrections) on its own line starting with "EN: ". Every other line is Serbian only. Keep the whole reply under 300 characters.`;

export const START_TURN = '[Session start. Greet Rob briefly and ask him one simple question.]';

// ── Cyrillic safety net ──────────────────────────────────────────────
const CYR = {'А':'A','Б':'B','В':'V','Г':'G','Д':'D','Ђ':'Đ','Е':'E','Ж':'Ž','З':'Z','И':'I','Ј':'J','К':'K','Л':'L','Љ':'Lj','М':'M','Н':'N','Њ':'Nj','О':'O','П':'P','Р':'R','С':'S','Т':'T','Ћ':'Ć','У':'U','Ф':'F','Х':'H','Ц':'C','Ч':'Č','Џ':'Dž','Ш':'Š',
  'а':'a','б':'b','в':'v','г':'g','д':'d','ђ':'đ','е':'e','ж':'ž','з':'z','и':'i','ј':'j','к':'k','л':'l','љ':'lj','м':'m','н':'n','њ':'nj','о':'o','п':'p','р':'r','с':'s','т':'t','ћ':'ć','у':'u','ф':'f','х':'h','ц':'c','ч':'č','џ':'dž','ш':'š'};
export function toLatin(s) {
  if (!s) return '';
  // An all-caps word keeps digraphs in caps (ЉУБАВ → LJUBAV, not LjUBAV)
  return s.replace(/[Ѐ-ӿ]+/g, w => {
    const out = [...w].map(ch => CYR[ch] ?? ch).join('');
    const allCaps = w.length > 1 && w === w.toUpperCase() && w !== w.toLowerCase();
    return allCaps ? out.toUpperCase() : out;
  });
}

// Lines starting with "EN:" are English support; the rest is Serbian.
export function splitLines(text) {
  return text.split(/\n+/).map(l => l.trim()).filter(Boolean)
    .map(l => /^EN:\s*/i.test(l) ? { lang: 'en', text: l.replace(/^EN:\s*/i, '') } : { lang: 'sr', text: l });
}
export function serbianOnly(text) {
  return splitLines(text).filter(l => l.lang === 'sr').map(l => l.text).join(' ');
}

// A reply cut off by max_tokens ends at its last complete line or sentence.
export function trimCutoff(text) {
  const t = text.trim();
  const lastNl = t.lastIndexOf('\n');
  if (lastNl > 0) return t.slice(0, lastNl).trim();
  const m = t.match(/^[\s\S]*[.!?…]/);
  return m ? m[0].trim() : t;
}

export function buildSystem({ english = true, mistakes = [] } = {}) {
  let s = TUTOR_PROMPT;
  s += english
    ? '\n\nEnglish support is ON for this session (unless he says "bez engleskog").'
    : '\n\nEnglish support is OFF: Rob turned it off in the app. Do not translate or add EN: lines until he says "na engleskom".';
  const m = (Array.isArray(mistakes) ? mistakes : []).slice(0, 5)
    .map(x => x && x.said && x.correct ? `- He said "${clip(x.said, 80)}"; correct: "${clip(x.correct, 80)}"${x.why ? ` (${clip(x.why, 100)})` : ''}` : null)
    .filter(Boolean);
  if (m.length) s += '\n\nRecent mistakes from earlier sessions. Give him a natural chance to use these correctly again, without lecturing:\n' + m.join('\n');
  return s;
}

// Client history → Claude messages: alternating roles, starting with the user.
export function buildMessages(history = []) {
  const msgs = [];
  for (const h of (Array.isArray(history) ? history : []).slice(-MAX_HISTORY)) {
    const role = h && h.role === 'assistant' ? 'assistant' : 'user';
    const text = clip(String((h && h.text) || ''), MAX_TURN_CHARS);
    if (!text) continue;
    if (msgs.length && msgs[msgs.length - 1].role === role) msgs[msgs.length - 1].content += '\n' + text;
    else msgs.push({ role, content: text });
  }
  if (!msgs.length || msgs[0].role !== 'user') msgs.unshift({ role: 'user', content: START_TURN });
  return msgs;
}

function clip(s, n) { s = String(s || '').trim(); return s.length > n ? s.slice(0, n) : s; }

export function replyText(response) {
  if (response.stop_reason === 'refusal') return 'Izvini, hajde da pričamo o nečem drugom.\nEN: Sorry, let\'s talk about something else.';
  let text = response.content.filter(b => b.type === 'text').map(b => b.text).join('').trim();
  if (response.stop_reason === 'max_tokens') text = trimCutoff(text);
  return toLatin(text);
}

// ── ElevenLabs ───────────────────────────────────────────────────────
export async function transcribe(fetchFn, apiKey, audio, filename) {
  const fd = new FormData();
  fd.append('model_id', STT_MODEL);
  fd.append('language_code', 'sr');
  fd.append('file', audio, filename || 'speech.webm');
  const r = await fetchFn('https://api.elevenlabs.io/v1/speech-to-text', { method: 'POST', headers: { 'xi-api-key': apiKey }, body: fd });
  if (!r.ok) throw new HttpError(502, 'Speech-to-text failed (' + r.status + ')');
  const j = await r.json();
  return toLatin(String(j.text || '').trim());
}

export async function synthesize(fetchFn, apiKey, voiceId, text) {
  const r = await fetchFn(`https://api.elevenlabs.io/v1/text-to-speech/${encodeURIComponent(voiceId)}?output_format=mp3_44100_64`, {
    method: 'POST',
    headers: { 'xi-api-key': apiKey, 'content-type': 'application/json', accept: 'audio/mpeg' },
    body: JSON.stringify({ text, model_id: TTS_MODEL }),
  });
  if (!r.ok) throw new HttpError(502, 'Text-to-speech failed (' + r.status + ')');
  return base64(new Uint8Array(await r.arrayBuffer()));
}

function base64(bytes) {
  let s = '';
  for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  return btoa(s);
}

// ── Firebase sign-in check ───────────────────────────────────────────
// The app sends the signed-in user's Firebase ID token. It is verified here
// against Google's published keys, and only allowed email addresses get through,
// so nobody else can spend the API credit.
const JWKS_URL = 'https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com';
let jwksCache = { keys: null, until: 0 };

function b64urlBytes(s) {
  s = s.replace(/-/g, '+').replace(/_/g, '/');
  while (s.length % 4) s += '=';
  const bin = atob(s);
  return Uint8Array.from(bin, c => c.charCodeAt(0));
}
function b64urlJson(s) { return JSON.parse(new TextDecoder().decode(b64urlBytes(s))); }

export async function verifyFirebaseToken(token, { projectId, allowedEmails, fetchFn, now = Date.now() }) {
  const parts = String(token || '').split('.');
  if (parts.length !== 3) throw new HttpError(401, 'Sign in to use Speaking Practice');
  const header = b64urlJson(parts[0]);
  const claims = b64urlJson(parts[1]);
  if (header.alg !== 'RS256' || !header.kid) throw new HttpError(401, 'Bad sign-in token');
  if (!jwksCache.keys || now > jwksCache.until) {
    const r = await fetchFn(JWKS_URL);
    if (!r.ok) throw new HttpError(503, 'Could not check sign-in');
    const maxAge = Number((r.headers.get('cache-control') || '').match(/max-age=(\d+)/)?.[1] || 3600);
    jwksCache = { keys: (await r.json()).keys || [], until: now + maxAge * 1000 };
  }
  const jwk = jwksCache.keys.find(k => k.kid === header.kid);
  if (!jwk) throw new HttpError(401, 'Bad sign-in token');
  const key = await crypto.subtle.importKey('jwk', jwk, { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['verify']);
  const ok = await crypto.subtle.verify('RSASSA-PKCS1-v1_5', key, b64urlBytes(parts[2]), new TextEncoder().encode(parts[0] + '.' + parts[1]));
  if (!ok) throw new HttpError(401, 'Bad sign-in token');
  const sec = now / 1000;
  if (claims.aud !== projectId || claims.iss !== 'https://securetoken.google.com/' + projectId) throw new HttpError(401, 'Bad sign-in token');
  if (!(claims.exp > sec) || claims.iat > sec + 300 || !claims.sub) throw new HttpError(401, 'Sign-in expired, try again');
  const email = String(claims.email || '').toLowerCase();
  const allowed = String(allowedEmails || '').toLowerCase().split(',').map(e => e.trim()).filter(Boolean);
  if (!email || claims.email_verified !== true || !allowed.includes(email)) throw new HttpError(403, 'Speaking Practice is not switched on for this account');
  return { uid: claims.sub, email };
}

export class HttpError extends Error { constructor(status, message) { super(message); this.status = status; } }

// ── Request handlers ─────────────────────────────────────────────────
// deps: { claude (SDK client), fetchFn, env, summarySchemaFormat }
export async function handleTurn(form, deps) {
  const { claude, fetchFn, env } = deps;
  const payload = JSON.parse(String(form.get('payload') || '{}'));
  const audio = form.get('audio');
  const history = Array.isArray(payload.history) ? payload.history : [];
  let userText = '';
  if (audio && typeof audio !== 'string') {
    if (audio.size > MAX_AUDIO_BYTES) throw new HttpError(413, 'That recording is too long; keep it under a minute');
    if (audio.size < 800) throw new HttpError(400, 'Nothing was recorded; hold the button while you speak');
    userText = await transcribe(fetchFn, env.ELEVENLABS_API_KEY, audio, audio.name);
    if (!userText) return { user_text: '', tutor_text: '', audio_b64: '', tts_chars: 0, empty: true };
  } else if (!payload.start) {
    throw new HttpError(400, 'No recording received');
  }
  const messages = buildMessages(userText ? [...history, { role: 'user', text: userText }] : history);
  const response = await claude.messages.create({
    model: CLAUDE_MODEL,
    max_tokens: REPLY_MAX_TOKENS,
    thinking: { type: 'disabled' },
    output_config: { effort: 'low' },
    system: buildSystem({ english: payload.english !== false, mistakes: payload.mistakes }),
    messages,
  });
  const tutorText = replyText(response);
  const speech = serbianOnly(tutorText) || tutorText;
  const audioB64 = speech ? await synthesize(fetchFn, env.ELEVENLABS_API_KEY, env.ELEVENLABS_VOICE_ID, speech) : '';
  return {
    user_text: userText,
    tutor_text: tutorText,
    audio_b64: audioB64,
    audio_mime: 'audio/mpeg',
    tts_chars: speech.length,
    usage: { input_tokens: response.usage?.input_tokens || 0, output_tokens: response.usage?.output_tokens || 0 },
  };
}

export const SUMMARY_REQUEST = 'Rob ended the session. Write the summary now, as described in your instructions (in English: what he did well, the 2 or 3 most important corrections, and 3 useful words or phrases from the session). Also list each correction you made during the session.';

export async function handleSummary(body, deps) {
  const { claude, summarySchemaFormat } = deps;
  const messages = buildMessages([...(body.history || []), { role: 'user', text: SUMMARY_REQUEST }]);
  const response = await claude.messages.parse({
    model: CLAUDE_MODEL,
    max_tokens: SUMMARY_MAX_TOKENS,
    thinking: { type: 'disabled' },
    output_config: { effort: 'low', format: summarySchemaFormat },
    system: buildSystem({ english: true }),
    messages,
  });
  const out = response.parsed_output;
  if (!out) throw new HttpError(502, 'The summary came back empty; try again');
  return {
    summary: toLatin(out.summary),
    corrections: (out.corrections || []).slice(0, 10).map(c => ({ said: toLatin(c.said), correct: toLatin(c.correct), why: c.why })),
    usage: { input_tokens: response.usage?.input_tokens || 0, output_tokens: response.usage?.output_tokens || 0 },
  };
}
