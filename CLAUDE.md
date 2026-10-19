# Zeka — project guide for Claude

Read this first in every session (desktop, cloud or phone). It replaces the May 2026 notes and is kept in git so
cloud sessions get it too. Update it when something here stops being true.

## What Zeka is

Zeka (zeka.one) is a Duolingo-style PWA for learning **Serbian** (Latin script, ekavian), A1 to C1. Italian was
retired on 2026-10-12. The owner, **Rob** (GitHub `robgilmore26`), builds it and is also its main learner: his own
progress in Serbian matters more than polish. A few other people use it; it is free, with no ads.

**How Rob works:** short approvals ("yes", "ship it"), screenshots when something looks wrong, and he expects a root
cause, a fix, a deploy and a check that it is live — not a description. He reads Serbian well: flag judgment calls
(standard vs colloquial forms) instead of silently choosing. Explain in plain language; he is not a developer.

## Architecture

- `index.html` — the whole app (~7,000 lines): HTML, CSS and JS inline, data included. No build step, no bundler,
  no tests. Firebase Auth + Firestore (compat 10.12, CDN), Google Identity Services, Motion One (CDN, `window.M`).
- `sw.js` — service worker. Network-first for HTML and `voice/manifest.json`, cache-first for other assets,
  passes Firebase/Google/Umami straight through. **Bump `CACHE` (`zeka-vNN`) on every user-visible deploy**; that
  also makes the "Zeka updated · Tap to reload" pill appear for open tabs.
- `help/index.html` — static Help & FAQ (privacy, credits, how scheduling works). Keep it in step with features.
- `voice/manifest.json` + `voice/sr/*.mp3` — published, human-approved listening clips (empty until published).
- `tools/audio/` — the listening-audio pipeline (see below and its README).
- `docs/superpowers/specs|plans/` — dated design and plan docs for major features.
- `manifest.json`, `capacitor.config.json`, `package.json` — PWA manifest and the (not yet scaffolded) native shell.

## Deploying

- GitHub Pages serves `main` at **zeka.one** (repo `robgilmore26/Zeka`; the old name SerbianDuolingo redirects).
  Deploy = get the change onto `main` and push. Work on a branch, then merge or fast-forward it into `main`.
- On Rob's PC the main checkout has two modified icon PNGs he wants left **uncommitted**; never `git add -A` there.
- GitHub's CDN caches HTML for ~10 minutes. Confirm a deploy with the page's `Last-Modified` header
  (`curl -s -D - -o /dev/null "https://zeka.one/?nocache=$(date +%s)"`) and by grepping the live HTML for a symbol
  from the change. Profile shows `Build <Last-Modified in UTC>` for the same purpose.
- Commit messages: imperative summary line, a short body saying why, and the co-author trailer you are given.

## Rules that prevent real bugs

- **Data ids are permanent.** Word id = `unit.id * 100 + position`: never reorder words in a unit, never reuse a
  unit id (Serbian units use ids 1–93; ids 80–83 once collided and merged progress). Append new words at the end.
  `CLOZE_SR` ids (st.czg progress), `READ_SR` ids (st.readDone) and `SENT_SR` ids are append-only too. Conversation
  Path steps (`PATH_SR`) use unit ids 94+; they reuse existing words by id (`r:[...]`, same flashcard) and list only
  words new to the course in `w`, so check a word isn't already in the course before adding it. Verb cards
  are keyed `v_<infinitive>`, so renaming an infinitive orphans its card.
- **Boot order.** `setLang(curLang)` runs at load; anything it (or other boot code) touches must be declared above
  it, or the app hangs on "Loading…" for everyone (temporal dead zone — this happened once).
- **Persisted state:** a new `st` field must be added to the `st` defaults, `getStateData()` **and**
  `applyStateData()`, or it silently fails to sync. Never call `save()` while state is loading: it can overwrite a
  newer cloud copy with an older local one before `fbLoad` compares them. `fbLoad` takes the copy with the newer
  `savedAt` as the base and `_mergeState` adds everything earned only in the other copy (completed, uacc, xp, readDone,
  firsts, ws, czg, streak, `st.fc` card by card by `last`), so a stale tab saving later can't wipe progress; a tab
  back from >60 s in the background re-reads the cloud first. A new persisted field that only grows belongs in
  `_mergeState` too.
