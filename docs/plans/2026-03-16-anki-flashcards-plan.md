# Anki-Style Flashcard Feature — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add SM-2 spaced repetition flashcards to Zeka with a toggle on the LEARN tab, and simplify the header.

**Architecture:** Single-file PWA (index.html). All changes in one file. Flashcard state (`st.fc`) stored alongside existing state in localStorage + Firestore. SM-2 algorithm implemented as pure functions. Flashcard UI reuses existing screen pattern (`.sc` class) with a new `#flashcard` screen. The LEARN tab gets a segmented toggle; the old REVIEW tab is removed.

**Tech Stack:** Vanilla JS, CSS3 (3D transforms for card flip), Firebase Firestore, existing `speak()` TTS system.

---

### Task 1: Simplify Header — Remove XP/Hearts, Move Streak

**Files:**
- Modify: `index.html:452-457` (header HTML)
- Modify: `index.html:61-62` (header CSS)
- Modify: `index.html:2010-2014` (`updH` function)

**Step 1: Update header HTML**

Change lines 452-457 from:
```html
<div class="st"><button class="lang-ind" id="h-lang" onclick="S.switchLang()" title="Switch language"><img ...></button><span class="elo-badge" id="h-elo">1000</span></div>
<div class="hdr-stats">
  <div class="st" style="color:var(--orange)"><span class="st-i">🔥</span><span id="h-str">0</span></div>
  <div class="st" style="color:var(--gold)"><span class="st-i">⚡</span><span id="h-xp">0</span></div>
  <div class="st" style="color:var(--red)"><span class="st-i">❤️</span><span id="h-hrt">5</span></div>
</div>
```

To:
```html
<div class="st"><button class="lang-ind" id="h-lang" onclick="S.switchLang()" title="Switch language"><img src="https://flagcdn.com/w40/rs.png" alt="🇷🇸" style="height:18px;vertical-align:middle"></button><span class="elo-badge" id="h-elo">1000</span><div class="st" style="color:var(--orange);margin-left:10px"><span class="st-i">🔥</span><span id="h-str">0</span></div></div>
```

**Step 2: Update `updH` JS function**

Change `updH` (~line 2010) to remove references to `h-xp` and `h-hrt`:
```javascript
updH(){document.getElementById('h-elo').textContent=st.elo;
  document.getElementById('h-str').textContent=st.streak;
  const hl=document.getElementById('h-lang');hl.innerHTML=langFlag();hl.title=langName();},
```

**Step 3: Remove `hdr-stats` div and its CSS**

Remove the `.hdr-stats` CSS rule at line 62. The `hdr-stats` div is gone from the HTML so no longer needed.

**Step 4: Commit**
```
git add index.html && git commit -m "Simplify header: remove XP/hearts, keep streak next to ELO"
```

---

### Task 2: Remove REVIEW Tab, Add Segmented Toggle to LEARN Tab

**Files:**
- Modify: `index.html:460-466` (home screen nav bar — remove Review button)
- Modify: `index.html:490-502` (remove `#review` screen HTML entirely)
- Modify: `index.html:298-325` (remove review CSS)
- Modify: `index.html:2370-2450` (remove `goReview`, `rvCard`, `startReview`, `genReviewEx`, `startRandomPractice` JS)
- Modify: all other nav bars (lines ~496-501, ~510-514, ~546-550) — remove Review button from Social/Profile nav bars
- Add: segmented toggle HTML inside `#home` screen, between header and scroll area

**Step 1: Remove the `#review` screen HTML (lines 490-502)**

Delete the entire `<div class="sc" id="review">...</div>` block.

**Step 2: Remove Review nav buttons from ALL nav bars**

In each `.bnav`, remove the line:
```html
<button class="ni" onclick="S.goReview()">...</button>
```

This appears in the home, social, and profile nav bars. Update grid from 4 columns to 3.

**Step 3: Remove Review CSS (lines 298-325)**

Delete all CSS rules starting with `#review`, `.rvtop`, `.rvtit`, `.rvsub`, `.rvbody`, `.rv-empty`, `.rv-sect`, `.rv-word`, `.rv-em`, `.rv-inf`, `.rv-sr`, `.rv-en`, `.rv-stats`, `.rv-stat`, `.rv-btn`.

**Step 4: Remove Review JS functions**

Delete `goReview()`, `rvCard()`, `startReview()`, `genReviewEx()`, `startRandomPractice()` (~lines 2370-2450).

