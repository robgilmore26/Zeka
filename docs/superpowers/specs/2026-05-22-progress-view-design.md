# Progress view design

**Date:** 2026-05-22
**Status:** Approved (design)
**Replaces:** Social tab

## Summary

Replace the Social tab with a Progress tab that combines motivation (streak, words, mastery) with diagnostic (cards you're struggling on, cards you're improving on). Per-language only — the view always reflects the currently selected language. No charts; stat cards, a stacked mastery bar, and ranked word lists.

The friends activity feed currently in the Social tab moves into the Profile screen as a secondary section (Profile already owns friend management).

## Goals

- Give users a clear answer to "how am I doing?" without leaving the app.
- Surface action items: which words to practice next.
- Reinforce engagement with visible wins (milestones, "bouncing back" recoveries).
- Replace a tab that is dead for solo/unsigned-in users with one that always has content.

## Non-goals

- Time-series history or X-Y charts.
- Cross-language comparison views.
- Tracking calendar heatmaps, hourly activity, or other deep analytics.
- Social/leaderboard features.

## Information architecture

Bottom nav changes from `Learn / Social / Profile` to `Learn / Progress / Profile`.

`S.goSocial()` is renamed to `S.goProgress()`. The `#social` screen is repurposed to `#progress`. The friends activity feed (`_loadActivities`, `_socFriendUids`, `_socCursor`, `_socActivities` and related DOM) is **removed entirely** as part of this work — Social was a dead tab for unsigned/solo users, and Profile already owns friend management. Friend-list features (adding friends, viewing friend profiles) stay where they are in Profile. Activity-feed surfacing returns as a future feature when social signal is worth re-introducing.

## Screen layout (top to bottom)

1. **Header** — `📈 Progress` title + current language flag/name.
2. **Hero row** — three stat cards: Streak (🔥), Words (🏆 = mastered count), Today (⚡ = reviews completed today).
3. **Needs work** — top struggling cards, ranked. "Practice weak cards →" button starts a flashcard session containing only this list.
4. **Bouncing back** — cards you used to fail but are now nailing. Soft green glow.
5. **Mastery** — stacked-segment bar + bucket counts (Mastered / Familiar / Learning / Not yet seen).
6. **Recent wins** — milestone log (mastery thresholds, streak hits, units completed).

Order rationale: action up top → context (where you stand) → reward at the bottom.

## Data model

### Per-card additions (extends `st.fc[k]`)

The card structure already has `{ease, ivl, due, reps, views}` after recent changes. Add two more fields:

| Field | Type | Behavior |
|---|---|---|
| `lapses` | int | Increments by 1 every time the user presses **Again** (rating 0). Never decreases. |
| `streak` | int | Current consecutive correct streak. Resets to 0 on Again; +1 on Hard/Good/Easy. |

Both default to 0. `fcGet` migrates existing cards (set to 0 if missing). Both increments live inside `fcRate` — single call site.

### No new global state

Mastery bucket counts, milestones, "today's reviews," and the needs-work/bouncing-back lists are all **derived on render** from `st.fc`, `st.completed`, `st.streak`, and `st.lastDate`. No new persisted state outside of `lapses` and `streak`.

"Today's reviews" reuses the existing daily-reset pattern: `_fcResetDayIfNeeded()` already resets `st.fcNewToday` to 0 when `st.fcNewDate` changes. Extend it to also reset `st.fcReviewedToday` in the same block (one new line). `st.fcReviewedToday` is incremented inside `fcRate` regardless of rating.

## Mastery buckets

Derived from SRS state for each `(wordId, dir)` card:

