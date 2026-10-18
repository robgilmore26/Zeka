# Cross-Subject Match Exercise — Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development to execute task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Add a standalone match-the-words exercise that pulls from the user's full vocabulary (not subject/lesson-specific), as a complement to flashcards.

**Design summary:**
- New segment on the Learn screen: `Lessons | Flashcards | Match | Verbs | Sentences`.
- Session = 5 rounds × 5 pairs (25 total words).
- Pair direction is mixed (some rounds SR→EN, some EN→SR), 50/50.
- Pair selection weighted toward weak/due cards, topped up from any seen card (`reps ≥ 1`).
- No SRS impact (this is a reinforcement game, not a graded test). XP earned per round, streak credit on session completion.
- Empty state if <10 eligible cards: "Finish a few flashcards first to unlock matching."
- After a completed flashcard session, surface a "Try matching →" CTA on the completion screen.

**Architecture:** Reuses the existing matching DOM/CSS (`.mb`, `.mcon`, `.sel`, `.ok`, `.bad`) from the lesson matching exercise. Adds a new "match home" screen and a session screen. Session state held on `st.mc*` keys (mc = "match cross-subject"); per-round state continues to use `st.matchSt`.

**Tech Stack:** Single-file vanilla JS, no build step. All work in `index.html`.

---

## Task 1: Add pair-selection logic

**Files:** Modify `index.html` — insert helpers next to the Progress derivation functions (around line 3110).

- [ ] **Step 1: Add `_mcEligibleCards()` helper**

Insert near other derivation functions (search for `getRecentWins` function end around line 3110):

```js
// ═══════════════ MATCH (cross-subject) ═══════════════

// Returns array of {word, key, ease, due, lapses, streak, weight}
// sorted by weight desc (higher = more deserving of reinforcement).
function _mcEligibleCards(){
  const now=Date.now();
  const out=[];
  UNITS.flatMap(u=>u.words).forEach(w=>{
    // Use 'se' direction for canonical card lookup; we don't need both
    // dirs in match (the round randomizes which side shows source vs english)
    const c=st.fc[fcKey(w.id,'se')];
    if(!c||c.reps===0)return;
    const lapses=c.lapses||0;
    const streak=c.streak||0;
    const dueOverdue=c.due&&c.due<=now?1:0;
    // Weight: weak cards first, then due, then everything else.
    // (lapses-streak) is positive for struggling cards.
    const weight=(lapses-streak)*4+dueOverdue*3+(1/(c.ease||2.5));
    out.push({word:w,key:fcKey(w.id,'se'),ease:c.ease,due:c.due,lapses,streak,weight});
  });
  out.sort((a,b)=>b.weight-a.weight);
  return out;
}

// Build a session: 5 rounds × 5 pairs. Each round has a random direction.
// Returns null if not enough eligible cards (need ≥10 to unlock).
function buildMatchSession(){
  const eligible=_mcEligibleCards();
  if(eligible.length<10)return null;
  // Take up to 25, with some randomization within the top half so it's not identical session-to-session
  const topHalf=eligible.slice(0,Math.max(25,Math.floor(eligible.length/2)));
  const picked=[];
  const pool=[...topHalf];
  while(picked.length<25&&pool.length>0){
    // Bias: ~70% chance pick from top 5 of pool, else random
    const idx=Math.random()<0.7?Math.min(Math.floor(Math.random()*5),pool.length-1):Math.floor(Math.random()*pool.length);
    picked.push(pool.splice(idx,1)[0]);
  }
  // If we have fewer than 25 eligible, just use what we have (in groups of 5; trim if odd)
  const groupSize=5;
  const groupCount=Math.floor(picked.length/groupSize);
  if(groupCount===0)return null;
  const rounds=[];
  for(let i=0;i<groupCount;i++){
    const group=picked.slice(i*groupSize,(i+1)*groupSize);
    // Random direction per round: 'se' = source→english, 'es' = english→source
    const dir=Math.random()<0.5?'se':'es';
    rounds.push({
      pairs:group.map(g=>({id:g.word.id,l:g.word.l,e:g.word.e})),
      dir
    });
  }
  return rounds;
}
```

- [ ] **Step 2: Commit**

```bash
git add index.html
git commit -m "Add match-exercise pair selection logic"
```

---