**Step 5: Add segmented toggle to LEARN tab**

Insert between the `<div class="hdr">` and `<div class="hscr">` in the `#home` screen:
```html
<div class="seg-toggle" id="learn-toggle">
  <button class="seg-btn seg-active" onclick="S.setLearnMode('lessons')">Lessons</button>
  <button class="seg-btn" onclick="S.setLearnMode('flashcards')">Flashcards</button>
</div>
```

**Step 6: Add segmented toggle CSS**
```css
.seg-toggle{display:flex;margin:8px 20px;background:var(--g1);border-radius:12px;padding:3px;gap:2px}
.seg-btn{flex:1;padding:8px 0;border:none;border-radius:10px;font-size:13px;font-weight:700;cursor:pointer;background:transparent;color:var(--g5);transition:.2s}
.seg-btn.seg-active{background:#fff;color:var(--g7);box-shadow:0 1px 3px rgba(0,0,0,.1)}
```

**Step 7: Add JS for toggle**
```javascript
setLearnMode(mode){
  document.querySelectorAll('.seg-btn').forEach((b,i)=>{
    b.classList.toggle('seg-active',i===(mode==='lessons'?0:1));
  });
  document.getElementById('hscr').style.display=mode==='lessons'?'':'none';
  document.getElementById('fc-home').style.display=mode==='flashcards'?'':'none';
  if(mode==='flashcards')this.renderFcHome();
},
```

**Step 8: Add flashcard home container in `#home` screen**

After `<div class="hscr" id="hscr"></div>`, add:
```html
<div id="fc-home" style="display:none;flex:1;overflow-y:auto;padding:14px 22px 100px"></div>
```

**Step 9: Commit**
```
git add index.html && git commit -m "Remove Review tab, add Lessons/Flashcards toggle on LEARN tab"
```

---

### Task 3: Add Flashcard State to Data Model

**Files:**
- Modify: `index.html:1955-1956` (add `fc:{}` to `st` initial state)
- Modify: `index.html:1680-1682` (`getStateData` — include `fc`)
- Modify: `index.html:1684-1689` (`applyStateData` — restore `fc`)

**Step 1: Add `fc` to initial state**

Change line 1955-1956:
```javascript
let st={elo:1000,xp:0,streak:0,lastDate:null,hearts:5,completed:[],ws:{},fc:{},
  unit:null,ei:0,exs:[],lxp:0,lcor:0,ltot:0,lelo:0,selIdx:-1,answered:false,matchSt:null,wbAns:[],wbUsed:null};
```

**Step 2: Update `getStateData`**

```javascript
function getStateData(){
  return{elo:st.elo,xp:st.xp,streak:st.streak,lastDate:st.lastDate,
    completed:st.completed,ws:st.ws,hearts:st.hearts,fc:st.fc};
}
```

**Step 3: Update `applyStateData`**

Add `st.fc=p.fc||{};` to the function:
```javascript
function applyStateData(p){
  st.elo=p.elo||1000;st.xp=p.xp||0;st.streak=p.streak||0;st.lastDate=p.lastDate||null;
  st.completed=p.completed||[];st.ws=p.ws||{};st.hearts=p.hearts??5;st.fc=p.fc||{};
  const today=new Date().toDateString();
  if(st.lastDate){const d=Math.floor((new Date(today)-new Date(st.lastDate))/864e5);if(d>1)st.streak=0;}
}
```

**Step 4: Commit**
```
git add index.html && git commit -m "Add flashcard state (st.fc) to data model and sync pipeline"
```

---

### Task 4: Implement SM-2 Algorithm

**Files:**
- Modify: `index.html` — add SM-2 functions after the `wstat` function (~line 1976)

**Step 1: Add SM-2 core functions**

Insert after `function wstat(id){...}` (~line 1976):

