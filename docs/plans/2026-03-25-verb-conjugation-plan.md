# Verb Conjugation Drill — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a verb conjugation drill mode as a third segment on the LEARN tab toggle, with two-phase exercises (infinitive translation + conjugation grid) and flashcard integration.

**Architecture:** Verb data is hardcoded as `V_SR` array in index.html. A new `[Verbs]` segment on the existing toggle switches to a verb home view. Verb exercises use a new `#verb-drill` screen with phase 1 (translate infinitive) and phase 2 (fill conjugation grid with pre-filled stems). Practiced verbs auto-seed into the existing flashcard system.

**Tech Stack:** Vanilla JS, CSS, HTML — all in index.html (single-file PWA)

---

### Task 1: Add Verb Data

**Files:**
- Modify: `index.html` — insert after the `U_IT` array (find `const U_IT=` and insert after its closing `];`)

**Step 1: Add Serbian verb data array**

Insert this block:

```javascript
const V_SR=[
{inf:'biti',en:'to be',em:'🔄',conj:{ja:'sam',ti:'si',on:'je',mi:'smo',vi:'ste',oni:'su'}},
{inf:'imati',en:'to have',em:'🤲',conj:{ja:'imam',ti:'imaš',on:'ima',mi:'imamo',vi:'imate',oni:'imaju'}},
{inf:'hteti',en:'to want',em:'💭',conj:{ja:'hoću',ti:'hoćeš',on:'hoće',mi:'hoćemo',vi:'hoćete',oni:'hoće'}},
{inf:'moći',en:'to be able',em:'💪',conj:{ja:'mogu',ti:'možeš',on:'može',mi:'možemo',vi:'možete',oni:'mogu'}},
{inf:'ići',en:'to go',em:'🚶',conj:{ja:'idem',ti:'ideš',on:'ide',mi:'idemo',vi:'idete',oni:'idu'}},
{inf:'raditi',en:'to work',em:'💼',conj:{ja:'radim',ti:'radiš',on:'radi',mi:'radimo',vi:'radite',oni:'rade'}},
{inf:'znati',en:'to know',em:'🧠',conj:{ja:'znam',ti:'znaš',on:'zna',mi:'znamo',vi:'znate',oni:'znaju'}},
{inf:'videti',en:'to see',em:'👀',conj:{ja:'vidim',ti:'vidiš',on:'vidi',mi:'vidimo',vi:'vidite',oni:'vide'}},
{inf:'jesti',en:'to eat',em:'🍽️',conj:{ja:'jedem',ti:'jedeš',on:'jede',mi:'jedemo',vi:'jedete',oni:'jedu'}},
{inf:'piti',en:'to drink',em:'🥤',conj:{ja:'pijem',ti:'piješ',on:'pije',mi:'pijemo',vi:'pijete',oni:'piju'}},
{inf:'govoriti',en:'to speak',em:'🗣️',conj:{ja:'govorim',ti:'govoriš',on:'govori',mi:'govorimo',vi:'govorite',oni:'govore'}},
{inf:'razumeti',en:'to understand',em:'💡',conj:{ja:'razumem',ti:'razumeš',on:'razume',mi:'razumemo',vi:'razumete',oni:'razumeju'}},
{inf:'pisati',en:'to write',em:'✍️',conj:{ja:'pišem',ti:'pišeš',on:'piše',mi:'pišemo',vi:'pišete',oni:'pišu'}},
{inf:'čitati',en:'to read',em:'📖',conj:{ja:'čitam',ti:'čitaš',on:'čita',mi:'čitamo',vi:'čitate',oni:'čitaju'}},
{inf:'učiti',en:'to learn',em:'📚',conj:{ja:'učim',ti:'učiš',on:'uči',mi:'učimo',vi:'učite',oni:'uče'}},
{inf:'živeti',en:'to live',em:'🏠',conj:{ja:'živim',ti:'živiš',on:'živi',mi:'živimo',vi:'živite',oni:'žive'}},
{inf:'voleti',en:'to love',em:'❤️',conj:{ja:'volim',ti:'voliš',on:'voli',mi:'volimo',vi:'volite',oni:'vole'}},
{inf:'spavati',en:'to sleep',em:'😴',conj:{ja:'spavam',ti:'spavaš',on:'spava',mi:'spavamo',vi:'spavate',oni:'spavaju'}},
{inf:'kupovati',en:'to buy',em:'🛒',conj:{ja:'kupujem',ti:'kupuješ',on:'kupuje',mi:'kupujemo',vi:'kupujete',oni:'kupuju'}},
{inf:'davati',en:'to give',em:'🎁',conj:{ja:'dajem',ti:'daješ',on:'daje',mi:'dajemo',vi:'dajete',oni:'daju'}},
{inf:'igrati',en:'to play',em:'⚽',conj:{ja:'igram',ti:'igraš',on:'igra',mi:'igramo',vi:'igrate',oni:'igraju'}},
{inf:'pevati',en:'to sing',em:'🎤',conj:{ja:'pevam',ti:'pevaš',on:'peva',mi:'pevamo',vi:'pevate',oni:'pevaju'}},
{inf:'trčati',en:'to run',em:'🏃',conj:{ja:'trčim',ti:'trčiš',on:'trči',mi:'trčimo',vi:'trčite',oni:'trče'}},
{inf:'putovati',en:'to travel',em:'✈️',conj:{ja:'putujem',ti:'putuješ',on:'putuje',mi:'putujemo',vi:'putujete',oni:'putuju'}},
{inf:'kuvati',en:'to cook',em:'👨‍🍳',conj:{ja:'kuvam',ti:'kuvaš',on:'kuva',mi:'kuvamo',vi:'kuvate',oni:'kuvaju'}}
];
```