## Task 2: Add Match screen DOM + CSS + nav segment

**Files:** Modify `index.html` — segment toggle, two new `<div class="sc">` screens, CSS.

- [ ] **Step 1: Update the learn-toggle segment**

Find line 692:

```html
<div class="seg-toggle seg-toggle-4" id="learn-toggle">
  <button class="seg-btn seg-active" onclick="S.setLearnMode('lessons')">Lessons</button>
  <button class="seg-btn" onclick="S.setLearnMode('flashcards')">Flashcards</button>
  <button class="seg-btn" onclick="S.setLearnMode('verbs')">Verbs</button>
  <button class="seg-btn" onclick="S.setLearnMode('sentences')">Sentences</button>
</div>
```

Replace with:

```html
<div class="seg-toggle seg-toggle-5" id="learn-toggle">
  <button class="seg-btn seg-active" onclick="S.setLearnMode('lessons')">Lessons</button>
  <button class="seg-btn" onclick="S.setLearnMode('flashcards')">Flashcards</button>
  <button class="seg-btn" onclick="S.setLearnMode('match')">Match</button>
  <button class="seg-btn" onclick="S.setLearnMode('verbs')">Verbs</button>
  <button class="seg-btn" onclick="S.setLearnMode('sentences')">Sentences</button>
</div>
```

- [ ] **Step 2: Add `seg-toggle-5` CSS**

Find line 434:

```css
.seg-toggle-4 .seg-btn{font-size:11px;padding:8px 2px;letter-spacing:.2px}
```

Add immediately after:

```css
.seg-toggle-5 .seg-btn{font-size:10px;padding:8px 1px;letter-spacing:0}
```

- [ ] **Step 3: Add match-home container**

Find line 699:

```html
<div id="fc-home" style="display:none;flex:1;overflow-y:auto;padding:14px 22px 100px"></div>
```

Insert immediately after:

```html
<div id="match-home" style="display:none;flex:1;overflow-y:auto;padding:14px 22px 100px"></div>
```

- [ ] **Step 4: Add the match-game screen**

Find the flashcard screen `<div class="sc" id="flashcard">` (around line 739) and observe its structure. After the flashcard screen block closes (and the case screen `<div class="sc" id="case">` if present), add a new screen. Look for an appropriate insertion point near the existing per-exercise screens. Insert:

```html
<div class="sc" id="match-game">
  <div class="hdr"><div class="st">
    <button class="xbtn" onclick="S.exitMatch()"><span data-icon="x"></span></button>
    <div style="flex:1;text-align:center"><div id="mc-count" style="font-size:13px;font-weight:700;color:rgba(255,255,255,.7)">1 / 5</div></div>
    <div style="width:32px"></div>
  </div></div>
  <div id="mc-body" style="flex:1;overflow-y:auto;padding:14px 22px"></div>
</div>
```

- [ ] **Step 5: Commit**

```bash
git add index.html
git commit -m "Add Match nav segment, home container, and game screen"
```

---

## Task 3: Implement `setLearnMode('match')` + match-home rendering

**Files:** Modify `index.html` — extend `setLearnMode`, add `renderMatchHome` method on `S`.

- [ ] **Step 1: Extend `setLearnMode`**

Find:

```js
setLearnMode(mode){
  const modes=['lessons','flashcards','verbs','sentences'];
```

Change `modes` to include `'match'` between `'flashcards'` and `'verbs'`:

```js
  const modes=['lessons','flashcards','match','verbs','sentences'];
```

And in the `containers` object (a few lines below):

```js
  const containers={lessons:document.getElementById('hscr'),flashcards:document.getElementById('fc-home'),verbs:document.getElementById('grammar-home'),sentences:document.getElementById('sentence-home')};
```

Change to:

```js
  const containers={lessons:document.getElementById('hscr'),flashcards:document.getElementById('fc-home'),match:document.getElementById('match-home'),verbs:document.getElementById('grammar-home'),sentences:document.getElementById('sentence-home')};
```

And in the `renderNew` function add a match render call:

```js
    if(mode==='flashcards'&&typeof this.renderFcHome==='function')this.renderFcHome();
    if(mode==='match'&&typeof this.renderMatchHome==='function')this.renderMatchHome();
    if(mode==='verbs')this.setGrammarMode(st.grammarMode||'verbs');
    if(mode==='sentences')this.renderSentHome();
```

