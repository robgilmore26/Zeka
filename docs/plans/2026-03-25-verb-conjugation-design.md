# Verb Conjugation Drill — Design

## Overview
A verb conjugation practice mode on the LEARN tab, focused on drilling present tense conjugation forms. Two-phase exercise: translate the infinitive, then fill in all 6 conjugation forms with pre-filled common stems.

## Navigation
- Third segment on LEARN tab toggle: `[Lessons] [Flashcards] [Verbs]`
- `setLearnMode('verbs')` switches to the verb home view

## Verbs Home View
- **Random Session** button with 3/5/10 verb count picker
- **Full verb list** below — scrollable, tap any verb to drill it solo
- Each row: infinitive + English (e.g. "raditi — to work")

## Exercise Flow

### Phase 1 — Infinitive Translation
- App shows verb infinitive in either English or Serbian (randomized)
- User types the translation
- Instant feedback: green if correct, red with correction if wrong
- Proceed to Phase 2 regardless of correctness

### Phase 2 — Conjugation Grid
- Compute longest common prefix across all 6 conjugation forms
- Display prefix in muted/grey text, input box immediately after for the suffix
- 6 rows with pronoun labels:
  - Ja ___
  - Ti ___
  - On/Ona/Ono ___
  - Mi ___
  - Vi ___
  - Oni/One/Ona ___
- Individual validation on tab/move to next field — instant green/red per box
- Speaker button appears on correct answers for pronunciation
- If no common prefix exists across all forms, show full empty input boxes

### Examples
- Regular verb "raditi": prefix `rad` pre-filled → type `im`, `iš`, `i`, `imo`, `ite`, `e`
- Irregular verb "moći": prefix `mo` pre-filled → type `gu`, `žeš`, `že`, `žemo`, `žete`, `gu`

## Session Modes
1. **Random session**: user picks 3/5/10 verbs, random selection from full list
2. **Single verb**: tap any verb from the list to drill just that one

## Session Summary
- Displayed after completing all verbs in a session
- Stats: verbs completed, conjugations correct/total, accuracy %
- "Done" button returns to Verbs home view

## Flashcard Integration
- After practicing a verb, its infinitive (Serbian ↔ English) auto-seeds into `st.fc` if not already present
- Uses existing SM-2 flashcard system
- Verb infinitives appear in flashcard due queue alongside vocabulary words

## Verb Data Structure
```javascript
const V_SR = [
  {inf: 'biti', en: 'to be', em: '🔄', conj: {
    ja: 'sam', ti: 'si', on: 'je', mi: 'smo', vi: 'ste', oni: 'su'
  }},
  {inf: 'imati', en: 'to have', em: '🤲', conj: {
    ja: 'imam', ti: 'imaš', on: 'ima', mi: 'imamo', vi: 'imate', oni: 'imaju'
  }},
  // ... 25 verbs total
];
```

### Serbian Verbs (25, present tense)

**Essential (10):** biti, imati, hteti, moći, ići, raditi, znati, videti, jesti, piti

**Daily Life (10):** govoriti, razumeti, pisati, čitati, učiti, živeti, voleti, spavati, kupovati, davati

**Action (5):** igrati, pevati, trčati, putovati, kuvati

### Italian Verbs
To be defined — similar set of 25 common present tense verbs.

## No Spaced Repetition for Conjugation
- Verb conjugation drills are pure practice — no SM-2 scheduling
- Only the infinitive translation feeds into the flashcard system

## Future Expansion
- Past tense conjugations
- Future tense conjugations
- More verbs added over time as user masters current set