**Step 2: Add VERBS variable and helper**

After `let UNITS;` (which is set in `pickLang()`), add:

```javascript
let VERBS=[];
```

In `pickLang()`, after the line that sets `UNITS=buildUnits(...)`, add:

```javascript
VERBS=curLang==='sr'?V_SR:[];
```

**Step 3: Add commonPrefix helper function**

Insert after the `fcTotalCards` function:

```javascript
function verbPrefix(v){
  const forms=Object.values(v.conj);
  let pre=forms[0];
  for(let i=1;i<forms.length;i++){
    while(forms[i].indexOf(pre)!==0)pre=pre.slice(0,-1);
    if(!pre)return '';
  }
  return pre;
}
```

**Step 4: Commit**

```
git add index.html
git commit -m "Add Serbian verb conjugation data (25 verbs, present tense)"
```

---

### Task 2: Update Segmented Toggle for 3 Modes

**Files:**
- Modify: `index.html`

**Step 1: Add Verbs button to toggle HTML**

Find (line 452):
```html
  <button class="seg-btn" onclick="S.setLearnMode('flashcards')">Flashcards</button>
```

Add after it:
```html
  <button class="seg-btn" onclick="S.setLearnMode('verbs')">Verbs</button>
```

**Step 2: Add verb-home container**

Find (line 455):
```html
<div id="fc-home" style="display:none;flex:1;overflow-y:auto;padding:14px 22px 100px"></div>
```

Add after it:
```html
  <div id="verb-home" style="display:none;flex:1;overflow-y:auto;padding:14px 22px 100px"></div>
```

**Step 3: Update setLearnMode method**

Replace the existing `setLearnMode` method (lines 2191-2198) with:

```javascript
setLearnMode(mode){
  const modes=['lessons','flashcards','verbs'];
  document.querySelectorAll('.seg-btn').forEach((b,i)=>{
    b.classList.toggle('seg-active',i===modes.indexOf(mode));
  });
  document.getElementById('hscr').style.display=mode==='lessons'?'':'none';
  document.getElementById('fc-home').style.display=mode==='flashcards'?'':'none';
  document.getElementById('verb-home').style.display=mode==='verbs'?'':'none';
  if(mode==='flashcards'&&typeof this.renderFcHome==='function')this.renderFcHome();
  if(mode==='verbs')this.renderVerbHome();
},
```

**Step 4: Commit**

```
git add index.html
git commit -m "Add Verbs as third segment on LEARN tab toggle"
```

---

### Task 3: Build Verb Home View

**Files:**
- Modify: `index.html`