- [ ] **Step 2: Add `renderMatchHome` method**

Find the existing `renderFcHome()` method (around line 3162 — search for `renderFcHome(){`). Insert a new method immediately after `renderFcHome` (and its closing `},`). The new method:

```js
renderMatchHome(){
  const el=document.getElementById('match-home');
  const eligible=_mcEligibleCards();
  const count=eligible.length;
  let h='<div style="text-align:center;padding:14px 0 0">';
  h+='<div style="font-size:48px;margin-bottom:8px">🧩</div>';
  h+='<div style="font-size:22px;font-weight:800;color:#fff">Match the words</div>';
  h+='<div style="font-size:13px;color:rgba(255,255,255,.6);margin-top:6px">Pair words with their translations across your full vocabulary.</div>';
  if(count<10){
    h+='<div style="margin-top:24px;padding:24px;background:var(--surface);border-radius:14px;color:rgba(255,255,255,.7);font-size:13px;line-height:1.6">';
    h+='Finish a few flashcards first to unlock matching.<br><span style="color:var(--g5);font-size:12px">You have '+count+' card'+(count!==1?'s':'')+' ready · need at least 10.</span>';
    h+='</div>';
    h+='<button style="margin-top:20px;width:100%;padding:16px;border:none;border-radius:16px;font-size:16px;font-weight:800;cursor:pointer;text-transform:uppercase;letter-spacing:1px;color:#fff;background:var(--sr-blue);box-shadow:0 4px 0 var(--sr-blue-d)" onclick="S.setLearnMode(\'flashcards\')">Go to flashcards →</button>';
  }else{
    h+='<div style="margin-top:24px;padding:18px;background:var(--surface);border-radius:14px;font-size:13px;color:rgba(255,255,255,.7);line-height:1.6">';
    h+='<div style="font-size:28px;font-weight:800;color:#fff;line-height:1">'+count+'</div>';
    h+='<div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;font-weight:700;color:var(--g5);margin-top:4px">Words ready</div>';
    h+='<div style="margin-top:14px">Each session: <strong style="color:#fff">5 rounds × 5 pairs</strong>, weighted toward words you\'ve struggled with.</div>';
    h+='</div>';
    h+='<button style="margin-top:20px;width:100%;padding:16px;border:none;border-radius:16px;font-size:16px;font-weight:800;cursor:pointer;text-transform:uppercase;letter-spacing:1px;color:#fff;background:var(--green);box-shadow:0 4px 0 var(--green-d)" onclick="S.startMatchSession()">Start matching</button>';
  }
  h+='</div>';
  el.innerHTML=h;
},
```

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "Wire Match into setLearnMode and add home screen"
```

---

## Task 4: Implement match session — start, render round, tap, complete

**Files:** Modify `index.html` — add session methods on `S` next to existing match methods (around line 4301, `rMa`).

- [ ] **Step 1: Add session-control methods on `S`**

Find the existing matching code:

```js
// MATCH
rMa(b,ex){
  st.matchSt={sel:null,selT:null,matched:[],err:0};
```

Insert these methods BEFORE the `// MATCH` comment (or anywhere logical on the `S` object — placement before `rMa` keeps related code together):

```js
// ── CROSS-SUBJECT MATCH ──

startMatchSession(){
  const rounds=buildMatchSession();
  if(!rounds||rounds.length===0){this.toast('Not enough cards yet');return;}
  st.mcRounds=rounds;
  st.mcIdx=0;
  st.mcCorrect=0;
  st.mcReviewed=0;
  st.mcXp=0;
  this.goScr('match-game');
  this.renderMatchRound();
},

renderMatchRound(){
  if(st.mcIdx>=st.mcRounds.length){this.finishMatchSession();return;}
  const round=st.mcRounds[st.mcIdx];
  document.getElementById('mc-count').textContent=(st.mcIdx+1)+' / '+st.mcRounds.length;
  st.matchSt={sel:null,selT:null,matched:[],err:0};
  // Direction: 'se' = source words on left, english on right (tap source first then english)
  //            'es' = english on left, source on right (tap english first then source)
  const isSE=round.dir==='se';
  const leftText=isSE?'l':'e';
  const rightText=isSE?'e':'l';
  const leftType='s';// keep matching the existing mTap logic: first column = type 's'
  const rightType='e';// second column = type 'e'
  const sC=this.sh(round.pairs.map(p=>({t:p[leftText],k:p.id})));
  const eC=this.sh(round.pairs.map(p=>({t:p[rightText],k:p.id})));
  const dirLabel=isSE?(langName()+' → English'):('English → '+langName());
  let h=`<div class="lcont"><div class="exq">Match the pairs</div>
    <div class="exsub">${esc(dirLabel)}</div><div class="mcon">`;
  sC.forEach(it=>{h+=`<button class="mb" data-t="${leftType}" data-k="${it.k}" onclick="S.mcTap(this)">${esc(it.t)}</button>`;});
  eC.forEach(it=>{h+=`<button class="mb" data-t="${rightType}" data-k="${it.k}" onclick="S.mcTap(this)">${esc(it.t)}</button>`;});
  h+=`</div></div><div class="fbar" id="fbar" style="display:none"></div>`;
  document.getElementById('mc-body').innerHTML=h;
},

mcTap(el){
  const ms=st.matchSt;if(!ms)return;
  const t=el.dataset.t,k=+el.dataset.k;
  if(ms.matched.includes(k))return;sCl();
  if(!ms.sel){ms.sel=el;ms.selT=t;el.classList.add('sel');}
  else if(ms.selT===t){ms.sel.classList.remove('sel');ms.sel=el;ms.selT=t;el.classList.add('sel');}
  else{
    if(+ms.sel.dataset.k===k){
      sMa();
      ms.matched.push(k);
      ms.sel.classList.remove('sel');ms.sel.classList.add('ok');el.classList.add('ok');
      ms.sel=null;ms.selT=null;
      const round=st.mcRounds[st.mcIdx];
      if(ms.matched.length===round.pairs.length){
        // Round complete
        const perf=ms.err===0;
        const xp=perf?15:8;
        st.mcXp+=xp;
        st.mcReviewed+=round.pairs.length;
        if(perf)st.mcCorrect++;
        sOk();
        setTimeout(()=>{st.mcIdx++;this.renderMatchRound();},700);
      }
    }else{
      ms.err++;el.classList.add('bad');ms.sel.classList.add('bad');ms.sel.classList.remove('sel');sNo();
      const prev=ms.sel;setTimeout(()=>{el.classList.remove('bad');prev.classList.remove('bad');},350);
      ms.sel=null;ms.selT=null;
    }
  }
},

finishMatchSession(){
  let streakHit=null;
  if(st.mcReviewed>0){streakHit=bumpStreak();st.xp+=st.mcXp;save();}
  const totalRounds=st.mcRounds.length;
  const perfectRounds=st.mcCorrect;
  const xpEarned=st.mcXp;
  let h='<div style="text-align:center;padding:30px 20px;display:flex;flex-direction:column;align-items:center;gap:14px">';
  h+=zekaHtml(perfectRounds===totalRounds?'Flawless!':perfectRounds>=totalRounds*0.7?'Nice work!':'Keep going!');
  h+='<div style="font-size:22px;font-weight:800;color:#fff">Session Complete!</div>';
  h+='<div style="display:flex;gap:20px;justify-content:center">';
  h+='<div style="text-align:center"><div style="font-size:28px;font-weight:800;color:var(--green)">'+perfectRounds+'/'+totalRounds+'</div><div style="font-size:11px;color:rgba(255,255,255,.5);font-weight:700">PERFECT ROUNDS</div></div>';
  h+='<div style="text-align:center"><div style="font-size:28px;font-weight:800;color:var(--gold)">+'+xpEarned+'</div><div style="font-size:11px;color:rgba(255,255,255,.5);font-weight:700">XP</div></div>';
  h+='</div>';
  h+='<button style="width:100%;max-width:360px;padding:16px;border:none;border-radius:16px;font-size:16px;font-weight:800;cursor:pointer;text-transform:uppercase;letter-spacing:1px;color:#fff;background:var(--green);box-shadow:0 4px 0 var(--green-d)" onclick="S.exitMatch()">Done</button>';
  h+='</div>';
  document.getElementById('mc-body').innerHTML=h;
  sDn();
  if(streakHit)setTimeout(()=>showStreakMilestone(streakHit),600);
},

exitMatch(){
  sCl();
  this.goHome();
  this.setLearnMode('match');
},
```

- [ ] **Step 2: Commit**

```bash
git add index.html
git commit -m "Implement match session: start, round, tap, complete"
```

---

## Task 5: Add "Try matching →" CTA on flashcard completion

**Files:** Modify `index.html` — update `finishFcSession` to show an additional CTA when eligible.

- [ ] **Step 1: Update `finishFcSession`**

Find the section of `finishFcSession` that renders the Done button (search for `'<button style="width:100%;max-width:360px;padding:16px;border:none;border-radius:16px;font-size:16px;font-weight:800;cursor:pointer;text-transform:uppercase;letter-spacing:1px;color:#fff;background:var(--green);box-shadow:0 4px 0 var(--green-d)" onclick="S.exitFc()">Done</button>'`).

Replace that single Done button line with two buttons in a column:

```js
  h+='<div style="display:flex;flex-direction:column;gap:10px;width:100%;max-width:360px;margin-top:8px">';
  // Show Match CTA if there are enough eligible cards
  if(typeof _mcEligibleCards==='function'&&_mcEligibleCards().length>=10){
    h+='<button style="width:100%;padding:14px;border:none;border-radius:14px;font-size:14px;font-weight:800;cursor:pointer;text-transform:uppercase;letter-spacing:1px;color:#fff;background:var(--sr-blue);box-shadow:0 3px 0 var(--sr-blue-d)" onclick="S.exitFc();setTimeout(()=>{S.setLearnMode(\'match\');S.startMatchSession();},300)">🧩 Try matching →</button>';
  }
  h+='<button style="width:100%;padding:16px;border:none;border-radius:16px;font-size:16px;font-weight:800;cursor:pointer;text-transform:uppercase;letter-spacing:1px;color:#fff;background:var(--green);box-shadow:0 4px 0 var(--green-d)" onclick="S.exitFc()">Done</button>';
  h+='</div>';
```

- [ ] **Step 2: Commit**

```bash
git add index.html
git commit -m "Add Try matching CTA on flashcard session complete"
```

---

## Task 6: Smoke verify (manual) + merge + deploy

- [ ] **Step 1: Manual smoke**

In a browser:
1. Reload zeka.one (after Task 5 commits).
2. Go to Learn → Match. With < 10 seen cards, see "Finish a few flashcards first to unlock matching." With ≥ 10, see "X words ready" + "Start matching".
3. Tap Start matching. Round 1/5 shows two columns of 5 buttons. Header shows "1 / 5".
4. Make a wrong match: both buttons flash red briefly. Make a right match: both go green.
5. Complete a full round: a brief OK sound, advance to round 2/5.
6. Complete all 5 rounds: see completion screen with "X/5 perfect rounds" and "+N XP". Tap Done.
7. Streak should tick if it hadn't already today.
8. Go do a flashcard session. On the Session Complete screen, see "🧩 Try matching →" above the Done button (if eligible).

- [ ] **Step 2: Cherry-pick all six commits onto main, push**

```bash
git -C <main-worktree-path> cherry-pick <task1-sha>..<task5-sha>
git -C <main-worktree-path> push origin main
```

(Or use a range / individual cherry-picks if the implementer prefers.)

---

## Self-review

- ✅ Match seg-btn appears at index 2 (between Flashcards and Verbs) — matches user description "after flashcards"
- ✅ Word pool uses `reps ≥ 1` — words user has actually been introduced to
- ✅ 5 rounds × 5 pairs — matches user-confirmed option
- ✅ Direction mixed (50/50 per round) — matches user choice
- ✅ Weighted selection — matches user choice
- ✅ Streak tick on completion via `bumpStreak()` consistent with other session-finishers
- ✅ XP awarded but NO SRS card-state changes — clean separation
- ✅ Empty state with helpful message if < 10 eligible cards
- ✅ CTA on flashcard session completion to flow into matching
- ✅ Uses existing `.mb` / `.mcon` / `.sel` / `.ok` / `.bad` CSS — no new visual identity needed

Out of scope (potential future):
- Daily match-completed indicator on Progress screen
- Per-language match stats
- "Hard mode" with 6 pairs per round or shorter timer
- Direction selection toggle (currently always Mixed)
