# Learning upgrades: past tense, aspect cards, cloze, reading

Approved by Rob on 2026-09-19 ("Let's build 1 thru 4"). Serbian only; Italian is
untouched. Everything lives in `index.html` following the existing single-file
patterns (data consts → `S.*` methods → inline CSS blocks).

## 1. Past tense (perfekt) for every conjugated verb

**Data.** Each `V_SR` entry keeps `conj` (present). The l-participle is derived
by `verbPast(v)` from the infinitive (`raditi → radio / radila / radilo / radili /
radile / radila`); irregular verbs carry an explicit `pp:['išao','išla']`
(masc/fem singular) and the other four forms derive from the feminine stem.
Reflexive verbs (`buditi se`) get the auxiliary+`se` order (`sam se budio`,
`se budio` in 3sg). `reći` uses `kazati` forms for the present, with a `note`.

**Drill.** Verb home gets a Present / Past segmented toggle (`st.vbTense`,
persisted). Past sessions keep phase 1 (translate the infinitive) and replace
phase 2 with six rows: Ja (m) sam ___, Ti (f) si ___, Ono je ___, Mi smo ___,
Vi ste ___, One su ___ — the auxiliary is shown, the participle is typed with
the same common-prefix trick the present drill uses.

**Dictionary.** The verb expansion shows a "Past" line (`bio · bila · bili`) and
the search index gains the masc/fem participles as aliases.

## 2. Aspect pairs as real cards

The 37 perfective partners in `V_SR_ASPECT` become:
- **Flashcards**: a new A2 unit `{id:93, t:"Aspect Pairs"}` inserted after the
  last A2 unit so it enters the new-card queue at the right point. It holds the
  28 perfectives that are not already unit words. Each word's 5th field (`gn`)
  reads `pf. · impf. čitati`; the 10 perfectives already present as words get
  the same `gn` tag added in place (positions unchanged). Unit phrases contrast
  the pair ("Čitam knjigu." / "Pročitao sam knjigu.").
- **Verb drill / dictionary**: the 37 perfectives (except `doći`, already there)
  are appended to `V_SR` with present conjugations, `pf:true`, and derive past
  forms like any other verb. The verb list shows a small "pf" badge.

Word ids 9300–9327 are new; no existing id changes.

## 3. Cloze drill

**Sources.** Every `SENT_SR` blank, plus every unit phrase (≥3 tokens) whose
tokens contain one of the unit's own words (stem match via `_fcStemKey`).

**Selection.** Level gate from `learnedWordCount()` (<150 → A1; <400 → A1–A2;
else all). Weighted sampling: ×3 if the answer belongs to a word the learner has
reviewed, +2 if that card is weak (`lapses ≥ 2`), ×1 otherwise. No sentence
repeats within a session. Sessions of 5 / 10 / 15.

**Answering.** Two modes, `st.clozeMode` = `tap` (default) or `type`, switchable
on the drill. Tap shows four options: the answer plus three distractors chosen
to target the grammar point — other case forms of the same noun (`N_SR`),
other persons of the same verb (`V_SR.conj`), other gender/number forms of the
participle, other prepositions (unit 49) — falling back to same-level answers of
similar length. Type mode uses `normSR` (diacritic-tolerant) checking.

**Feedback loop.** A miss on an item tied to a flashcard word makes that card
due now (both directions) so it resurfaces in the daily session. A hit changes
nothing. Session end bumps the streak.

**Entry points.** ⋯ menu → Cloze; the flashcard session-complete screen offers
"Practice in context" (10 items).

## 4. Reading mode

**Data.** `READ_SR`: eight graded texts (A1 ×3, A2 ×3, B1 ×2) as
`{id, lv, t, em, s:[{sr,en}], g:{token:gloss}}`. `g` glosses every token of the
text in its inflected form (e.g. `sirom: 'cheese (instr.)'`), so tap-to-translate
never depends on dictionary lookup; lookup is only the fallback.

**Screen.** Reading home lists texts by level with a ✓ for finished ones
(`st.readDone`, persisted). The reading screen renders each sentence with every
word tappable; a tap shows the gloss in a bottom bar and highlights the word,
and each sentence has a toggle to reveal its English. "Mark as read" records the
text, bumps the streak and shows how many words were looked up.

**Entry point.** ⋯ menu → Reading.

## Shared

- New `st` fields: `vbTense`, `clozeMode`, `readDone` (all persisted);
  session-only `cz*` / `rd*` fields.
- `setLearnMode` gains `cloze` and `reading` containers; both highlight ⋯.
- `insertSrKey` (šžčćđ keys) now also targets `.sent-blank` and cloze inputs —
  the Sentences drill rendered the keys but ignored them.
- Verification: browser pane on `zeka-dev` with cache-busted reloads; every
  inline script parsed with `new Function()` before commit.
