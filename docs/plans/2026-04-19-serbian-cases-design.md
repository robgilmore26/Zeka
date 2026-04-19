# Serbian Cases — Design Doc

## Summary

Add a new "Cases" drill mode for Serbian. Users practice declining nouns through all 7 grammatical cases in two phases: filling in a declension table, then applying the forms in contextual sentences. The feature introduces a new "Grammar" segment on the LEARN toggle that contains both Verbs and Cases, enabling future expansion (Past, Future, Adjectives).

## Scope

- **Cases covered:** All 7 Serbian cases — Nominativ, Genitiv, Dativ, Akuzativ, Vokativ, Instrumental, Lokativ
- **Number:** Singular only (plural is future work)
- **Language:** Serbian only at launch (Italian has no equivalent case system)
- **Starting nouns:** 18 nouns, 6 per gender (masculine, feminine, neuter)

## Navigation Changes

### Before
```
LEARN toggle: [Lessons] [Flashcards] [Verbs]
```

### After
```
LEARN toggle: [Lessons] [Flashcards] [Grammar]
Grammar screen sub-toggle: [Verbs] [Cases]
```

The existing Verbs screen moves under the Grammar segment. Tapping the Grammar segment shows the Grammar home view, which defaults to the Verbs sub-tab and includes a Cases sub-tab.

When the active language is not Serbian, the Cases sub-tab is hidden (Italian has no cases).

## Cases Home View

Layout (top to bottom):
1. **Header:** "Case Conjugation · 18 nouns"
2. **Random Session picker:** Three buttons (3 / 5 / 10 nouns) + a "Random Session" primary button
3. **Gender sections:** Three collapsible/scrollable sections — Masculine, Feminine, Neuter
   - Each noun row: emoji + Serbian nominative + English translation + arrow
   - Tap any noun → starts a single-noun session with just that noun

## Exercise Flow — Two Phases Per Noun

### Phase 1: Declension Table

Shows a grid of 7 rows, one per case. Each row contains:
- Case label (e.g. "Akuzativ")
- Short English hint label under the case name (e.g. "direct object", "of/from", "in/at") — purely informational, no prefill
- Pre-filled longest common prefix (muted style) + input for the changing suffix
- Individual field validation: blur or Enter triggers check → green border with suffix shown or red border with correct suffix shown
- Session counts incremented per attempt

Features:
- Serbian special character bar (`š ž č ć đ`) below the input grid (reused from Verbs)
- "Next Phase" button appears after all 7 boxes are filled
- If no common prefix exists across cases, show full empty inputs

### Phase 2: Contextual Sentences

Shows 5 sentences per noun, one at a time. Each sentence:
- Includes a blank where the declined noun goes
- Shows the nominative form in parentheses as a hint
- User types the correct declined form
- Individual feedback: green if correct, red + correction if wrong
- Tap "Next" to advance; final sentence advances to the next noun (or session summary)

Example:
```
Prompt: Idem u ______ (škola).
Answer: školu
```

Sentences are hardcoded per noun (not templated) to ensure natural phrasing.

## Session Summary

Displayed after completing all nouns in the session:
- Nouns completed count
- Declension accuracy (Phase 1 correct / total boxes)
- Sentence accuracy (Phase 2 correct / total sentences)
- Overall accuracy percentage
- "Done" button returns to Cases home

## Data Structure

New top-level array `NOUNS_SR` in index.html, referenced from `LANG_DATA.sr.nouns`:

```javascript
const NOUNS_SR = [
  {
    nom: 'škola',
    en: 'school',
    em: '🏫',
    gender: 'f',
    cases: {
      nom: 'škola',
      gen: 'škole',
      dat: 'školi',
      acc: 'školu',
      voc: 'školo',
      ins: 'školom',
      loc: 'školi'
    },
    sentences: [
      {case: 'acc', text: 'Idem u ______.', hint: 'to school'},
      {case: 'loc', text: 'Radim u ______.', hint: 'at school'},
      {case: 'gen', text: 'Nema ______.', hint: 'no school'},
      {case: 'ins', text: 'Zadovoljna sam ______.', hint: 'happy with school'},
      {case: 'dat', text: 'Idem ka ______.', hint: 'toward the school'}
    ]
  },
  // ... 17 more
];
```