**Step 1: Add renderVerbHome method to S object**

Add this method right before `setLearnMode`:

```javascript
renderVerbHome(){
  const el=document.getElementById('verb-home');
  if(!VERBS.length){
    el.innerHTML='<div style="text-align:center;padding:60px 20px;color:rgba(255,255,255,.6)">'+
      '<div style="font-size:56px;margin-bottom:12px">🔤</div>'+
      '<div style="font-size:18px;font-weight:800;color:#fff;margin-bottom:6px">No Verbs Available</div>'+
      '<div style="font-size:13px">Verb conjugation is not yet available for '+esc(langName())+'.</div></div>';
    return;
  }
  let h='<div style="text-align:center;padding:16px 0">';
  h+='<div style="font-size:48px;margin-bottom:8px">🔤</div>';
  h+='<div style="font-size:20px;font-weight:800;color:#fff;margin-bottom:4px">Verb Conjugation</div>';
  h+='<div style="font-size:13px;color:rgba(255,255,255,.6);margin-bottom:16px">Present Tense · '+VERBS.length+' verbs</div>';
  h+='<div style="display:flex;gap:8px;justify-content:center;margin-bottom:8px">';
  [3,5,10].forEach(n=>{
    h+='<button style="padding:10px 20px;border:none;border-radius:12px;font-size:14px;font-weight:800;cursor:pointer;color:#fff;background:rgba(255,255,255,.12);transition:.2s" onclick="S.startVerbSession('+n+')">'+n+' verbs</button>';
  });
  h+='</div>';
  h+='<button style="width:100%;padding:14px;border:none;border-radius:14px;font-size:15px;font-weight:800;cursor:pointer;text-transform:uppercase;letter-spacing:1px;color:#fff;background:var(--green);box-shadow:0 4px 0 var(--green-d);margin-top:8px" onclick="S.startVerbSession('+Math.min(5,VERBS.length)+')">Random Session</button>';
  h+='</div>';
  h+='<div style="margin-top:20px">';
  h+='<div style="font-size:14px;font-weight:800;color:rgba(255,255,255,.5);text-transform:uppercase;letter-spacing:1px;margin-bottom:10px">All Verbs</div>';
  VERBS.forEach((v,i)=>{
    h+='<div style="display:flex;align-items:center;gap:10px;padding:12px;border:2px solid rgba(255,255,255,.1);border-radius:12px;margin-bottom:6px;cursor:pointer" onclick="S.startVerbSession(1,'+i+')">';
    h+='<span style="font-size:24px">'+v.em+'</span>';
    h+='<div style="flex:1"><div style="font-size:14px;font-weight:700;color:#fff">'+esc(v.inf)+'</div>';
    h+='<div style="font-size:12px;color:rgba(255,255,255,.5)">'+esc(v.en)+'</div></div>';
    h+='<span style="color:rgba(255,255,255,.3);font-size:18px">›</span>';
    h+='</div>';
  });
  h+='</div>';
  el.innerHTML=h;
},
```

**Step 2: Commit**

```
git add index.html
git commit -m "Add verb home view with random session picker and verb list"
```

---

### Task 4: Add Verb Drill Screen HTML + CSS

**Files:**
- Modify: `index.html`

**Step 1: Add verb drill screen HTML**

Find the `<div class="sc" id="flashcard">` block. After its closing `</div>`, add:

```html
<div class="sc" id="verb-drill">
  <div class="vd-top">
    <button class="xbtn" onclick="S.exitVerb()">&#10005;</button>
    <div class="vd-count" id="vd-count">0 / 0</div>
    <div style="width:32px"></div>
  </div>
  <div class="vd-body" id="vd-body"></div>
</div>
```

**Step 2: Add verb drill CSS**

Add after the flashcard CSS block (after `.fc-rate-btn.r-easy{background:var(--blue)}`):