```javascript
// ═══════════════ SM-2 SPACED REPETITION ═══════════════
function fcKey(wordId,dir){return wordId+'_'+dir;}// e.g. "105_se"

function fcGet(wordId,dir){
  const k=fcKey(wordId,dir);
  if(!st.fc[k])st.fc[k]={ease:2.5,ivl:0,due:0,reps:0};
  return st.fc[k];
}

function fcRate(wordId,dir,rating){
  // rating: 0=Again, 1=Hard, 2=Good, 3=Easy
  const c=fcGet(wordId,dir);
  const now=Date.now();
  if(rating===0){
    // Again: reset
    c.reps=0;c.ivl=1/(24*60);// 1 minute in days
    c.ease=Math.max(1.3,c.ease-0.2);
  }else if(c.reps===0){
    // First correct answer on a new/reset card
    c.ivl=10/(24*60);// 10 minutes
    c.reps=1;
    if(rating===1)c.ease=Math.max(1.3,c.ease-0.15);
    if(rating===3)c.ease+=0.15;
  }else if(c.reps===1){
    // Second correct answer
    c.ivl=1;// 1 day
    c.reps=2;
    if(rating===1)c.ease=Math.max(1.3,c.ease-0.15);
    if(rating===3)c.ease+=0.15;
  }else{
    // SM-2 formula
    if(rating===1){c.ivl=Math.max(1,c.ivl*1.2);c.ease=Math.max(1.3,c.ease-0.15);}
    else if(rating===2){c.ivl=Math.max(1,c.ivl*c.ease);}
    else if(rating===3){c.ivl=Math.max(1,c.ivl*c.ease*1.3);c.ease+=0.15;}
    c.reps++;
  }
  c.due=now+c.ivl*86400000;// Convert days to ms
  save();
}

function fcIvlLabel(wordId,dir,rating){
  // Preview what the interval would be after a given rating
  const c=fcGet(wordId,dir);
  let ivl;
  if(rating===0)ivl=1/(24*60);
  else if(c.reps===0)ivl=10/(24*60);
  else if(c.reps===1)ivl=1;
  else{
    if(rating===1)ivl=Math.max(1,c.ivl*1.2);
    else if(rating===2)ivl=Math.max(1,c.ivl*c.ease);
    else ivl=Math.max(1,c.ivl*c.ease*1.3);
  }
  // Format: <1h = minutes, <1d = hours, else days
  if(ivl<1/24)return Math.round(ivl*24*60)+'m';
  if(ivl<1)return Math.round(ivl*24)+'h';
  if(ivl<30)return Math.round(ivl)+'d';
  return Math.round(ivl/30)+'mo';
}

function fcDueCards(){
  // Return all cards due now from completed units
  const now=Date.now();
  const cards=[];
  const compWords=UNITS.filter(u=>st.completed.includes(u.id)).flatMap(u=>u.words);
  compWords.forEach(w=>{
    ['se','es'].forEach(dir=>{
      const k=fcKey(w.id,dir);
      const c=st.fc[k];
      if(!c||c.due<=now)cards.push({word:w,dir:dir,key:k});
    });
  });
  return cards;
}

function fcTotalCards(){
  const compWords=UNITS.filter(u=>st.completed.includes(u.id)).flatMap(u=>u.words);
  return compWords.length*2;// bidirectional
}
```

**Step 2: Commit**
```
git add index.html && git commit -m "Implement SM-2 spaced repetition algorithm"
```

---

### Task 5: Build Flashcard Home View (Due Cards Summary)

**Files:**
- Modify: `index.html` — add `renderFcHome()` method to the `S` object

**Step 1: Add `renderFcHome` to the `S` object**

Add inside the `S={...}` object (after `setLearnMode`):

