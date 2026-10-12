# Grammar cloze bank + future tense

Approved by Rob on 2026-10-12 ("Let's do 1 and 2"). Serbian only.

## Why

The cloze drill was meant to train grammar, but its items come from the
sentence bank and unit phrases, which mostly blank plain vocabulary: of 529
items only 41 test a case ending, preposition or participle, and 6 of 225
sentences use the future. The verb drill has present and past only.

## 1. Grammar cloze bank (`CLOZE_SR`)

Hand-written items, each testing one grammar point:
`{id, lv, g, sr, a, en, c, d:[3], w}` where `g` is the tag
(loc, acc, gen, dat, ins, voc, past, asp, fut), `a` the answer token (appears
exactly once in `sr`), `c` the cue shown after the blank (base form, or the
pronoun for future auxiliaries), `d` three hand-picked wrong options that
contrast with the answer, and `w` a one-line rule shown after answering.
Ids are permanent (progress is keyed by them): append only, never reorder.

## 2. Cloze changes

- **Focus picker** on the Cloze home: Mixed · Cases · Past & aspect · Future
  (`st.czFocus`, persisted). Mixed is ~60% grammar items, ~40% the existing
  vocabulary-in-context items.
- **Grammar memory** `st.czg[id] = {n, ok}` (attempts, consecutive correct),
  persisted. Weight: unseen 2, last answer wrong 4, one right 1, two or more
  right 0.35. A missed rule comes back in the next rounds; mastered ones fade.
- Grammar items use their own wrong options, show the cue next to the blank,
  and always show the rule line after answering. They never nudge flashcards
  (the mistake is grammar, not vocabulary).
- The round summary lists results per grammar point, weakest first.
- "Practice in context" after flashcards always starts a Mixed round; other
  entry points use the chosen focus.

## 3. Future tense (futur I) in the verb drill

- `verbFuture(v)`: auxiliary ću/ćeš/će/ćemo/ćete/će. Infinitives in -ti merge
  (raditi → radiću; jesti → ješću via `fu:'ješ'`); infinitives in -ći stay two
  words (ići ću). Reflexives put se last (budiću se, obući ću se).
- Verb home toggle becomes Present / Past / Future (`st.vbTense`). Rows are
  labelled (ja)…(oni) because the pronoun is dropped, which is when the merged
  form is used; the note shows the pronoun form (Ja ću raditi). The learner
  types the full form, diacritic-tolerant; reflexives are accepted with or
  without se.
- Dictionary verb card gets a Future line; the merged 1sg is a search alias.

## Verification

Generator validates every item (answer present exactly once, three distinct
wrong options that differ from the answer after diacritic folding, valid tag
and level). Browser pane: each focus, tap and type, summary, verb future rows.
An independent reviewer checks the Serbian before deploy.
