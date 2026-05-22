# Progress View Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Social tab with a per-language Progress view that shows motivation stats, weak-card diagnostics, "bouncing back" recoveries, mastery buckets, and recent wins — and fix the streak bug where flashcard sessions don't tick the streak.

**Architecture:** All changes live in `index.html` (single-file static app). Two new SRS fields (`lapses`, `streak`) on each card, derived render functions for the Progress screen, deletion of dead friend-activity-feed code, and a small `bumpStreak()` helper called from all four "meaningful session" exit points.

**Tech Stack:** Vanilla HTML/CSS/JS in a single file. No build step. Manual testing in browser. Deployment is GitHub Pages on the `main` branch with `CNAME = zeka.one`.

---

## File Structure

Only one source file changes:

- **Modify:** `/c/Users/rober/OneDrive/Desktop/SerbianDuolingo/.claude/worktrees/serene-pascal-1a4b6a/index.html` — all CSS, HTML, and JS changes.

No new files. No tests file (no harness exists). Verification is manual via browser.

---

## Task 1: Add `lapses` and `streak` to SRS card state

**Files:**
- Modify: `index.html` — `fcGet()` near line 2870, `fcRate()` near line 2891

This task extends the per-card data model so we can later distinguish "struggling" from "recovering" cards. Tracked at every `fcRate()` call. Existing cards migrate to zero (no historical reconstruction).

- [ ] **Step 1: Update `fcGet()` default + migration**

Find in `index.html`:

```js
function fcGet(wordId,dir){
  const k=fcKey(wordId,dir);
  if(!st.fc[k])st.fc[k]={ease:2.5,ivl:0,due:0,reps:0,views:0};
  // Migrate older cards that lack the views counter
  if(typeof st.fc[k].views!=='number')st.fc[k].views=st.fc[k].reps||0;
  return st.fc[k];
}
```

Replace with:

```js
function fcGet(wordId,dir){
  const k=fcKey(wordId,dir);
  if(!st.fc[k])st.fc[k]={ease:2.5,ivl:0,due:0,reps:0,views:0,lapses:0,streak:0};
  // Migrate older cards that lack newer counters
  if(typeof st.fc[k].views!=='number')st.fc[k].views=st.fc[k].reps||0;
  if(typeof st.fc[k].lapses!=='number')st.fc[k].lapses=0;
  if(typeof st.fc[k].streak!=='number')st.fc[k].streak=0;
  return st.fc[k];
}
```

- [ ] **Step 2: Update `fcRate()` to maintain lapses + streak**

Find the top of `fcRate()`:

```js
function fcRate(wordId,dir,rating){
  const c=fcGet(wordId,dir);
  const now=Date.now();
  const wasBrandNew=(c.due===0&&c.reps===0);
  c.views=(c.views||0)+1;
```

Replace the last line with:

```js
  c.views=(c.views||0)+1;
  if(rating===0){c.lapses=(c.lapses||0)+1;c.streak=0;}
  else{c.streak=(c.streak||0)+1;}
```

- [ ] **Step 3: Manual verification**

1. Open `index.html` in a browser.
2. Open DevTools console, run `localStorage.clear()` and reload.
3. Pick any language with vocab. Go to Flashcards → Start a session → introduce one new card with "Got it · Continue".
4. The card returns ~minutes later as a review; rate "Again". In the console run:
   `Object.values(st.fc).filter(c=>c.lapses>0)` — should show that card with `lapses: 1, streak: 0`.