```javascript
renderFcHome(){
  const el=document.getElementById('fc-home');
  const due=fcDueCards();
  const total=fcTotalCards();
  if(total===0){
    el.innerHTML='<div style="text-align:center;padding:60px 20px;color:var(--g5)">'+
      '<div style="font-size:56px;margin-bottom:12px">📚</div>'+
      '<div style="font-size:18px;font-weight:800;color:var(--g7);margin-bottom:6px">No Flashcards Yet</div>'+
      '<div style="font-size:13px">Complete a lesson to unlock flashcards for those words.</div></div>';
    return;
  }
  let h='<div style="text-align:center;padding:20px 0">';
  h+='<div style="font-size:48px;margin-bottom:8px">'+(due.length>0?'📖':'🎉')+'</div>';
  h+='<div style="font-size:28px;font-weight:800;color:var(--g7)">'+due.length+' card'+(due.length!==1?'s':'')+' due</div>';
  h+='<div style="font-size:13px;color:var(--g5);margin-top:4px">'+total+' total cards</div>';
  if(due.length>0){
    h+='<button class="rv-btn primary" style="margin-top:20px" onclick="S.startFcSession()">Start Review</button>';
  }else{
    h+='<div style="font-size:15px;color:var(--green);font-weight:700;margin-top:16px">All caught up! Come back later.</div>';
  }
  h+='</div>';
  // Per-unit breakdown
  const compUnits=UNITS.filter(u=>st.completed.includes(u.id));
  if(compUnits.length>0){
    h+='<div style="margin-top:20px">';
    h+='<div style="font-size:14px;font-weight:800;color:var(--g5);text-transform:uppercase;letter-spacing:1px;margin-bottom:10px">By Unit</div>';
    compUnits.forEach(u=>{
      const now=Date.now();
      const uDue=u.words.reduce((n,w)=>{
        return n+['se','es'].filter(d=>{const c=st.fc[fcKey(w.id,d)];return !c||c.due<=now;}).length;
      },0);
      h+='<div style="display:flex;align-items:center;gap:10px;padding:10px;border:2px solid var(--g2);border-radius:12px;margin-bottom:6px">';
      h+='<span style="font-size:24px">'+esc(u.ic)+'</span>';
      h+='<div style="flex:1"><div style="font-size:14px;font-weight:700;color:var(--g7)">'+esc(u.t)+'</div>';
      h+='<div style="font-size:11px;color:var(--g5)">'+(u.words.length*2)+' cards</div></div>';
      if(uDue>0)h+='<span style="background:var(--orange);color:#fff;font-size:12px;font-weight:800;padding:3px 8px;border-radius:10px">'+uDue+' due</span>';
      else h+='<span style="color:var(--green);font-size:12px;font-weight:700">✓</span>';
      h+='</div>';
    });
    h+='</div>';
  }
  el.innerHTML=h;
},
```

**Step 2: Commit**
```
git add index.html && git commit -m "Add flashcard home view with due card summary and unit breakdown"
```

---

### Task 6: Build Flashcard Session Screen (Card UI + Flip Animation)

**Files:**
- Modify: `index.html` — add `#flashcard` screen HTML after `#comp` screen
- Modify: `index.html` — add flashcard CSS
- Modify: `index.html` — add `goScr` to recognize `flashcard` screen for sbar styling

**Step 1: Add flashcard screen HTML**

Insert after the `</div>` closing `#comp` (~line 488):
```html
<div class="sc" id="flashcard">
  <div class="fc-top">
    <button class="xbtn" onclick="S.exitFc()">&#10005;</button>
    <div class="fc-count" id="fc-count">0 / 0</div>
    <div style="width:32px"></div>
  </div>
  <div class="fc-body" id="fc-body"></div>
</div>
```

**Step 2: Add flashcard CSS**

Insert after the segmented toggle CSS:
```css
/* FLASHCARD */
.fc-top{padding:58px 20px 10px;display:flex;align-items:center;justify-content:space-between}
.fc-count{font-size:14px;font-weight:700;color:var(--g5)}
.fc-body{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px}
.fc-card-wrap{width:100%;max-width:320px;perspective:1000px;cursor:pointer}
.fc-card{position:relative;width:100%;min-height:280px;transition:transform .5s;transform-style:preserve-3d}
.fc-card.flipped{transform:rotateY(180deg)}
.fc-face{position:absolute;top:0;left:0;width:100%;min-height:280px;backface-visibility:hidden;border-radius:20px;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:28px;text-align:center}
.fc-front{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;box-shadow:0 8px 30px rgba(102,126,234,.3)}
.fc-back{background:#fff;border:2px solid var(--g2);transform:rotateY(180deg)}
.fc-dir{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;opacity:.7;margin-bottom:12px}
.fc-word{font-size:32px;font-weight:800;line-height:1.3}
.fc-em{font-size:40px;margin-bottom:8px}
.fc-trans{font-size:24px;font-weight:800;color:var(--g7);margin-top:8px}
.fc-hint{font-size:12px;color:rgba(255,255,255,.6);margin-top:20px}
.fc-ratings{display:flex;gap:6px;margin-top:20px;width:100%;max-width:320px}
.fc-rate-btn{flex:1;padding:12px 4px;border:none;border-radius:12px;font-size:13px;font-weight:700;cursor:pointer;color:#fff;box-shadow:0 3px 0 rgba(0,0,0,.15);transition:.1s}
.fc-rate-btn:active{transform:translateY(2px);box-shadow:0 1px 0 rgba(0,0,0,.15)}
.fc-rate-btn .fc-rate-ivl{display:block;font-size:10px;opacity:.8;margin-top:2px}
.fc-rate-btn.r-again{background:var(--red)}
.fc-rate-btn.r-hard{background:var(--orange)}
.fc-rate-btn.r-good{background:var(--green)}
.fc-rate-btn.r-easy{background:var(--blue)}
```

