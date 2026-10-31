// Cloudflare Worker for Zeka Speaking Practice. Keeps the API keys server-side:
// the app sends audio and the conversation so far; this returns the transcript,
// the tutor's reply and its audio. Setup: tools/tutor/README.md.
import Anthropic from '@anthropic-ai/sdk';
import { z } from 'zod';
import { zodOutputFormat } from '@anthropic-ai/sdk/helpers/zod';
import { handleTurn, handleSummary, verifyFirebaseToken, HttpError } from './tutor.js';

const SummarySchema = z.object({
  summary: z.string(),
  corrections: z.array(z.object({ said: z.string(), correct: z.string(), why: z.string() })),
});

function cors(env, request) {
  const origin = request.headers.get('origin') || '';
  const allowed = String(env.ALLOWED_ORIGINS || 'https://zeka.one').split(',').map(s => s.trim());
  return {
    'access-control-allow-origin': allowed.includes(origin) ? origin : allowed[0],
    'access-control-allow-methods': 'POST, OPTIONS',
    'access-control-allow-headers': 'authorization, content-type',
    'access-control-max-age': '86400',
    vary: 'origin',
  };
}

export default {
  async fetch(request, env) {
    const headers = cors(env, request);
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers });
    const json = (obj, status = 200) => new Response(JSON.stringify(obj), { status, headers: { ...headers, 'content-type': 'application/json' } });
    try {
      if (request.method !== 'POST') throw new HttpError(405, 'Use POST');
      for (const k of ['ANTHROPIC_API_KEY', 'ELEVENLABS_API_KEY', 'ELEVENLABS_VOICE_ID', 'ALLOWED_EMAILS', 'FIREBASE_PROJECT_ID']) {
        if (!env[k]) throw new HttpError(500, 'Server not set up: ' + k + ' is missing');
      }
      const token = (request.headers.get('authorization') || '').replace(/^Bearer\s+/i, '');
      await verifyFirebaseToken(token, { projectId: env.FIREBASE_PROJECT_ID, allowedEmails: env.ALLOWED_EMAILS, fetchFn: fetch });
      const claude = new Anthropic({ apiKey: env.ANTHROPIC_API_KEY });
      const deps = { claude, fetchFn: fetch, env, summarySchemaFormat: zodOutputFormat(SummarySchema) };
      const path = new URL(request.url).pathname;
      if (path === '/turn') return json(await handleTurn(await request.formData(), deps));
      if (path === '/summary') return json(await handleSummary(await request.json(), deps));
      throw new HttpError(404, 'Not found');
    } catch (err) {
      if (err instanceof HttpError) return json({ error: err.message }, err.status);
      if (err instanceof Anthropic.RateLimitError) return json({ error: 'The tutor is busy; try again in a moment' }, 429);
      if (err instanceof Anthropic.APIConnectionError) return json({ error: 'Could not reach the tutor; try again' }, 502);
      if (err instanceof Anthropic.APIError) return json({ error: 'Tutor error (' + err.status + ')' }, 502);
      console.error(err);
      return json({ error: 'Something went wrong' }, 500);
    }
  },
};
