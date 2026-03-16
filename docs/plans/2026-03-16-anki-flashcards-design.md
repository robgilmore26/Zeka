# Anki-Style Flashcard Feature Design

## Summary

Add a spaced repetition flashcard system (SM-2 algorithm) to Zeka, accessible via a toggle on the LEARN tab. Remove XP and hearts from the header, keep streaks next to ELO.

## Header Changes

- Remove XP (lightning) and hearts from the top status bar
- Move streak (fire) next to the ELO badge in the top-left
- Result: `[flag] [ELO] [fire streak]`

## LEARN Tab Toggle

- Segmented control at top of LEARN tab: `[Lessons] [Flashcards]`
- Lessons view: existing unit path (unchanged)
- Flashcards view: due card count, "Start Review" button, per-unit card summary

## Flashcard Deck Rules

- Word pool: only words from completed units
- New cards: when a unit is completed, all its words enter the flashcard system as new (interval=0, due immediately)
- Bidirectional: each word generates two cards (Serbian->English, English->Serbian), tracked independently

## SM-2 Spaced Repetition Algorithm

### Per-card state

- `ease`: ease factor (starts at 2.5)
- `ivl`: interval in days (starts at 0)
- `due`: timestamp of next review
- `reps`: consecutive correct count

### Rating buttons (shown after flip)

| Button | Interval Effect | Ease Effect | Reps |
|--------|----------------|-------------|------|
| Again  | Reset to 1 min | ease - 0.2 (min 1.3) | 0 |
| Hard   | interval * 1.2 | ease - 0.15 | +1 |
| Good   | interval * ease | no change | +1 |
| Easy   | interval * ease * 1.3 | ease + 0.15 | +1 |

### Initial intervals (new cards)

- First review: immediate (new card)
- After "Again": 1 minute
- After first "Good": 10 minutes
- After second "Good": 1 day
- Then SM-2 formula takes over

## Card UI

### Front
- Word text (Serbian or English depending on direction)
- Speaker button (pronunciation)
- Tap card or "Flip" button to reveal

### Back
- Translation + emoji
- Speaker buttons for both languages
- CSS 3D flip animation
- Four rating buttons: `[Again] [Hard] [Good] [Easy]`
- Each button shows next interval preview (e.g. "Again (1m)", "Good (3d)")

## Session Flow

- No fixed session size: show all due cards
- Flashcards view shows "X cards due today" or "All caught up!"
- "Again" cards re-enter current session (shown again after a few other cards)
- Session ends when no more due cards remain
- Summary screen at end: cards reviewed, accuracy breakdown

## Data Storage

- New field: `st.fc` object keyed by `{wordId}_{direction}` (e.g. "105_se", "105_es")
- Each entry: `{ease: 2.5, ivl: 0, due: timestamp, reps: 0}`
- Synced to Firestore via existing `getStateData()` / `applyStateData()` pipeline
- Persisted in localStorage alongside existing state
