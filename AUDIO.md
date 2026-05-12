# Audio Pipeline

Zeka pre-downloads TTS audio for every word so playback is instant and
doesn't depend on a third-party API at runtime.

## How it works

- Audio files live under `audio/sr/` and `audio/it/`
- Filenames are the URL-encoded source text + `.mp3` (e.g. `škola` → `%C5%A1kola.mp3`)
- The browser builds the URL `audio/<lang>/<encoded>.mp3` for each speaker click
- Files are sourced from Lingva Translate mirrors (Google Translate TTS proxy)
- Missing files fall back to the Web Speech API at runtime

## Adding new words

1. Edit `index.html` — add words to a unit, verb to `V_SR`, noun to `N_SR`, etc.
2. **If you have the pre-commit hook installed (recommended), audio is fetched automatically before commit.**
3. Otherwise, run manually:

```bash
python sync_audio.py            # both languages
python sync_audio.py --sr       # Serbian only
python sync_audio.py --it       # Italian only
python sync_audio.py --check    # list missing without downloading
```

## Installing the pre-commit hook (one-time setup)

```bash
git config core.hooksPath .githooks
```

After that, any commit that touches `index.html` will automatically:

1. Scan `index.html` for new Serbian/Italian strings
2. Download missing MP3s from Lingva mirrors
3. Stage the new audio files into the commit

If the script fails (network down, all mirrors rate-limited, etc.) the
commit is aborted — fix the issue and retry.

## What gets extracted

The script pulls every string that needs audio from `index.html`:

| Source | Pattern |
|---|---|
| Unit vocabulary words | `["s","l","e","em"]` arrays inside units |
| Phrases | Items inside `p:[...]` blocks |
| Verb infinitives (SR) | `{inf:'…',…}` |
| Verb conjugations (SR) | All 6 forms in `conj:{…}` |
| Noun nominatives (SR) | `nom:'…'` |
| Noun case forms (SR) | All 7 cases in `cases:{…}` |
| Case sentence answers (SR) | `a:'…'` inside sentence arrays |

## Failure modes

- **All mirrors down**: try again later; Lingva mirrors come and go
- **HTTP 429 rate limited**: script backs off and retries 4× per file
- **Empty audio**: some Lingva mirrors return empty responses for tricky strings; the script reports these for manual investigation
- **Encoding mismatches**: ensure source text in `index.html` uses normalized Unicode (precomposed forms)

## File integrity

The script considers a file "valid" if it exists and is at least 100 bytes.
If a download was truncated, delete the file manually and re-run sync.

```bash
# Find suspiciously small files
find audio/ -name "*.mp3" -size -1k -ls
```