```css
/* VERB DRILL */
.vd-top{padding:58px 20px 10px;display:flex;align-items:center;justify-content:space-between;background:#131F24}
.vd-count{font-size:14px;font-weight:700;color:rgba(255,255,255,.6)}
.vd-body{flex:1;display:flex;flex-direction:column;align-items:center;padding:20px;background:#131F24;overflow-y:auto}
.vd-phase{width:100%;max-width:360px}
.vd-prompt{font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:rgba(255,255,255,.5);margin-bottom:8px;text-align:center}
.vd-inf{font-size:28px;font-weight:800;color:#fff;text-align:center;margin-bottom:16px}
.vd-input{width:100%;padding:14px;border:2px solid rgba(255,255,255,.15);border-radius:14px;font-size:18px;font-weight:700;text-align:center;background:rgba(255,255,255,.08);color:#fff;outline:none;transition:.2s}
.vd-input:focus{border-color:var(--blue)}
.vd-input.correct{border-color:var(--green);background:rgba(88,204,2,.1)}
.vd-input.wrong{border-color:var(--red);background:rgba(255,75,75,.1)}
.vd-correction{font-size:14px;color:var(--red);font-weight:700;text-align:center;margin-top:6px}
.vd-conj{width:100%;max-width:360px;margin-top:16px}
.vd-row{display:flex;align-items:center;gap:8px;margin-bottom:8px}
.vd-pronoun{font-size:14px;font-weight:800;color:rgba(255,255,255,.6);width:90px;text-align:right;flex-shrink:0}
.vd-stem{font-size:16px;font-weight:700;color:rgba(255,255,255,.4)}
.vd-suffix{flex:1;padding:10px;border:2px solid rgba(255,255,255,.15);border-radius:10px;font-size:16px;font-weight:700;background:rgba(255,255,255,.08);color:#fff;outline:none;transition:.2s}
.vd-suffix:focus{border-color:var(--blue)}
.vd-suffix.correct{border-color:var(--green);background:rgba(88,204,2,.1)}
.vd-suffix.wrong{border-color:var(--red);background:rgba(255,75,75,.1)}
.vd-next{width:100%;max-width:360px;padding:14px;border:none;border-radius:14px;font-size:15px;font-weight:800;cursor:pointer;text-transform:uppercase;letter-spacing:1px;color:#fff;background:var(--green);box-shadow:0 4px 0 var(--green-d);margin-top:16px}
```

**Step 3: Update goScr sbar toggle**

Find (line 2053):
```javascript
document.getElementById('sbar').classList.toggle('lt',id==='splash'||id==='comp'||id==='home'||id==='social'||id==='flashcard');},
```

Add `||id==='verb-drill'` before the closing `);`:
```javascript
document.getElementById('sbar').classList.toggle('lt',id==='splash'||id==='comp'||id==='home'||id==='social'||id==='flashcard'||id==='verb-drill');},
```

**Step 4: Add responsive CSS for verb drill**

In the `@media(display-mode:standalone)` section, add after `.fc-top{...}`:
```css
.vd-top{padding-top:calc(env(safe-area-inset-top,20px) + 10px)}
```

**Step 5: Commit**

```
git add index.html
git commit -m "Add verb drill screen HTML and CSS"
```

---

### Task 5: Implement Verb Session Logic

**Files:**
- Modify: `index.html`

**Step 1: Add verb session state**

Find `let st={...}` and add these properties:
```
vbVerbs:[],vbIdx:0,vbPhase:1,vbCorrect:0,vbTotal:0
```

**Step 2: Add verb session methods to S object**

Add these methods near `renderVerbHome`:

