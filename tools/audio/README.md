# Zeka listening audio

Every clip the app plays was generated from **Cyrillic** text and **listened to by a person** before it shipped.
The app reads `voice/manifest.json`; an item with no entry there simply has no speaker button. There is no
fallback to the device's own speech.

## Why it is built this way

Audio was removed in May 2026 because it sounded wrong. The old pipeline fed Microsoft's Serbian voices the
**Latin** spelling of each word, and voiced bare fragments such as `ćeš` or `psu` on their own. Those voices
expect Serbian in Cyrillic, and isolated fragments are where any voice is weakest. This pipeline:

1. converts every word and sentence to Cyrillic (`extract.js`; Latin and Cyrillic Serbian map one-to-one),
2. voices only whole words, phrases and sentences, with leading and trailing silence trimmed,
3. uses Microsoft's Azure Speech service, whose output may be used in apps (the free Edge endpoint used in May
   is not licensed for that and is only used here for the local trial),
4. optionally sends every clip back through Azure speech-to-text and flags any whose transcript doesn't match,
5. publishes nothing until a person has approved it in the review page.

## One-time setup

1. In the Azure portal, create a **Speech** resource (any region; the pay-as-you-go tier costs a few dollars
   for the whole course, the free tier works but is rate-limited and slower).
2. Copy its key and region, then set them in your own terminal (never paste them into a file in this repo):

   ```bash
   export AZURE_SPEECH_KEY=...
   export AZURE_SPEECH_REGION=westeurope
   ```

## Routine

```bash
python tools/audio/build.py trial                                   # optional: old vs new, by ear (no account)
python tools/audio/build.py generate --engine azure --verify        # all words + sentences; resumable
python tools/audio/build.py review                                  # rewrite the review page
```

Open `tools/audio/staging/review.html` in a browser (the zeka-dev preview serves it at
`/tools/audio/staging/review.html`). Clips the automatic check flagged come first. Keys: `Space` play,
`S` slow, `A` OK and next, `F` flag and next. When done, **Download decisions**, then:

```bash
python tools/audio/build.py publish ~/Downloads/zeka-audio-review.json
git add voice && git commit -m "Publish reviewed listening clips"
```

Publishing merges into the existing manifest, so you can review and publish in batches (for example A1 first).
Flagged clips are removed from the manifest. New course content: re-run `generate`; only new items are voiced.

## Files

| Path | What it is | In git |
|---|---|---|
| `tools/audio/extract.js` | Everything speakable, as Cyrillic | yes |
| `tools/audio/build.py` | generate · review · publish · trial | yes |
| `tools/audio/*_template.html` | Review and trial pages | yes |
| `tools/audio/staging/` | Generated clips, results, review page | no |
| `tools/audio/trial/` | Trial clips and page | no |
| `voice/manifest.json`, `voice/sr/*.mp3` | Published, approved clips the app plays | yes |