**Step 3: Update `goScr` sbar styling**

In the `goScr` method (~line 1993), add `'flashcard'` to the dark sbar list:
```javascript
goScr(id){document.querySelectorAll('.sc').forEach(s=>s.classList.remove('act'));
  document.getElementById(id).classList.add('act');
  document.getElementById('sbar').classList.toggle('lt',id==='splash'||id==='comp'||id==='home'||id==='social'||id==='flashcard');},
```

**Step 4: Add responsive/standalone CSS for flashcard screen**

In `@media(display-mode:standalone)` and `@media(max-width:430px)` sections, add:
```css
.fc-top{padding-top:calc(env(safe-area-inset-top,20px) + 10px)}
```

**Step 5: Commit**
```
git add index.html && git commit -m "Add flashcard session screen HTML and CSS with 3D flip animation"
```

---

### Task 7: Implement Flashcard Session Logic

**Files:**
- Modify: `index.html` — add session methods to `S` object

**Step 1: Add session state variables**

Add to `st` initial state:
```javascript
fcCards:[],fcIdx:0,fcFlipped:false,fcReviewed:0,fcAgainCount:0,fcCorrectCount:0
```

**Step 2: Add `startFcSession` method**

```javascript
startFcSession(){
  const due=fcDueCards();
  if(!due.length){this.toast('No cards due!');return;}
  // Shuffle due cards
  st.fcCards=this.sh(due);
  st.fcIdx=0;st.fcFlipped=false;st.fcReviewed=0;st.fcAgainCount=0;st.fcCorrectCount=0;
  this.goScr('flashcard');
  this.renderFcCard();
},
```

**Step 3: Add `renderFcCard` method**

