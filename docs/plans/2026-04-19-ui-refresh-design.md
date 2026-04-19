# UI Refresh — Refined Dark + Zeka Personality — Design Doc

## Summary

Refresh the Zeka UI around two pillars:
1. **Refined Dark** visual language — warmer dark base, Serbian blue replacing purple, consistent spacing and dividers
2. **Personality layer** — put Zeka the bunny (our existing logo) to work across the app. Add celebrations, empty states, and subtle micro-animations.

No new features. No navigation changes. No third-party dependencies. Same single-file PWA architecture.

## Goals & Non-Goals

**Goals**
- Replace ad hoc inline styles with a consistent color system based on CSS variables
- Give Zeka visual personality without commissioning new art
- Make empty states feel intentional, not like missing UI
- Add animation polish that conveys motion and feedback

**Non-Goals**
- No typography overhaul (keep system font stack)
- No navigation restructure
- No new mascot illustrations beyond the existing `icon-512.png`
- No light mode (dark only for now)

## 1. Color & Theme System

Replace the current scattered colors and inline `rgba(255,255,255,X)` values with CSS variables. Add the new variables at the top of the `:root` block in `index.html`.

### New CSS Variables

```css
:root {
  /* Surface */
  --bg: #0F1419;
  --surface: #1A2028;
  --surface-raised: #222A33;
  --divider: rgba(255,255,255,.06);

  /* Text */
  --text-1: #F5F7FA;
  --text-2: rgba(245,247,250,.65);
  --text-3: rgba(245,247,250,.4);

  /* Brand & Accents */
  --sr-blue: #1A5FD1;       /* ELO badge, primary brand */
  --sr-blue-d: #0C3D8E;     /* button shadow */
  --green: #58CC02;         /* unchanged — primary action */
  --green-d: #3D8B00;       /* unchanged */
  --orange: #FFA54F;        /* streak fire */
  --red: #FF6B6B;           /* hearts, errors */
  --gold: #FFD43B;          /* perfect-score moments */
}
```

### Migration
- `#131F24` → `var(--bg)` everywhere
- Purple ELO badge gradient → solid `var(--sr-blue)` with white text
- `rgba(255,255,255,.06)` borders/dividers → `var(--divider)`
- Scattered text colors in inline styles → `var(--text-1/2/3)` via utility classes where practical
- Keep button shadow pattern (`box-shadow: 0 4px 0 <darker>`) on primary buttons

### Risk
- Touching many inline styles. Where conversion is mechanical (find/replace `#131F24` → `var(--bg)`), do it in one pass. Where inline `rgba(255,255,255,X)` is in template literals with many variants, migrate only the most visible ones — not a full sweep.

## 2. Zeka Mascot Placement

Use the existing `icon-512.png` file consistently. No new art.

### Where Zeka appears

| Location | Size | Context |
|---|---|---|
| Splash screen | 120px | Centered above "Let's learn!" CTA — welcomes user |
| Session complete | 80px | With confetti, rotating message based on accuracy |
| Flashcards empty state | 100px | "Finish a lesson to unlock flashcards" |
| Flashcards caught up | 100px | "All caught up! Come back in Xh" |
| Social empty state | 100px | "Zeka is lonely — invite a friend" |
| Grammar unavailable | 80px | "Cases are Serbian-only" |
| Profile avatar fallback | 48px | When no Google photo |
| Streak milestone toast | 72px | When hitting 3/7/14/30/100 |

### Speech bubble component

New CSS component `.zeka-speak` for Zeka's contextual messages:
- Uses `var(--surface)` background with `var(--divider)` border
- Rounded corners (16px), max-width ~260px, 14px text in `var(--text-1)`
- Includes a small triangle pointer (via `::before`) aimed at the Zeka face above it
- Exact triangle positioning can be tweaked during implementation

### Rotating messages

`ZEKA_MSG` arrays for variety:

```javascript
const ZEKA_MSG = {
  sessionComplete: {
    perfect: ['Savršeno!', 'Odlično! No mistakes!', 'Incredible!', 'Zeka is impressed!'],
    good: ['Bravo!', 'Nice work!', 'Keep going!', 'You got this!'],
    rough: ["Don't give up!", 'Every mistake teaches you!', 'Try again!']
  },
  streakMilestone: [
    'Three days! Zeka is proud!',
    'A week! You\'re on fire!',
    'Two weeks! Unstoppable!',
    'A month! Zeka bows down 🙇',
    'A hundred days! Legend!'
  ]
};
```

## 3. Celebrations

### Session complete (upgraded)

Before: shows stats card + "Continue" button.

After:
- Zeka appears (80px) top center with speech bubble
- Accuracy-based message: perfect (100%) → perfect array, ≥70% → good array, <70% → rough array
- Confetti (already exists) stays, but only for perfect score
- Stats card below Zeka with existing content
- Gold border on the stats card if 100%

### Streak milestone toast (new)

Triggers when `st.streak` hits one of [3, 7, 14, 30, 100] and was lower before.

```javascript
function showStreakMilestone(days) {
  // Full-screen overlay with Zeka + fire + "X day streak!" for ~2 seconds
  // Auto-dismisses, clickable to dismiss early
}
```

Implementation: reuses the existing `.ov` overlay pattern. Fires from `showComp` after save.

