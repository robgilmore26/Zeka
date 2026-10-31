# Speaking Practice server

A Cloudflare Worker that turns one spoken turn into the tutor's reply:

1. ElevenLabs Scribe (`scribe_v2`, language `sr`) transcribes the recording.
2. Claude (`claude-haiku-5-5`, replies capped at 160 tokens, thinking off) answers as Zeka the tutor,
   with the conversation so far and the 5 most recent corrections from earlier sessions.
3. Any Cyrillic is converted to Latin.
4. ElevenLabs TTS (`eleven_v3`, the "Ivan - Deep Serbian & Croatian (Balkan)" voice) voices the Serbian lines
   (lines starting `EN:` are English support: shown in the app, not voiced).

`POST /turn` takes `multipart/form-data` (`payload` JSON + optional `audio`), `POST /summary` takes JSON and returns
the end-of-session summary and corrections (structured output). Both need the signed-in user's Firebase ID token
(`Authorization: Bearer …`); only addresses in `ALLOWED_EMAILS` get through, so nobody else can spend the credit.

## Setup (once, on the PC)

Needs Node.js (LTS, from nodejs.org), a free Cloudflare account, an ElevenLabs API key and an Anthropic API key.

```
powershell -ExecutionPolicy Bypass -File tools\tutor\setup.ps1
```

It installs the packages, runs the tests, logs in to Cloudflare, asks for both keys with hidden input (they go
straight into Cloudflare as secrets), finds the Ivan voice and adds it to your ElevenLabs voices, asks which email
may use the tutor, and deploys. It prints an address ending in `workers.dev`: put that in `TUTOR_URL` in
`index.html` to switch the mode on.

- Code changes only: `setup.ps1 -DeployOnly`
- Another voice: `setup.ps1 -VoiceId <id>`
- Tests (no network or keys needed): `npm test` in this folder

Secrets: `ANTHROPIC_API_KEY`, `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `ALLOWED_EMAILS`. Plain settings in
`wrangler.toml`: `FIREBASE_PROJECT_ID`, `ALLOWED_ORIGINS`. Never put a key in a file or a chat.