5. Rate the same card "Good" next time it comes up. Run the same query: should show `lapses: 1, streak: 1`.
6. Rate "Good" two more times: should show `lapses: 1, streak: 3`.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "Track lapses and current-streak per flashcard"
```

---

## Task 2: Add `fcReviewedToday` daily counter

**Files:**
- Modify: `index.html` — `_fcResetDayIfNeeded()` near line 2878, `fcRate()` near line 2891, `st` initializer near line 2840, `fbApplyCloud()`/load function near line 2547

A counter for the hero "Today" stat. Resets at midnight using the same key used for new-card reset.

- [ ] **Step 1: Add to default state**

Find in `index.html` (around line 2840):

```js
let st={elo:1000,xp:0,streak:0,lastDate:null,hearts:5,completed:[],ws:{},fc:{},uacc:{},
```

Add `fcReviewedToday:0,` to that initializer. The exact line currently sets several defaults — insert `fcReviewedToday:0,` adjacent to where `fcNewToday` lives in the same object. Search the file for `fcNewToday` in the initializer to find the right neighbor; place the new key right after it.

- [ ] **Step 2: Reset alongside new-card counter**

Find:

```js
function _fcResetDayIfNeeded(){
  const today=new Date().toDateString();
  if(st.fcNewDate!==today){st.fcNewDate=today;st.fcNewToday=0;}
}
```

Replace with:

```js
function _fcResetDayIfNeeded(){
  const today=new Date().toDateString();
  if(st.fcNewDate!==today){st.fcNewDate=today;st.fcNewToday=0;st.fcReviewedToday=0;}
}
```

- [ ] **Step 3: Increment on every grade**

Find in `fcRate()` (near where `c.views++` was added in Task 1):

```js
  c.views=(c.views||0)+1;
  if(rating===0){c.lapses=(c.lapses||0)+1;c.streak=0;}
  else{c.streak=(c.streak||0)+1;}
```

Insert immediately after that block:

```js
  _fcResetDayIfNeeded();
  st.fcReviewedToday=(st.fcReviewedToday||0)+1;
```

- [ ] **Step 4: Load from cloud**

Find in the cloud-load function near line 2550 (search for `st.fcNewToday=p.fcNewToday`):

```js
  st.fcNewToday=p.fcNewToday||0;st.fcNewDate=p.fcNewDate||'';st.fcNewLimit=p.fcNewLimit||10;
```

Replace with:

```js
  st.fcNewToday=p.fcNewToday||0;st.fcNewDate=p.fcNewDate||'';st.fcNewLimit=p.fcNewLimit||10;
  st.fcReviewedToday=p.fcReviewedToday||0;
```

- [ ] **Step 5: Save to cloud**

Find the function near line 2541 that returns the cloud-shaped object (search for `return{elo:st.elo,xp:st.xp`):

```js
  return{elo:st.elo,xp:st.xp,streak:st.streak,lastDate:st.lastDate,
```

That object continues over multiple lines. Locate where `fcNewToday:st.fcNewToday` is included in the same returned object. Add `fcReviewedToday:st.fcReviewedToday,` adjacent to it.

If `fcNewToday` is not explicitly serialized in that return value (some apps reconstruct on load), do not invent serialization — `_fcResetDayIfNeeded()` handles staleness on next load.

- [ ] **Step 6: Manual verification**

1. Reload `index.html` with cleared localStorage.
2. Do a flashcard session, rate 3 cards.
3. Console: `st.fcReviewedToday` should be `3`.
4. Console: `st.fcNewDate=''; _fcResetDayIfNeeded();` — `st.fcReviewedToday` should now be `0`.

- [ ] **Step 7: Commit**

```bash
git add index.html
git commit -m "Track daily flashcard reviews for Today stat"
```

---

## Task 3: Add `bumpStreak()` helper and fix streak bug

**Files:**
- Modify: `index.html` — new helper after `STREAK_MILES` at line 2315, plus call sites at lines ~4335 (`showComp`), 3259 (`finishFcSession`), 3811 (`finishSentSession`), 3830 (`finishVerbSession`), 3628 (`finishCaseSession`)

Current bug: streak only ticks inside `showComp()` (lesson completion). Flashcard / verb / sentence / case-drill sessions don't tick it.

- [ ] **Step 1: Add `bumpStreak()` helper**

Find:

```js
const STREAK_MILES=[3,7,14,30,100];
```

Insert immediately after:

```js
const STREAK_MILES=[3,7,14,30,100];
function bumpStreak(){
  const today=new Date().toDateString();
  if(st.lastDate===today)return null;
  const prev=st.streak;
  st.streak++;
  st.lastDate=today;
  return STREAK_MILES.includes(st.streak)&&st.streak>prev?st.streak:null;
}
```

- [ ] **Step 2: Replace inline streak logic in `showComp`**

Find in `showComp()` near line 4335:

```js
  const today=new Date().toDateString();
  let streakHit=null;
  if(st.lastDate!==today){
    const prevStreak=st.streak;st.streak++;st.lastDate=today;
    if(STREAK_MILES.includes(st.streak)&&st.streak>prevStreak)streakHit=st.streak;
  }
```

Replace with:

```js
  const streakHit=bumpStreak();
```

- [ ] **Step 3: Add streak tick to `finishFcSession`**

Find near line 3259:

```js
finishFcSession(){
  const el=document.getElementById('fc-body');
  const pct=st.fcReviewed>0?Math.round(st.fcCorrectCount/st.fcReviewed*100):0;
```

After the `pct` line, insert:

```js
  let streakHit=null;
  if(st.fcReviewed>0){streakHit=bumpStreak();if(streakHit)save();}
```

Then at the very bottom of `finishFcSession()`, just before its closing `},`, insert:

```js
  if(streakHit)setTimeout(()=>showStreakMilestone(streakHit),600);
```

- [ ] **Step 4: Add streak tick to `finishVerbSession`**

Find at line 3830 (`finishVerbSession(){`). Inside the function, after any "if there's no progress, return" guard and before the body that shows the completion UI, insert:

```js
  const streakHit=bumpStreak();
```

At the end of the function (before `},`), insert:

```js
  if(streakHit)setTimeout(()=>showStreakMilestone(streakHit),600);
```

If `bumpStreak()` should only tick on actual engagement (not bailed-out empty sessions), guard it with whatever progress flag the function already uses (look for an `st.vbCorrect` or similar counter at the top of the function — if it's 0, skip the bump).

- [ ] **Step 5: Add streak tick to `finishSentSession`**

Find at line ~3811 (`finishSentSession(){`). Read the function — there should be a "reviewed" or "correct" counter set during the session. At the top of the function (after any early-return guards), insert:

```js
  const streakHit=bumpStreak();
```

At the bottom, before the closing `},`, insert:

```js
  if(streakHit)setTimeout(()=>showStreakMilestone(streakHit),600);
```

If `bumpStreak()` should be guarded against empty sessions (user opened sentences and immediately exited): wrap the call as `const streakHit = (st.sentReviewed > 0) ? bumpStreak() : null;` — substitute `st.sentReviewed` for whichever counter the function actually maintains (grep `st.sent` near line 3811 to find the right one).

- [ ] **Step 6: Add streak tick to `finishCaseSession`**

Find at line ~3628 (`finishCaseSession(){`). Apply the same insertion as Step 5, substituting the case-drill engagement counter (grep `st.cs` near line 3628 to find it).

```js
  const streakHit=bumpStreak();
```

And at the bottom:

```js
  if(streakHit)setTimeout(()=>showStreakMilestone(streakHit),600);
```

Guard with whatever counter exists, e.g., `const streakHit = (st.csReviewed > 0) ? bumpStreak() : null;`

- [ ] **Step 7: Manual verification**

1. Console: `localStorage.clear()` and reload.
2. Console: `st.lastDate='Wed Jan 01 1970'; st.streak=5;` — simulate "yesterday".
3. Do a flashcard session, rate one card, exit. Console: `st.streak` should be `6` and `st.lastDate` should be today's `toDateString()`.
4. Do a second flashcard session same day. Console: `st.streak` should STILL be `6` (only ticks once per day).
5. Repeat with a verb drill and a sentence session — each should also tick the streak if done across a day boundary.

- [ ] **Step 8: Commit**

```bash
git add index.html
git commit -m "Fix streak: count flashcards, verbs, sentences toward streak"
```

---

## Task 4: Add derivation functions for Progress view

**Files:**
- Modify: `index.html` — insert new functions near line 3000 (after `fcTotalCards()`)

Four pure derivation functions. Each takes only inputs needed; no side effects. They're testable from the console with synthetic state.

- [ ] **Step 1: Add `getProgressData()` master function**

Find near line 2999:

```js
function fcTotalCards(){
  const sourceWords=_fcSourceWords();
  let total=sourceWords.length*2;
  VERBS.forEach(v=>{
    const vId='v_'+v.inf;
    if(st.fc[vId+'_se']||st.fc[vId+'_es'])total+=2;
  });
  return total;
}
```

Insert immediately after:

```js
// ═══════════════ PROGRESS VIEW DERIVATIONS ═══════════════

// Bucket each (word,dir) card by SRS state.
// Returns {mastered, familiar, learning, notSeen, total, pctKnown}
function getMasteryBuckets(){
  const sourceWords=UNITS.flatMap(u=>u.words);
  let mastered=0,familiar=0,learning=0,notSeen=0;
  sourceWords.forEach(w=>{
    ['se','es'].forEach(dir=>{
      const c=st.fc[fcKey(w.id,dir)];
      if(!c||(c.due===0&&c.reps===0))notSeen++;
      else if(c.reps>=2&&c.ivl>=21)mastered++;
      else if(c.reps>=2)familiar++;
      else learning++;
    });
  });
  const total=sourceWords.length*2;
  const pctKnown=total>0?Math.round((mastered+familiar)/total*100):0;
  return{mastered,familiar,learning,notSeen,total,pctKnown};
}

// Cards with ≥2 lapses and ≤1 current correct streak. Sorted hardest-first.
// Each entry: {word, dir, key, lapses, streak, views, ease, accuracy}
function getWeakCards(limit){
  const out=[];
  UNITS.flatMap(u=>u.words).forEach(w=>{
    ['se','es'].forEach(dir=>{
      const c=st.fc[fcKey(w.id,dir)];
      if(!c||c.reps===0)return;
      const lapses=c.lapses||0;
      const streak=c.streak||0;
      if(lapses>=2&&streak<=1){
        const views=c.views||0;
        const accuracy=views>0?Math.round((views-lapses)/views*100):0;
        out.push({word:w,dir,key:fcKey(w.id,dir),lapses,streak,views,ease:c.ease,accuracy});
      }
    });
  });
  out.sort((a,b)=>b.lapses-a.lapses||a.streak-b.streak||a.ease-b.ease);
  return limit?out.slice(0,limit):out;
}

// Cards that struggled (≥2 lapses) but are now on a streak (≥3 correct).
function getBouncingBackCards(limit){
  const out=[];
  UNITS.flatMap(u=>u.words).forEach(w=>{
    ['se','es'].forEach(dir=>{
      const c=st.fc[fcKey(w.id,dir)];
      if(!c)return;
      const lapses=c.lapses||0;
      const streak=c.streak||0;
      if(lapses>=2&&streak>=3){
        out.push({word:w,dir,key:fcKey(w.id,dir),lapses,streak});
      }
    });
  });
  out.sort((a,b)=>b.streak-a.streak);
  return limit?out.slice(0,limit):out;
}

// Recent milestones derived from current state. Returns array of
// {icon, title, when} where `when` is a string or null if undatable.
function getRecentWins(buckets){
  const wins=[];
  // Word-mastered milestones (no dates available)
  [10,50,100,250,500].forEach(n=>{
    if(buckets.mastered>=n)wins.push({icon:'✨',title:n+' words mastered',whenRank:n,sortKey:n});
  });
  // Streak milestones the user has actually passed; derive date from current streak
  STREAK_MILES.forEach(n=>{
    if(st.streak>=n){
      let when='';
      if(st.lastDate){
        const last=new Date(st.lastDate);
        const daysAgo=Math.max(0,st.streak-n);
        when=daysAgo===0?'today':daysAgo===1?'yesterday':daysAgo+'d ago';
      }
      wins.push({icon:'⭐',title:n+'-day streak',when,sortKey:1000+n});
    }
  });
  // Units completed — single entry "Latest unit complete" if any
  if(st.completed&&st.completed.length>0){
    const latestId=st.completed[st.completed.length-1];
    const u=UNITS.find(x=>x.id===latestId);
    if(u)wins.push({icon:'🎯',title:'Completed: '+u.t,when:'',sortKey:500});
  }
  // Take top 3 by sortKey desc (highest milestones first)
  wins.sort((a,b)=>b.sortKey-a.sortKey);
  return wins.slice(0,3);
}
```

- [ ] **Step 2: Console verification (no commit yet — used in Task 5)**

1. Open the browser console after reloading.
2. Run `getMasteryBuckets()` — should return an object with sane counts whose total = (vocab × 2).
3. Run `getWeakCards()` — should return `[]` on a fresh state.
4. Run `getBouncingBackCards()` — should return `[]` on a fresh state.
5. Run `getRecentWins(getMasteryBuckets())` — should return `[]` on a fresh state.
6. Manually inject a struggling card: `st.fc['1_se']={ease:2.0,ivl:0,due:Date.now(),reps:1,views:5,lapses:3,streak:1}` then run `getWeakCards()` — should return that card.
7. Change `streak:5`, rerun `getWeakCards()` — should be empty. `getBouncingBackCards()` — should return it.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "Add Progress view derivation functions"
```

---

## Task 5: Add Progress view CSS + chart icon

**Files:**
- Modify: `index.html` — `ICONS` object at line 2280, CSS block near line 395 (where `/* SOCIAL */` is)

- [ ] **Step 1: Add `chart` icon**

Find:

```js
const ICONS={
  home:'<path d="M3 12L12 3l9 9v9a2 2 0 0 1-2 2h-4v-7H10v7H6a2 2 0 0 1-2-2v-9z"/>',
  users:'<path d="M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm0 2c-3.3 0-6 2-6 5v2h12v-2c0-3-2.7-5-6-5zm9-3a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm0 2c-1.3 0-2.5.4-3.4 1A6 6 0 0 1 17 18h5v-2c0-2.5-2-4-4-4z"/>',
```

After the `users` line, insert:

```js
  chart:'<path d="M4 20V10m6 10V4m6 16v-7m6 7V8" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" fill="none"/>',
```

- [ ] **Step 2: Replace SOCIAL CSS block with PROGRESS CSS block**

Find the `/* SOCIAL */` block at line 395 and the lines that follow (the social-specific styles run until the next major comment). Search the file with Grep for `/* SOCIAL */` to find the exact boundary; the block ends where the next CSS section begins (e.g., another comment header or unrelated selector).

Replace the entire SOCIAL CSS block with:

```css
/* PROGRESS */
#progress{background:var(--bg);overflow-y:auto;-webkit-overflow-scrolling:touch;padding-bottom:90px}
.pg-head{display:flex;align-items:center;justify-content:space-between;padding:18px 18px 16px}
.pg-head h2{margin:0;font-size:22px;font-weight:800;color:#fff}
.pg-head .pg-lang{font-size:13px;font-weight:700;opacity:.6}
.pg-hero{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;padding:0 14px 18px}
.pg-stat{background:var(--surface);border-radius:14px;padding:14px 6px;text-align:center}
.pg-stat-i{font-size:22px;margin-bottom:4px}
.pg-stat-v{font-size:24px;font-weight:800;line-height:1;color:#fff;font-feature-settings:'tnum' on}
.pg-stat-l{font-size:10px;color:var(--g5);text-transform:uppercase;letter-spacing:1px;margin-top:4px;font-weight:700}
.pg-section-l{font-size:11px;font-weight:800;color:rgba(255,255,255,.45);text-transform:uppercase;letter-spacing:1.5px;margin:6px 18px 10px}
.pg-card{background:var(--surface);border-radius:14px;padding:14px;margin:0 14px 18px}
.pg-card.glow{box-shadow:0 0 0 1px rgba(88,204,2,.25),0 0 30px rgba(88,204,2,.07)}
.pg-item{display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-top:1px solid rgba(255,255,255,.06)}
.pg-item:first-of-type{border-top:none}
.pg-word{font-size:15px;font-weight:800;color:#fff}
.pg-trans{font-size:12px;color:var(--g4);margin-top:2px}
.pg-meta{font-size:11px;font-weight:700;text-align:right;line-height:1.4}
.pg-meta.bad{color:var(--red)}
.pg-meta.good{color:var(--green)}
.pg-cta{display:block;width:100%;margin-top:14px;padding:12px;border:none;border-radius:12px;color:#fff;font-weight:800;font-size:13px;text-transform:uppercase;letter-spacing:1px;cursor:pointer;background:var(--sr-blue);box-shadow:0 3px 0 var(--sr-blue-d)}
.pg-cta:active{transform:translateY(2px);box-shadow:0 1px 0 var(--sr-blue-d)}
.pg-master-bar{height:10px;border-radius:5px;background:var(--surface-raised);overflow:hidden;display:flex;margin-bottom:8px}
.pg-master-bar > div{height:100%}
.pg-master-pct{font-size:13px;font-weight:700;color:var(--green);text-align:right;margin-bottom:8px}
.pg-bucket-row{display:flex;justify-content:space-between;font-size:13px;padding:5px 0;font-weight:700;color:#fff}
.pg-bucket-row .pg-dot{display:inline-block;width:8px;height:8px;border-radius:4px;margin-right:8px;vertical-align:middle}
.pg-mile-row{display:flex;align-items:center;gap:12px;padding:6px 0}
.pg-mile-i{font-size:22px}
.pg-mile-t{flex:1;font-size:13px;font-weight:700;color:#fff}
.pg-mile-d{font-size:11px;color:var(--g5)}
.pg-empty{text-align:center;color:var(--g4);font-size:13px;padding:30px 18px;font-style:italic}
```

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "Add Progress view styles and chart icon"
```

---

## Task 6: Rebuild Progress screen DOM + bottom nav

**Files:**
- Modify: `index.html` — `#social` block at lines 777-789, bottom-nav references at lines 715, 785, 820, plus `#friend-modal-wrap` if present in `#social`

- [ ] **Step 1: Replace `#social` block with `#progress`**

Find lines 777-789:

```html
<div class="sc" id="social">
  <div class="soc-top">
    <div class="soc-tit">👥 Social</div>
    <div class="soc-sub">See what your friends are up to</div>
  </div>
  <div class="soc-body" id="soc-body"></div>
  <div class="bnav bnav-lt">
    <button class="ni ni-lt" onclick="S.goHome()"><span class="ni-i" data-icon="home"></span><span class="ni-l">Learn</span></button>
    <button class="ni ni-lt act" onclick="S.goSocial()"><span class="ni-i" data-icon="users"></span><span class="ni-l">Social</span></button>
    <button class="ni ni-lt" onclick="S.goProfile()"><span class="ni-i" data-icon="user"></span><span class="ni-l">Profile</span></button>
  </div>
  <div id="fp-modal-wrap"></div>
</div>
```

Replace with:

```html
<div class="sc" id="progress">
  <div class="pg-head">
    <h2>📈 Progress</h2>
    <div class="pg-lang" id="pg-lang"></div>
  </div>
  <div id="pg-body"></div>
  <div class="bnav bnav-lt">
    <button class="ni ni-lt" onclick="S.goHome()"><span class="ni-i" data-icon="home"></span><span class="ni-l">Learn</span></button>
    <button class="ni ni-lt act" onclick="S.goProgress()"><span class="ni-i" data-icon="chart"></span><span class="ni-l">Progress</span></button>
    <button class="ni ni-lt" onclick="S.goProfile()"><span class="ni-i" data-icon="user"></span><span class="ni-l">Profile</span></button>
  </div>
</div>
```

- [ ] **Step 2: Update Home screen bottom nav**

Find line 715:

```html
    <button class="ni" onclick="S.goSocial()"><span class="ni-i" data-icon="users"></span><span class="ni-l">Social</span></button>
```

Replace with:

```html
    <button class="ni" onclick="S.goProgress()"><span class="ni-i" data-icon="chart"></span><span class="ni-l">Progress</span></button>
```

- [ ] **Step 3: Update Profile screen bottom nav**

Find line 820 (within the `#prof` block):

```html
    <button class="ni ni-lt" onclick="S.goSocial()"><span class="ni-i" data-icon="users"></span><span class="ni-l">Social</span></button>
```

Replace with:

```html
    <button class="ni ni-lt" onclick="S.goProgress()"><span class="ni-i" data-icon="chart"></span><span class="ni-l">Progress</span></button>
```

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "Rebuild Progress screen DOM and bottom nav"
```

---

## Task 7: Implement `goProgress()` and `renderProgress()`

**Files:**
- Modify: `index.html` — replace the existing `goSocial()` body and supporting state near line 4677

Delete the existing friend-feed code in this task (`_loadActivities`, `_socCursor`, `_socActivities`, `_socFriendUids`, the `goSocial` body, and the helper functions specific to the social feed).

- [ ] **Step 1: Locate the SOCIAL section**

Find line 4668 (`// ── SOCIAL TAB ──`). The block runs from this comment through the closing of all social-specific methods on `S` (likely up to but not including the next named section like `// ── PROFILE ──`). Search for the next `// ──` divider after line 4668 to find the end.

- [ ] **Step 2: Replace the entire SOCIAL block with PROGRESS**

Delete from `// ── SOCIAL TAB ──` through the line immediately before the next `// ──` divider. Replace with:

```js
// ── PROGRESS TAB ──

goProgress(){
  document.getElementById('pg-lang').innerHTML=langFlag()+' '+esc(langName());
  this.renderProgress();
  this.goScr('progress');
},

renderProgress(){
  const el=document.getElementById('pg-body');
  const buckets=getMasteryBuckets();
  const weak=getWeakCards(5);
  const weakTotal=getWeakCards().length;
  const bouncing=getBouncingBackCards(3);
  const bouncingTotal=getBouncingBackCards().length;
  const wins=getRecentWins(buckets);
  const reviewedToday=st.fcReviewedToday||0;
  let h='';

  // Hero row
  h+='<div class="pg-hero">';
  h+='<div class="pg-stat"><div class="pg-stat-i">🔥</div><div class="pg-stat-v">'+(st.streak||0)+'</div><div class="pg-stat-l">Streak</div></div>';
  h+='<div class="pg-stat"><div class="pg-stat-i">🏆</div><div class="pg-stat-v">'+buckets.mastered+'</div><div class="pg-stat-l">Words</div></div>';
  h+='<div class="pg-stat"><div class="pg-stat-i">⚡</div><div class="pg-stat-v">'+reviewedToday+'</div><div class="pg-stat-l">Today</div></div>';
  h+='</div>';

  // Empty-state shortcut: nothing to show in middle sections AND no progress at all
  const totallyEmpty=buckets.mastered+buckets.familiar+buckets.learning===0;

  // Needs work
  h+='<div class="pg-section-l">Needs work'+(weakTotal>0?' · '+weakTotal+' card'+(weakTotal!==1?'s':''):'')+'</div>';
  h+='<div class="pg-card">';
  if(weak.length===0){
    h+='<div class="pg-empty">'+(totallyEmpty?'Start grading flashcards — tough ones will appear here.':'No tough cards right now. 🎉')+'</div>';
  }else{
    weak.forEach(item=>{
      h+='<div class="pg-item">';
      h+='<div><div class="pg-word">'+esc(item.word.l)+'</div><div class="pg-trans">'+esc(item.word.e)+'</div></div>';
      h+='<div class="pg-meta bad">Failed '+item.lapses+'×<br>'+item.accuracy+'% accuracy</div>';
      h+='</div>';
    });
    h+='<button class="pg-cta" onclick="S.startWeakCardSession()">Practice weak cards →</button>';
  }
  h+='</div>';

  // Bouncing back
  h+='<div class="pg-section-l">📈 Bouncing back'+(bouncingTotal>0?' · '+bouncingTotal+' card'+(bouncingTotal!==1?'s':''):'')+'</div>';
  h+='<div class="pg-card'+(bouncing.length>0?' glow':'')+'">';
  if(bouncing.length===0){
    h+='<div class="pg-empty">Cards you recover from will appear here.</div>';
  }else{
    bouncing.forEach(item=>{
      h+='<div class="pg-item">';
      h+='<div><div class="pg-word">'+esc(item.word.l)+'</div><div class="pg-trans">'+esc(item.word.e)+'</div></div>';
      h+='<div class="pg-meta good">Was failing<br>'+item.streak+' in a row ✓</div>';
      h+='</div>';
    });
  }
  h+='</div>';

  // Mastery
  h+='<div class="pg-section-l">Mastery</div>';
  h+='<div class="pg-card">';
  if(buckets.total===0){
    h+='<div class="pg-empty">No vocabulary loaded for this language yet.</div>';
  }else{
    const pctM=buckets.total>0?(buckets.mastered/buckets.total*100):0;
    const pctF=buckets.total>0?(buckets.familiar/buckets.total*100):0;
    const pctL=buckets.total>0?(buckets.learning/buckets.total*100):0;
    h+='<div class="pg-master-bar">';
    h+='<div style="background:var(--green);width:'+pctM+'%"></div>';
    h+='<div style="background:var(--blue);width:'+pctF+'%"></div>';
    h+='<div style="background:var(--orange);width:'+pctL+'%"></div>';
    h+='</div>';
    h+='<div class="pg-master-pct">'+buckets.pctKnown+'% known</div>';
    h+='<div class="pg-bucket-row"><span><span class="pg-dot" style="background:var(--green)"></span>Mastered</span><span>'+buckets.mastered+'</span></div>';
    h+='<div class="pg-bucket-row"><span><span class="pg-dot" style="background:var(--blue)"></span>Familiar</span><span>'+buckets.familiar+'</span></div>';
    h+='<div class="pg-bucket-row"><span><span class="pg-dot" style="background:var(--orange)"></span>Learning</span><span>'+buckets.learning+'</span></div>';
    h+='<div class="pg-bucket-row"><span><span class="pg-dot" style="background:var(--g6)"></span>Not yet seen</span><span>'+buckets.notSeen+'</span></div>';
  }
  h+='</div>';

  // Recent wins
  h+='<div class="pg-section-l">Recent wins</div>';
  h+='<div class="pg-card">';
  if(wins.length===0){
    h+='<div class="pg-empty">Your milestones will appear here.</div>';
  }else{
    wins.forEach(w=>{
      h+='<div class="pg-mile-row">';
      h+='<div class="pg-mile-i">'+w.icon+'</div>';
      h+='<div class="pg-mile-t">'+esc(w.title)+'</div>';
      h+='<div class="pg-mile-d">'+esc(w.when||'')+'</div>';
      h+='</div>';
    });
  }
  h+='</div>';

  el.innerHTML=h;
},

startWeakCardSession(){
  const weak=getWeakCards();
  if(weak.length===0)return;
  st.fcCards=this.sh(weak.map(item=>({
    word:item.word,
    dir:item.dir,
    key:item.key,
    isNew:false
  })));
  st.fcIdx=0;st.fcFlipped=false;st.fcReviewed=0;st.fcAgainCount=0;st.fcCorrectCount=0;
  this.setLearnMode('flashcards');
  this.goScr('flashcard');
  this.renderFcCard();
},
```

- [ ] **Step 3: Ensure icons render**

Since `renderIcons()` runs once at load (line 4856) and operates on `[data-icon]` elements in the static HTML, the new `data-icon="chart"` markers are picked up automatically. No extra call is needed — verify by reload. If for any reason chart icons don't appear (e.g., elements were dynamically inserted), update `goProgress()` body to call `renderIcons(document.getElementById('progress'))` before `this.goScr('progress')`.

- [ ] **Step 4: Manual verification — fresh state**

1. Console: `localStorage.clear()` and reload.
2. Tap Progress in the bottom nav.
3. Confirm: header shows 📈 Progress + flag/language. Hero row shows 0/0/0. Needs work shows "Start grading flashcards…". Bouncing back shows "Cards you recover from…". Mastery shows full Not-yet-seen count + 0% known. Recent wins shows "Your milestones will appear here."
4. Confirm bottom nav highlights Progress with the chart icon.

- [ ] **Step 5: Manual verification — populated state**

1. From Home, do a flashcard session and rate several cards (mix of ratings).
2. Tap Progress.
3. Hero "Today" shows the count of cards graded.
4. Inject a weak card via console: `st.fc[Object.keys(st.fc)[0]]={...st.fc[Object.keys(st.fc)[0]],lapses:3,streak:0,reps:1,views:5}; S.renderProgress();` — confirm it appears in Needs work with the right "Failed 3× / accuracy" line.
5. Bump that same card to `streak:5`: it should disappear from Needs work and appear in Bouncing back with green glow.

- [ ] **Step 6: Manual verification — language switch**

1. Switch to Italian (or whichever non-current language has vocab).
2. Tap Progress. The header flag/language should update, and bucket counts should reflect Italian vocabulary, not Serbian.

- [ ] **Step 7: Commit**

```bash
git add index.html
git commit -m "Implement Progress screen rendering and weak-card practice"
```

---

## Task 8: Remove dead Social-only code

**Files:**
- Modify: `index.html` — search for orphan references

After Task 7 replaced the SOCIAL TAB block with the PROGRESS TAB block, hunt for leftover references that no longer make sense.

- [ ] **Step 1: Grep for orphan symbols**

Run from the project root:

```bash
grep -n "goSocial\|_socActivities\|_socCursor\|_socFriendUids\|_loadActivities\|soc-body\|soc-top\|soc-tit\|soc-sub\|fp-modal-wrap" index.html
```

Each remaining match should be intentional or removed. Expected outcomes per symbol:
- `goSocial` — all replaced with `goProgress`.
- `_socActivities`, `_socCursor`, `_socFriendUids`, `_loadActivities` — should be 0 matches (entirely removed in Task 7).
- `soc-body`, `soc-top`, `soc-tit`, `soc-sub` — CSS classes; should also be gone after Task 5's CSS block replacement.
- `fp-modal-wrap` — this is the friend-PROFILE modal wrapper. If it's referenced by Profile-side friend-management code (likely), KEEP IT. The original was duplicated in both `#social` and `#prof`. We're only removing the `#social` instance.

- [ ] **Step 2: If any orphans remain, remove them**

For each lingering reference: read the surrounding code. If it's only-callable from the removed Social tab (e.g., a `_socScrollHandler`), delete it. If it's also used by Profile's friend-list features, leave it.

- [ ] **Step 3: Manual sanity pass**

1. Reload, click around: Home, Progress, Profile.
2. Open Profile, exercise friend-related features (add friend, view a friend profile) — confirm they still work.
3. Console: no errors.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "Remove dead Social-tab feed code"
```

---

## Task 9: Visual & smoke verification end-to-end

**Files:** None (verification only)

- [ ] **Step 1: Cross-language smoke**

1. Clear localStorage, reload.
2. Switch to each available language. Tap Progress. Confirm header text + bucket totals scale to that language's vocab.

- [ ] **Step 2: Streak fix verification**

1. Clear localStorage, reload.
2. Set `st.lastDate='Wed Jan 01 1970'; st.streak=0; save();` in console.
3. Do a flashcard session — rate at least one card. Exit.
4. Console: `st.streak` should be `1`. `st.lastDate` should be today's `toDateString()`.
5. Set `st.lastDate='Wed Jan 01 1970';` again. Reload (forces load-time staleness check).
6. Confirm `st.streak` is now `0` (gap was >1 day → reset). The reset logic at line 2555 should trigger.

- [ ] **Step 3: "Practice weak cards" CTA flow**

1. Console: inject three weak cards as in Task 7 Step 5.
2. Tap Progress → Practice weak cards.
3. Should land in a flashcard session containing exactly those cards. Rate them. After session, exit.
4. Tap Progress again — Needs work should reflect the updated state (cards that got correct streaks may have moved to Bouncing back or out entirely).

- [ ] **Step 4: Mobile viewport pass**

1. In Chrome DevTools, switch to a phone viewport (iPhone 14 or similar).
2. Confirm Progress screen scrolls smoothly with all sections visible.
3. Confirm hero stat cards don't overflow.
4. Confirm bottom nav doesn't obscure the last section (padding-bottom on `#progress` should handle this).

- [ ] **Step 5: No-commit checkpoint**

This task is verification only. No commit unless a bug is found and fixed.

---

## Task 10: Merge branch and deploy to zeka.one

**Files:** Repo root, GitHub remote

This deploys via the existing GitHub Pages setup. `CNAME` is already `zeka.one`. We assume Pages serves from `main` — verify before pushing.

- [ ] **Step 1: Verify the deploy branch**

```bash
git -C /c/Users/rober/OneDrive/Desktop/SerbianDuolingo/.claude/worktrees/serene-pascal-1a4b6a remote -v
# Confirm origin points to the expected GitHub repo.
gh api repos/{owner}/{repo}/pages --jq '.source.branch'
# Expected: "main" (or "master" — adjust subsequent steps if so)
```

If Pages serves from a different branch (e.g., `gh-pages`), pause and confirm with the user before merging.

- [ ] **Step 2: Confirm uncommitted icon PNG changes are excluded**

The user said to leave icon-192.PNG and icon-512.PNG out of this deploy. The worktree shows them as modified. Ensure none of the prior task commits accidentally staged them:

```bash
git -C /c/Users/rober/OneDrive/Desktop/SerbianDuolingo/.claude/worktrees/serene-pascal-1a4b6a status --short
# Expected: " M icon-192.PNG" and " M icon-512.PNG" still appearing as UNSTAGED.
```

- [ ] **Step 3: Switch to main and merge**

From the main worktree (not this feature worktree — the user has a separate main checkout). If unsure where main lives, ask the user. Otherwise:

```bash
# From the main checkout directory:
git fetch origin
git checkout main
git pull --ff-only origin main
git merge --no-ff claude/serene-pascal-1a4b6a -m "Merge Progress view + streak fix"
```

- [ ] **Step 4: Push**

```bash
git push origin main
```

GitHub Pages will pick up the change within ~1 minute.

- [ ] **Step 5: Verify live site**

1. Wait ~60 seconds.
2. Open https://zeka.one in a private/incognito window.
3. Confirm the Progress tab appears in the bottom nav with a chart icon.
4. Confirm flashcard sessions still work, "Seen N×" counter still shows, and Progress screen populates.

- [ ] **Step 6: Confirm with user**

Report back to the user with the live URL and a brief summary of what shipped.

---

## Self-Review Notes

Coverage check vs spec:
- ✅ Replace Social tab → Tasks 6, 7, 8
- ✅ Per-language only → derivations use `UNITS` which is set by `setLang()`
- ✅ Hero row (Streak / Words / Today) → Task 7
- ✅ Needs work + "Practice weak cards" CTA → Tasks 4, 7
- ✅ Bouncing back with green glow → Tasks 4, 5, 7
- ✅ Mastery bucket bar + counts → Tasks 4, 7
- ✅ Recent wins (datable + undatable) → Task 4, 7
- ✅ `lapses` + `streak` per-card → Task 1
- ✅ Daily reviewed counter → Task 2
- ✅ `bumpStreak()` from all four exit points → Task 3
- ✅ Friend-feed code deletion → Tasks 7, 8
- ✅ Deploy → Task 10

Outstanding ambiguity that may need user input during execution:
- Verb/sentence/case "engagement guards" (Task 3 steps 4-5) depend on actual variable names in those functions. The executor should `grep` for `st.vbReviewed`, `st.sentReviewed`, `st.csReviewed` (or similar) and apply the guard. If no such counter exists, defer to "called only if the user reached the finish handler" (which already implies engagement).
- The exact location of the main worktree (Task 10 step 3) is unknown. The executor should ask.