- **Overlays/sheets** mount through `_overlayHost()` (inside `#scr`), never `document.body`, or they stretch across
  the desktop window. No CSS `zoom`; use transforms (zoom rendered differently in Rob's browser).
- After editing, **parse every inline `<script>`** (extract each, strip the module `import` line,
  `new Function(body)`) before committing. Edit large blocks with exact-match replacements that fail loudly when a
  target is missing or not unique.

## Verifying changes

There is no test suite. Serve the repo (`python -m http.server 8080`) and load `/?cb=<something>` (the service
worker otherwise serves the old copy). Enter as guest (`enterGuest('sp')`), then drive features through the `S.*`
methods and check the DOM and `st`. Known noise: "Transition was skipped/aborted" promise errors, GSI/FedCM sign-in
messages and blocked `navigator.vibrate` are harmless. Measure layouts with `getBoundingClientRect` at 390×844 and at
1200×900; say plainly which browser engine was actually checked.

## Learning features (current)

Flashcards (spaced repetition, the main mode) · Lessons (Conversation Path: Stage 1 = ids 94–101, Stage 2 = ids 102–109, Stage 3 = ids 110–115;
plus the
93 original units as always-open Topic packs) · Match · Search/dictionary · Progress ·
Verbs (118 verbs, present / past / future drills) · Cases (7 cases) · Sentences (daily sentence + bank) ·
Cloze (152 hand-written grammar sentences + ~530 vocabulary sentences, focus picker, grammar memory) ·
Reading (8 graded texts, tap-to-translate) · Listening (drill + speaker buttons; hidden until clips are published).
The ⋯ segment on Learn opens the extra modes; Flashcards home has an "Also today" strip.

**Flashcard scheduling (v2, Oct 2026)** — `fcNext()` is the single source of truth (rating and button labels):
forgetting a review card gives one short retry, then half its old interval (not a reset); ease falls less (Again
−0.15 once per lapse, Hard −0.10) and Good restores it toward 2.5; overdue recall is credited (Good: half the delay,
Easy: all of it) from the per-card `last` timestamp; intervals cap at 365 days. A one-time, idempotent repair raises
worn-down ease (`fcAlgo:2`). Catch-up mode pauses new words while more than 60 reviews are due; new words ride on top of a full 30-review session (up to 10); new words/day can be
paused (0 is a real value, not "unset"). Each word is asked in one direction per day (`fcDueBreakdown`): a card
waits while its se/es sibling was rated today, only the more overdue of two due siblings is offered, and a new
word's English→Serbian card is introduced on a later day than its Serbian→English one. New words are introduced
in `FC_NEW_ORDER_SR` order (usefulness tiers + OpenSubtitles frequency, duplicates last); **add every new word id to
that list** at a sensible spot, or it is introduced after all 978 current words.

## Serbian content

Get every new batch of Serbian content (sentences, conjugations, glosses, wrong options) independently reviewed
before shipping. The usual failure is a "wrong" option that is also correct: Serbian uses the perfective present for
habits ("Uvek zaboravim ključeve"), the present for planned future ("Vidimo se sutra", "Radim sutra"), short
clitics ("Verujem ti"), and plural accusatives can fit. Write items so the sentence itself rules alternatives out.
With a pronoun, clitics cluster: "Ja ću se buditi", never "Ja ću buditi se". Forms that depend on the learner's gender
are written `{m|f}` in the data (`Žele{o|la} bih`) and resolved by `gx()` from `st.gender` (m / f / b = both). Tatoeba sentences (`SENT_SR` ids 100+,
CC BY 2.0 FR) carry `tt:[srId,enId]` and must keep their visible "Tatoeba #id" credit.

## Listening audio

Clips are made by `tools/audio/` (read its README): `extract.js` turns every item into **Cyrillic**; `build.py`
voices it with Azure Speech `sr-RS-NicholasNeural` (Rob's pick), trims silence, adds a slow version per sentence,
round-trips each clip through speech-to-text to flag mismatches, writes a review page, and `publish` copies only
clips Rob approved into `voice/`. The app plays only manifest clips and never falls back to device speech (the May
2026 audio failed because Latin text and bare fragments were fed to the voice). Generation needs Rob's Azure Speech
key; on his PC `tools\audio\run-azure.ps1` asks for it with hidden input. Never put the key in a file or a chat.

## Analytics and QA

- Umami (cookie-free) on zeka.one only. A once-a-day `open` event carries days since that device first opened Zeka
  (retention without identifying anyone). Profile has an opt-out; Rob and any QA bot should switch it off.
- QA is done by Rob's Grok bot from paste-ready markdown briefs: P0/P1/P2 items with steps, viewport (390×844 and a
  desktop size), auth (guest is fine), the expected build stamp, and the known console noise to ignore.

## Open threads (as of 2026-10-18)

- Azure Speech resource not created yet → no listening clips published. Next: generate A1 + verbs, Rob reviews.
- A throwaway QA account (`qa-grok@zeka.one`) still exists in Firebase Auth; Rob may delete it.
- Monetisation ideas (Zeka Plus, AI tutor) are parked. Before charging: move off GitHub Pages, and gate paid content
  server-side (the whole course ships inside `index.html`, so hiding the repo alone protects nothing).
- Native apps: Capacitor is configured but `npx cap add ios/android` has never been run.