### First-time moments (new)

Track in state: `st.firsts = { lesson: false, flashcard: false, verbDrill: false, caseDrill: false }`. On the first completion of each type, show a small celebratory toast with Zeka.

After being set to `true`, no longer shown. Persisted in localStorage/Firestore via existing state sync.

## 4. Empty States

Current empty states are one-line text messages. Replaced with:

### Flashcards (no cards yet)
```html
<div class="empty-state">
  <img src="icon-512.png" class="zeka-face" alt="Zeka">
  <div class="zeka-speak">Finish a lesson to unlock flashcards! 🥕</div>
  <button class="btn-primary" onclick="S.setLearnMode('lessons')">Go to Lessons</button>
</div>
```

### Flashcards (caught up)
```html
<div class="empty-state">
  <img src="icon-512.png" class="zeka-face" alt="Zeka">
  <div class="zeka-speak">All caught up! 🎉<br>Come back in <span id="fc-next-time">3h</span> for more.</div>
</div>
```

Compute next-due-time from earliest `due` timestamp in `st.fc`.

### Social (no friends)
Current: just "No activity yet" text
New: Zeka + "It's quiet here. Invite a friend with your code: **XYZ**" + copy button

### Grammar > Cases (wrong language)
Already exists; upgrade the text-only version to include Zeka face.

### Empty state CSS

```css
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 24px;
  gap: 16px;
  text-align: center;
}
.zeka-face {
  width: 100px;
  height: 100px;
  border-radius: 24px;
  box-shadow: 0 8px 24px rgba(0,0,0,.3);
}
```

## 5. Micro-animations

All animations use CSS transitions/keyframes, no JS animation libraries.

### Existing elements to animate

- **ELO badge pulse** — when ELO changes, briefly scale: `animation: elopulse 400ms`. Trigger by toggling a class in the ELO update code.
- **Streak fire flicker** — continuous subtle animation on the 🔥 emoji (hue-rotate + scale 1s infinite)
- **Heart loss shake** — when `st.hearts` drops, `animation: shake 400ms`
- **Active button press** — add `:active { transform: translateY(2px); box-shadow: 0 2px 0 var(--btn-d); }` to all primary buttons
- **Current unit node breathe** — the `cur` node on the lesson path gets `animation: breathe 2s ease-in-out infinite`

### Tab transition

```css
#home > .mode-container {
  animation: fadeIn 150ms ease;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}
```

Applied when switching between Lessons/Flashcards/Grammar.

### Flashcard flip enhancement

Existing 3D flip stays. Add a subtle `filter: drop-shadow(...)` that grows during the flip (simulates lift).

## 6. File Layout & Scope

All changes in `index.html` (single-file PWA). New assets: none.

### Changes by section

| Section | Lines affected (approx) | Change type |
|---|---|---|
| `:root` CSS vars | ~20 | Add new vars |
| Existing CSS rules | ~100 | Update to use new vars |
| HTML (empty states) | ~30 | Add new empty state blocks |
| JS (ZEKA_MSG, celebrations, firsts) | ~80 | Add new helpers + wire to existing completion handlers |
| Service worker | 1 | Bump cache version |

### Order of implementation

1. Add new CSS vars; migrate mechanical `#131F24` → `var(--bg)` and purple → `var(--sr-blue)` usages
2. Add `.zeka-face`, `.zeka-speak`, `.empty-state` components
3. Replace existing empty state contents with new structure
4. Add `ZEKA_MSG` and `showStreakMilestone` helpers
5. Wire celebrations into `showComp`, `finishFcSession`, `finishVerbSession`, `finishCaseSession`
6. Add `st.firsts` state, sync through getStateData/applyStateData
7. Wire first-time celebrations
8. Add animation keyframes + apply classes to ELO, streak, hearts
9. Add breathe to current node in `rPath`
10. Add fade transition to mode switcher
11. Bump SW cache

## 7. Testing / Verification

Manual verification checklist:
- [ ] Splash screen shows Zeka + intro
- [ ] ELO badge is Serbian blue, no purple anywhere
- [ ] Hit complete a lesson: session complete screen shows Zeka + rotating message
- [ ] Perfect score (100%): gold border, special message
- [ ] Complete a flashcard session: correct Zeka message
- [ ] Log out and back in: empty flashcards state shows Zeka + CTA to Lessons
- [ ] Complete all due flashcards: "all caught up" state shows Zeka + next-due time
- [ ] Switch language to Italian, go to Grammar > Cases: Zeka "Cases are Serbian-only"
- [ ] Hit a streak milestone (set `st.streak = 2` then complete lesson): milestone toast appears
- [ ] ELO badge pulses when ELO changes
- [ ] Current unit node breathes on lesson path
- [ ] Lose a heart: heart shake animation plays
- [ ] Tab switching on LEARN feels smooth (not snap)

## 8. Out of Scope (Future Work)

- Alternate Zeka poses/expressions (needs AI or illustration work)
- Light mode
- Typography system (custom display font, Serbian-specific treatment)
- Full accessibility audit / prefers-reduced-motion handling (noted for future)

## Success Criteria

1. App feels more cohesive (no purple/teal/orange dissonance)
2. Empty states have personality
3. Session complete moments feel rewarding
4. No regressions in existing functionality
5. Zeka the bunny is visibly the app's face