```javascript
startVerbSession(count,specificIdx){
  if(!VERBS.length)return;
  if(typeof specificIdx==='number'){
    st.vbVerbs=[VERBS[specificIdx]];
  }else{
    const shuffled=this.sh([...VERBS]);
    st.vbVerbs=shuffled.slice(0,Math.min(count,shuffled.length));
  }
  st.vbIdx=0;st.vbPhase=1;st.vbCorrect=0;st.vbTotal=0;
  this.goScr('verb-drill');
  this.renderVerbPhase();
},

renderVerbPhase(){
  if(st.vbIdx>=st.vbVerbs.length){this.finishVerbSession();return;}
  const v=st.vbVerbs[st.vbIdx];
  document.getElementById('vd-count').textContent=(st.vbIdx+1)+' / '+st.vbVerbs.length;
  if(st.vbPhase===1){this.renderVerbP1(v);}
  else{this.renderVerbP2(v);}
},

renderVerbP1(v){
  const toSr=Math.random()<0.5;
  const prompt=toSr?'Translate to '+langName():'Translate to English';
  const shown=toSr?v.en:v.inf;
  const answer=toSr?v.inf:v.en;
  let h='<div class="vd-phase">';
  h+='<div class="vd-prompt">'+esc(prompt)+'</div>';
  h+='<div class="vd-inf">'+v.em+' '+esc(shown)+'</div>';
  h+='<input class="vd-input" id="vd-inf-input" placeholder="Type translation..." autocomplete="off" autocapitalize="off" spellcheck="false">';
  h+='<div id="vd-inf-fb"></div>';
  h+='<button class="vd-next" id="vd-p1-btn" onclick="S.checkVerbP1(\''+answer.replace(/'/g,"\\'")+'\')">Check</button>';
  h+='</div>';
  document.getElementById('vd-body').innerHTML=h;
  const inp=document.getElementById('vd-inf-input');
  inp.focus();
  inp.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();document.getElementById('vd-p1-btn').click();}});
},

checkVerbP1(answer){
  const inp=document.getElementById('vd-inf-input');
  const btn=document.getElementById('vd-p1-btn');
  if(btn.textContent==='Next'){st.vbPhase=2;this.renderVerbPhase();return;}
  const val=inp.value.trim().toLowerCase();
  const correct=answer.toLowerCase();
  st.vbTotal++;
  if(val===correct){
    st.vbCorrect++;inp.classList.add('correct');sCl();
  }else{
    inp.classList.add('wrong');
    document.getElementById('vd-inf-fb').innerHTML='<div class="vd-correction">'+esc(answer)+'</div>';
  }
  inp.disabled=true;
  btn.textContent='Next';
},

renderVerbP2(v){
  const pre=verbPrefix(v);
  const pronouns=[
    ['Ja',v.conj.ja],['Ti',v.conj.ti],['On/Ona/Ono',v.conj.on],
    ['Mi',v.conj.mi],['Vi',v.conj.vi],['Oni/One/Ona',v.conj.oni]
  ];
  let h='<div class="vd-phase">';
  h+='<div class="vd-prompt">Conjugate: '+v.em+' '+esc(v.inf)+' ('+esc(v.en)+')</div>';
  h+='<div class="vd-conj">';
  pronouns.forEach((p,i)=>{
    const suffix=p[1].slice(pre.length);
    h+='<div class="vd-row">';
    h+='<span class="vd-pronoun">'+esc(p[0])+'</span>';
    if(pre)h+='<span class="vd-stem">'+esc(pre)+'</span>';
    h+='<input class="vd-suffix" id="vd-c'+i+'" data-answer="'+esc(suffix)+'" data-full="'+esc(p[1])+'" placeholder="'+(pre?'...':p[1].charAt(0)+'...')+'" autocomplete="off" autocapitalize="off" spellcheck="false">';
    h+='</div>';
  });
  h+='</div>';
  h+='<button class="vd-next" id="vd-p2-done" style="display:none" onclick="S.nextVerb()">Next Verb</button>';
  h+='</div>';
  document.getElementById('vd-body').innerHTML=h;
  // Set up individual validation on blur/enter
  pronouns.forEach((p,i)=>{
    const el=document.getElementById('vd-c'+i);
    const validate=()=>{
      if(el.classList.contains('correct')||el.classList.contains('wrong'))return;
      const val=el.value.trim().toLowerCase();
      if(!val)return;
      const ans=el.dataset.answer.toLowerCase();
      const full=el.dataset.full;
      st.vbTotal++;
      if(val===ans||val===full.toLowerCase()){
        st.vbCorrect++;el.classList.add('correct');sCl();
      }else{
        el.classList.add('wrong');el.value=el.dataset.answer;
      }
      el.disabled=true;
      // Focus next unanswered
      let next=null;
      for(let j=i+1;j<pronouns.length;j++){
        const nx=document.getElementById('vd-c'+j);
        if(!nx.disabled){next=nx;break;}
      }
      if(next)next.focus();
      else document.getElementById('vd-p2-done').style.display='';
    };
    el.addEventListener('blur',validate);
    el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key==='Tab'){e.preventDefault();validate();}});
  });
  document.getElementById('vd-c0').focus();
},

nextVerb(){
  // Seed verb infinitive into flashcards
  const v=st.vbVerbs[st.vbIdx];
  const vId='v_'+v.inf;
  ['se','es'].forEach(dir=>{
    const k=vId+'_'+dir;
    if(!st.fc[k])st.fc[k]={ease:2.5,ivl:0,due:0,reps:0};
  });
  st.vbIdx++;st.vbPhase=1;
  this.renderVerbPhase();
},

exitVerb(){
  sCl();save();
  this.goHome();
  this.setLearnMode('verbs');
},

finishVerbSession(){
  sDn();save();
  const el=document.getElementById('vd-body');
  const pct=st.vbTotal>0?Math.round(st.vbCorrect/st.vbTotal*100):0;
  let h='<div style="text-align:center;padding:40px 20px">';
  h+='<div style="font-size:56px;margin-bottom:12px">🎉</div>';
  h+='<div style="font-size:24px;font-weight:800;color:#fff;margin-bottom:20px">Session Complete!</div>';
  h+='<div style="display:flex;gap:20px;justify-content:center;margin-bottom:24px">';
  h+='<div style="text-align:center"><div style="font-size:28px;font-weight:800;color:var(--green)">'+st.vbVerbs.length+'</div><div style="font-size:11px;color:rgba(255,255,255,.5);font-weight:700">VERBS</div></div>';
  h+='<div style="text-align:center"><div style="font-size:28px;font-weight:800;color:var(--blue)">'+pct+'%</div><div style="font-size:11px;color:rgba(255,255,255,.5);font-weight:700">ACCURACY</div></div>';
  h+='<div style="text-align:center"><div style="font-size:28px;font-weight:800;color:var(--orange)">'+st.vbCorrect+'/'+st.vbTotal+'</div><div style="font-size:11px;color:rgba(255,255,255,.5);font-weight:700">CORRECT</div></div>';
  h+='</div>';
  h+='<button style="width:100%;padding:16px;border:none;border-radius:16px;font-size:16px;font-weight:800;cursor:pointer;text-transform:uppercase;letter-spacing:1px;color:#fff;background:var(--green);box-shadow:0 4px 0 var(--green-d)" onclick="S.exitVerb()">Done</button>';
  h+='</div>';
  el.innerHTML=h;
},
```