| Bucket | Criterion | Color |
|---|---|---|
| **Mastered** | `reps ≥ 2` AND `ivl ≥ 21` | `--green` (#58CC02) |
| **Familiar** | `reps ≥ 2` AND `ivl < 21` | `--blue` (#1CB0F6) |
| **Learning** | `reps = 1` (introduced once, not graduated) | `--orange` (#FFA54F) |
| **Not yet seen** | no card entry OR `reps = 0 AND due = 0` | `--g6` (#4B4B4B) |

The percentage in the bar header ("67% known") = `(Mastered + Familiar) / total`.

The source pool is the same set used by flashcards in **All Vocabulary** mode — i.e., `UNITS.flatMap(u => u.words)` for the current language, doubled for both directions (se/es). Verbs are excluded from bucket counts (they're not auto-introduced to the SRS).

## Needs work

A card qualifies if `lapses ≥ 2 AND streak ≤ 1`.

Ranking: descending by `lapses`, tiebreak ascending by `streak`, tiebreak ascending by `ease`.

Displayed: top 5 in the section, with a count badge ("Needs work · 8 cards") showing the total. The "Practice weak cards →" button seeds a one-off flashcard session built from the full qualifying list (not just the top 5), bypassing the daily new-card limit (these are all already-introduced cards).

Per-row meta text: `Failed N×` and `M% accuracy` where accuracy = `(views - lapses) / views`.

## Bouncing back

A card qualifies if `lapses ≥ 2 AND streak ≥ 3`.

Ranking: descending by `streak`.

Displayed: top 3 in the section, with a count badge. Section gets a subtle green glow border to feel like a pat on the back. No CTA button — this section is celebratory, not actionable.

Per-row meta text: `Was failing` / `N in a row ✓`.

**Note on the gap at `streak = 2`:** cards with `lapses ≥ 2 AND streak = 2` qualify for neither Needs work nor Bouncing back. This is intentional — two-in-a-row is too thin a signal to celebrate (could be a fluke), and the card isn't actively failing either. It re-enters Bouncing back at streak=3 or Needs work if streak resets.

## Recent wins

Derived retroactively on each render. Generated milestones:

- **Words mastered** at 10, 50, 100, 250, 500 (using bucket count).
- **Streak hits** at 3, 7, 14, 30, 100 (reusing existing `STREAK_MILES`).
- **Units completed** — one entry per `st.completed[]` ID, capped at "Latest unit complete" to avoid spam.

Since we have no historical timestamps for milestone hits, "X days ago" labels are computed from anchor data we DO have:

- **Streak milestones:** parse `st.lastDate` (a `toDateString()` value) back into a Date, subtract `(st.streak - milestoneValue)` days, format the gap from today as `Nd ago` (or `today`/`yesterday`). Only show streak milestones that the user has actually passed — i.e., `st.streak ≥ milestoneValue`.
- **Units:** use existing `st.completed` order as a proxy (most recent at end), no exact date — show as "Latest" / "Earlier" labels rather than days.
- **Word-count milestones:** don't show a date (just "✨ 100 words mastered" with no relative date).

If a milestone has no derivable date, the date column is blank. We don't fabricate. (A future enhancement could log `st.milestones[]` with hit timestamps; out of scope here.)

Top 3 most relevant entries shown.

## Streak fix (bundled with this work)

**Bug:** `st.streak++` is currently called only inside `showComp()` (lesson completion). Flashcard, verb-drill, and sentence-completion handlers never tick it. Users who do flashcards daily but skip lessons silently lose their streak.

**Fix:** extract a helper:

```js
function bumpStreak(){
  const today = new Date().toDateString();
  if(st.lastDate === today) return null;  // already counted today
  const prev = st.streak;
  st.streak++;
  st.lastDate = today;
  const hit = STREAK_MILES.includes(st.streak) && st.streak > prev ? st.streak : null;
  return hit;
}
```

Call from all four "meaningful session" exits:

| Existing call site | Becomes |
|---|---|
| `showComp` (lesson complete) | Already had the logic — replace with `bumpStreak()` |
| `finishFcSession` (flashcards) | Add `bumpStreak()` if `st.fcReviewed > 0` |
| Verb drill finish handler | Add `bumpStreak()` on successful completion |
| Sentence finish handler | Add `bumpStreak()` on completion |

Reset logic (line 2555) is unchanged. The `STREAK_MILES` celebration overlay continues to fire from `showComp` only (or wherever the caller's UX flow makes sense).

## Components and files

This is a single-file app (`index.html`). All changes happen there.

- **CSS:** new `.pg-*` block in the `<style>` section. Reuses existing tokens (`--bg`, `--green`, `--blue`, `--orange`, `--surface`, etc.).
- **HTML:** rename `<div class="sc" id="social">` → `id="progress"`. Restructure inner body.
- **Bottom nav:** all three nav rows (Home, Progress, Profile screens) updated to read `Progress` with appropriate icon.
- **JS:**
  - `goSocial` → `goProgress` (rename and refactor body).
  - New: `renderProgress()`, `getMasteryBuckets()`, `getWeakCards()`, `getBouncingBackCards()`, `getRecentWins()`, `startWeakCardSession()`.
  - New: `bumpStreak()` helper + four call-site updates.
  - Update `fcRate` to increment `lapses` and update `streak`, plus increment `st.fcReviewedToday`.
  - Update `fcGet` to migrate `lapses`/`streak` defaults.
  - **Delete** the friends activity feed: `_loadActivities`, `_socCursor`, `_socActivities`, `_socFriendUids`, `goSocial`'s feed-loading body, and the `#fp-modal-wrap`/empty-state DOM unique to that view. Friend management code in Profile is untouched.

## Edge cases

- **Empty state — no flashcard activity yet.** All four sections render with placeholder messaging:
  - Hero: streak `0`, words `0`, today `0`.
  - Needs work: "No tough cards yet — keep going!"
  - Bouncing back: "Cards you've recovered from will appear here."
  - Mastery: shows "Not yet seen" = full vocab count.
  - Recent wins: "Your milestones will appear here as you progress."
- **Existing users' cards lack `lapses`/`streak` history.** Migration sets both to 0. "Bouncing back" will be empty until they grade new cards. This is honest and acceptable.
- **Italian users with no flashcard vocab loaded for some units.** Mastery bucket totals reflect whatever `UNITS.flatMap(u => u.words)` returns for `curLang`. If a language has zero vocab, render empty state for the whole screen.
- **Language switch while on Progress screen.** Re-render. State refresh is already wired through `setLang()`.

## Out of scope (potential future work)

- Per-unit mastery breakdown ("Animals: 12/15 mastered").
- Direction-asymmetry insights ("You nail SR→EN but stumble EN→SR").
- Milestone timestamps (requires logging on hit; we can backfill from FC card timestamps but it's a separate effort).
- Re-introduction of a social/friend-activity surface anywhere in the app.
- Animated count-up on stat cards.

## Testing approach

This is a single-file static HTML app with no existing test harness. Testing is manual:

- **Layout / render** — open `index.html` locally, exercise each section with real data.
- **Empty state** — clear `localStorage`, reload, confirm all four sections render their empty messaging.
- **Derivations** — temporarily seed `st.fc` from the browser console with synthetic cards covering each bucket and each weak/bouncing-back criterion; confirm counts and lists.
- **Streak fix** — simulate cross-midnight by manually setting `st.lastDate` to yesterday's `toDateString()`, then run a flashcard session and confirm `st.streak` ticks by 1. Run a second flashcard session same-day and confirm it does NOT tick again.
- **Language switch** — switch between Serbian and Italian, confirm bucket counts reflect the current language's vocabulary.

Derivation functions (`getMasteryBuckets`, `getWeakCards`, `getBouncingBackCards`, `getRecentWins`) should be written as pure functions taking `st.fc` (and current language's word list) as input, so they're trivially re-testable in a future automated test pass if a harness is introduced.
