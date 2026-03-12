# Italian Language Expansion Design

## Architecture: Language Data Layer (Approach 1)

Single-file app with per-language vocabulary data. No external files or dynamic loading.

## Data Structure

- `LANG_DATA = { sr: { name, flag, units }, it: { name, flag, units } }`
- `curLang` tracks active language (persisted in localStorage + Firestore)
- `UNITS`, `ALL_W`, `ALL_PH` rebuilt via `setLang(code)`
- Italian words: `["", "Italian word", "English", "emoji"]` (empty Cyrillic field)

## Progress Tracking

- Independent ELO, XP, streak, completed units per language
- Firestore: `users/{uid}/langs/sr`, `users/{uid}/langs/it`
- Local: `st` saved/loaded per language key in localStorage

## UI Changes

- Splash: language picker (flag buttons) above sign-in
- Home header: language indicator, tap to switch
- Exercises: hide Cyrillic display when field is empty
- Profile: stats for current language

## Italian Course

Mirror Serbian's 88 units (A1-C1). Three Serbian-specific swaps:
- "Serbian Geography" -> "Italian Geography"
- "Serbian Folklore" -> "Italian Folklore"
- "Holidays & Celebrations" -> Italian holidays

## Unchanged

Auth, service worker, manifest, PWA, ELO algorithm, exercise types, normEN().