**Step 3: Update flashcard system to recognize verb flashcard entries**

The verb flashcard keys use format `v_raditi_se` / `v_raditi_es`. The existing `fcDueCards()` only looks at completed unit words. Add verb entries to `fcDueCards()`.

Find the `fcDueCards` function and replace with:

```javascript
function fcDueCards(){
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
  // Add verb infinitives that have been practiced
  VERBS.forEach(v=>{
    const vId='v_'+v.inf;
    ['se','es'].forEach(dir=>{
      const k=vId+'_'+dir;
      const c=st.fc[k];
      if(c&&c.due<=now)cards.push({word:{id:vId,l:v.inf,e:v.en,em:v.em,s:v.inf},dir:dir,key:k});
    });
  });
  return cards;
}
```

Update `fcTotalCards` similarly:

```javascript
function fcTotalCards(){
  const compWords=UNITS.filter(u=>st.completed.includes(u.id)).flatMap(u=>u.words);
  let total=compWords.length*2;
  VERBS.forEach(v=>{
    const vId='v_'+v.inf;
    if(st.fc[vId+'_se']||st.fc[vId+'_es'])total+=2;
  });
  return total;
}
```

**Step 4: Commit**

```
git add index.html
git commit -m "Implement verb drill session logic with flashcard integration"
```

---

### Task 6: Bump Service Worker Cache

**Files:**
- Modify: `sw.js`

**Step 1: Bump cache version**

Change `const CACHE='zeka-v24';` to `const CACHE='zeka-v25';`

**Step 2: Commit and push**

```
git add index.html sw.js
git commit -m "Bump SW cache to v25 for verb conjugation feature"
git push
```