```javascript
renderFcCard(){
  if(st.fcIdx>=st.fcCards.length){this.finishFcSession();return;}
  const card=st.fcCards[st.fcIdx];
  const w=card.word;
  const isSE=card.dir==='se';// Serbian->English
  const frontText=isSE?w.l:w.e;
  const frontLang=isSE?curLang:'en';
  const dirLabel=isSE?(langName()+' → English'):('English → '+langName());
  const backText=isSE?w.e:w.l;
  const backLang=isSE?'en':curLang;

  document.getElementById('fc-count').textContent=(st.fcIdx+1)+' / '+st.fcCards.length;

  let h='<div class="fc-card-wrap" onclick="S.flipFc()">';
  h+='<div class="fc-card" id="fc-card">';
  // Front
  h+='<div class="fc-face fc-front">';
  h+='<div class="fc-dir">'+esc(dirLabel)+'</div>';
  h+='<div class="fc-word">'+esc(frontText)+'</div>';
  h+=spkBtn(frontText,frontLang);
  h+='<div class="fc-hint">Tap to flip</div>';
  h+='</div>';
  // Back
  h+='<div class="fc-face fc-back">';
  h+='<div class="fc-em">'+w.em+'</div>';
  h+='<div class="fc-trans">'+esc(backText)+'</div>';
  h+=spkBtn(backText,backLang);
  h+='</div>';
  h+='</div></div>';
  // Rating buttons (hidden until flipped)
  h+='<div class="fc-ratings" id="fc-ratings" style="display:none">';
  h+='<button class="fc-rate-btn r-again" onclick="S.rateFc(0)">Again<span class="fc-rate-ivl">'+fcIvlLabel(w.id,card.dir,0)+'</span></button>';
  h+='<button class="fc-rate-btn r-hard" onclick="S.rateFc(1)">Hard<span class="fc-rate-ivl">'+fcIvlLabel(w.id,card.dir,1)+'</span></button>';
  h+='<button class="fc-rate-btn r-good" onclick="S.rateFc(2)">Good<span class="fc-rate-ivl">'+fcIvlLabel(w.id,card.dir,2)+'</span></button>';
  h+='<button class="fc-rate-btn r-easy" onclick="S.rateFc(3)">Easy<span class="fc-rate-ivl">'+fcIvlLabel(w.id,card.dir,3)+'</span></button>';
  h+='</div>';
  document.getElementById('fc-body').innerHTML=h;
  st.fcFlipped=false;
},

flipFc(){
  if(st.fcFlipped)return;
  st.fcFlipped=true;
  const card=document.getElementById('fc-card');
  if(card)card.classList.add('flipped');
  const ratings=document.getElementById('fc-ratings');
  if(ratings)ratings.style.display='flex';
},

rateFc(rating){
  const card=st.fcCards[st.fcIdx];
  fcRate(card.word.id,card.dir,rating);
  st.fcReviewed++;
  if(rating===0){
    st.fcAgainCount++;
    // Re-insert this card a few positions later
    const insertAt=Math.min(st.fcIdx+3+Math.floor(Math.random()*3),st.fcCards.length);
    st.fcCards.splice(insertAt,0,{...card});
  }else{
    st.fcCorrectCount++;
  }
  st.fcIdx++;
  this.renderFcCard();
},

exitFc(){
  sCl();
  this.setLearnMode('flashcards');
  this.goHome();
},

finishFcSession(){
  // Show summary using the comp screen pattern
  const el=document.getElementById('fc-body');
  const pct=st.fcReviewed>0?Math.round(st.fcCorrectCount/st.fcReviewed*100):0;
  let h='<div style="text-align:center;padding:40px 20px">';
  h+='<div style="font-size:56px;margin-bottom:12px">🎉</div>';
  h+='<div style="font-size:24px;font-weight:800;color:var(--g7);margin-bottom:20px">Session Complete!</div>';
  h+='<div style="display:flex;gap:20px;justify-content:center;margin-bottom:24px">';
  h+='<div style="text-align:center"><div style="font-size:28px;font-weight:800;color:var(--green)">'+st.fcReviewed+'</div><div style="font-size:11px;color:var(--g5);font-weight:700">REVIEWED</div></div>';
  h+='<div style="text-align:center"><div style="font-size:28px;font-weight:800;color:var(--blue)">'+pct+'%</div><div style="font-size:11px;color:var(--g5);font-weight:700">RECALLED</div></div>';
  if(st.fcAgainCount>0)h+='<div style="text-align:center"><div style="font-size:28px;font-weight:800;color:var(--orange)">'+st.fcAgainCount+'</div><div style="font-size:11px;color:var(--g5);font-weight:700">REPEATED</div></div>';
  h+='</div>';
  h+='<button class="rv-btn primary" onclick="S.exitFc()">Done</button>';
  h+='</div>';
  el.innerHTML=h;
  sDn();// Play completion sound
},
```

**Step 3: Commit**
```
git add index.html && git commit -m "Implement flashcard session: flip, rate, SM-2 scheduling, summary"
```

---

### Task 8: Auto-Initialize Flashcard Cards on Lesson Completion

**Files:**
- Modify: `index.html` — in the lesson completion handler, seed `st.fc` for newly completed unit words

**Step 1: Find lesson completion code**

Look for where `st.completed.push(u.id)` happens (in the lesson completion flow). After that line, add:

```javascript
// Seed flashcard entries for newly completed unit's words
u.words.forEach(w=>{
  ['se','es'].forEach(dir=>{
    const k=fcKey(w.id,dir);
    if(!st.fc[k])st.fc[k]={ease:2.5,ivl:0,due:0,reps:0};
  });
});
```

This ensures that when a lesson is completed, all its words are immediately available as "new" flashcards (due=0 means due now).

**Step 2: Commit**
```
git add index.html && git commit -m "Auto-seed flashcard cards when a lesson is completed"
```

---

### Task 9: Update Service Worker Cache Version

**Files:**
- Modify: `sw.js:1`

**Step 1: Bump cache version**

Change `const CACHE='zeka-v23';` to `const CACHE='zeka-v24';`

**Step 2: Commit and push**
```
git add index.html sw.js && git commit -m "Bump SW cache to v24 for flashcard feature"
git push
```

---

## Task Dependencies

```
Task 1 (header) ──┐
Task 2 (toggle)  ──┼── Task 3 (state) ── Task 4 (SM-2) ── Task 5 (fc home) ── Task 6 (fc screen) ── Task 7 (session logic) ── Task 8 (auto-seed) ── Task 9 (SW bump)
```

Tasks 1 and 2 can be done in parallel. All others are sequential.