Language accessor updated: `LANG_DATA.sr.nouns = NOUNS_SR`. Italian has no `nouns` array.

## Starting Noun List

### Masculine (6)

| Nominative | English | Emoji | Notes |
|---|---|---|---|
| čovek | man | 👨 | animate |
| pas | dog | 🐕 | animate, stem change |
| grad | city | 🏙️ | inanimate |
| sto | table | 🫖 | inanimate |
| auto | car | 🚗 | inanimate |
| film | film | 🎥 | inanimate |

### Feminine (6)

| Nominative | English | Emoji |
|---|---|---|
| škola | school | 🏫 |
| kuća | house | 🏠 |
| žena | woman | 👩 |
| knjiga | book | 📖 |
| voda | water | 🌊 |
| ulica | street | 🛣️ |

### Neuter (6)

| Nominative | English | Emoji | Notes |
|---|---|---|---|
| jutro | morning | 🌅 | -o neuter |
| selo | village | 🏞️ | -o neuter |
| more | sea | 🌊 | -e neuter |
| ime | name | 📛 | -e neuter, stem expansion |
| pismo | letter | ✉️ | -o neuter |
| dete | child | 🧒 | -e neuter, irregular |

Total: 18 nouns × 7 cases = **126 declensions**, plus 18 × 5 = **90 sentences**.

## UI / CSS

Reuse existing verb drill CSS where possible:
- `.vd-phase`, `.vd-prompt`, `.vd-conj`, `.vd-row`, `.vd-pronoun`, `.vd-stem`, `.vd-suffix`, `.vd-next`, `.sr-keys`, `.sr-key`
- Add `.cs-*` variants only where behavior diverges (e.g., case label column wider than pronoun column)

New screen ID: `#cases` (parallel to `#verbdrill`).

## State Model

New session state properties added to `st`:
```
csNouns: []         // nouns in current session
csIdx: 0            // current noun index
csPhase: 1          // 1 = declension table, 2 = sentences
csSentenceIdx: 0    // current sentence in phase 2
csTotal: 0          // total attempts this session
csCorrect: 0        // correct attempts this session
```

No persistent per-noun mastery tracking in the initial version — each session is independent. (Persistent tracking is future work, similar to flashcards' SM-2.)

## Common Prefix Logic

Reuse pattern from verb drill. For the 7 case forms of a noun:
```javascript
function casePrefix(noun){
  const forms = Object.values(noun.cases);
  let pre = forms[0];
  for (let i = 1; i < forms.length; i++){
    while (forms[i].indexOf(pre) !== 0) pre = pre.slice(0, -1);
    if (!pre) return '';
  }
  return pre;
}
```

Edge cases:
- `pas` → forms: pas, psa, psu, psa, pse, psom, psu → common prefix is `p` (very short but correct)
- `ime` → forms: ime, imena, imenu, ime, ime, imenom, imenu → common prefix is `ime`

## Answer Matching

Same logic as verb drill:
- Lowercase both sides before comparing
- Strip leading/trailing whitespace
- Phase 1 (declension table): user types only the suffix; the full form is reconstructed by concatenating the pre-filled prefix + typed suffix, then compared to the target case form
- Phase 2 (sentences): user types the complete declined noun (no preposition); compared to the target case form for that sentence
- Exact match required (no fuzzy matching in v1)

## Firestore Sync

No new Firestore fields required in the initial version. Session state is transient. If per-noun mastery is added later, it goes under `st.ns` (noun stats) similar to `st.ws` (word stats).

## Out of Scope (Future Work)

- Plural declensions (another 7 forms × 18 nouns)
- Additional noun entries beyond the initial 18
- Per-noun mastery tracking / spaced repetition
- Adjective agreement with cases
- Preposition drills
- Italian case-equivalent features (Italian uses prepositions, not cases)

## Success Criteria

1. User can tap Grammar on the LEARN toggle and see Verbs + Cases sub-tabs
2. User can start a random session or pick a specific noun
3. Phase 1 renders 7 input boxes with correct prefix pre-fill
4. Each box validates individually with green/red feedback
5. Phase 2 shows 5 sentences with correct answer matching
6. Session summary shows accurate counts
7. Serbian special character bar works in both phases
8. When active language is Italian, Cases sub-tab is hidden
9. No regressions in existing Verbs drill
