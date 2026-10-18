# Dictionary / Search — Implementation Plan

> **For agentic workers:** Single-file vanilla JS app. Use Edit tool for surgical changes. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Add a per-language dictionary that lets the user search words or verbs in either English or the source language and see translations. Results filter as the user types. Tapping a result expands it inline to show CEFR level, unit, mastery state, audio button, and (for verbs) the conjugation table.

**Design decisions (settled with the user):**
- 4th bottom-nav tab: `Learn | Progress | Search | Profile`
- Search scope: words from `UNITS` + verbs from `VERBS` (current language only)
- Tap row → expand inline (no navigation)
- Collapsed row: minimal, just word + translation (no badges)
- Expanded row: word, translation, 🔊, meta line (CEFR · unit · mastery), conjugation table for verbs
- Case + diacritic-insensitive matching
- Smart ranking: exact > prefix > substring
- Debounced input (~120ms)
- Empty input shows "Type to search" hint

---

## Task 1: Scaffolding — CSS, DOM, nav button, search icon, match logic

**File:** `index.html`

### Step 1: Add `search` SVG icon to the ICONS object

Find (around line 2293):

```js
  chart:'<path d="M4 20V10m6 10V4m6 16v-7m6 7V8" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" fill="none"/>',
```

Add immediately after:

```js
  search:'<path d="M10.5 4a6.5 6.5 0 1 0 4.13 11.55l4.41 4.41 1.41-1.41-4.41-4.41A6.5 6.5 0 0 0 10.5 4zm0 2a4.5 4.5 0 1 1 0 9 4.5 4.5 0 0 1 0-9z"/>',
```

### Step 2: Add Search-screen CSS

Find (around line 440, just after the `.fc-body` rule and the new `#match-game` rules from a prior task):

```css
#match-game{background:var(--bg);color:var(--text-1)}
#mc-body{background:var(--bg)}
```

Add immediately after:

```css
/* SEARCH / DICTIONARY */
#search{background:var(--bg);color:var(--text-1)}
.sx-head{padding:calc(env(safe-area-inset-top,20px) + 16px) 14px 12px;display:flex;align-items:center;gap:10px;background:var(--bg);border-bottom:1px solid var(--divider)}
.sx-input{flex:1;padding:12px 14px;border:1.5px solid var(--divider);border-radius:14px;background:var(--surface);color:var(--text-1);font-size:15px;font-weight:600;font-family:var(--font);outline:none;transition:border-color .15s}
.sx-input:focus{border-color:var(--sr-blue)}
.sx-input::placeholder{color:var(--text-3)}
.sx-clear{background:none;border:none;color:var(--g4);font-size:18px;cursor:pointer;padding:6px 10px;border-radius:8px}
.sx-clear:active{background:rgba(255,255,255,.06)}
.sx-body{flex:1;overflow-y:auto;-webkit-overflow-scrolling:touch;padding:8px 0 100px}
.sx-empty{text-align:center;padding:60px 24px;color:var(--g4);font-size:14px;line-height:1.5}
.sx-row{padding:14px 18px;border-bottom:1px solid rgba(255,255,255,.04);cursor:pointer;transition:background .12s}
.sx-row:active,.sx-row.expanded{background:rgba(255,255,255,.03)}
.sx-row-collapsed{display:flex;align-items:center;justify-content:space-between;gap:14px}
.sx-source{font-size:16px;font-weight:700;color:#fff;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sx-source.verb-tag::after{content:' verb';color:var(--purple);font-size:11px;font-weight:600;margin-left:6px;opacity:.8}
.sx-trans{font-size:14px;color:var(--text-2);text-align:right;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sx-expand{margin-top:12px;padding:14px;background:var(--surface);border-radius:12px;display:flex;flex-direction:column;gap:10px}
.sx-expand-word{font-size:22px;font-weight:800;color:#fff;display:flex;align-items:center;gap:10px}
.sx-expand-trans{font-size:15px;color:var(--text-2);font-weight:600}
.sx-expand-meta{display:flex;gap:8px;flex-wrap:wrap;margin-top:4px}
.sx-meta-chip{font-size:11px;font-weight:700;padding:4px 10px;border-radius:999px;background:rgba(255,255,255,.06);color:var(--text-2);text-transform:uppercase;letter-spacing:.5px}
.sx-meta-chip.lvl{background:rgba(28,176,246,.16);color:var(--blue)}
.sx-meta-chip.mast-mastered{background:rgba(88,204,2,.18);color:var(--green)}
.sx-meta-chip.mast-familiar{background:rgba(28,176,246,.16);color:var(--blue)}
.sx-meta-chip.mast-learning{background:rgba(255,165,79,.16);color:var(--orange)}
.sx-meta-chip.mast-new{background:rgba(255,255,255,.06);color:var(--g4)}
.sx-conj{margin-top:6px;display:grid;grid-template-columns:auto 1fr;gap:4px 12px;font-size:13px}
.sx-conj-p{color:var(--g5);font-weight:700}
.sx-conj-v{color:var(--text-1);font-weight:600}
```

### Step 3: Update the bnav on Home, Progress, and Profile screens

There are three bottom-nav blocks (in `#home`, `#progress`, `#prof`). Each currently has three buttons. Insert a Search button as the third item (between Progress/Social and Profile, so the order becomes Learn → Progress → Search → Profile).

**Home (around line 717-720):**

Find:
```html
    <button class="ni act" onclick="S.goHome()"><span class="ni-i" data-icon="home"></span><span class="ni-l">Learn</span></button>
    <button class="ni" onclick="S.goProgress()"><span class="ni-i" data-icon="chart"></span><span class="ni-l">Progress</span></button>
    <button class="ni" onclick="S.goProfile()"><span class="ni-i" data-icon="user"></span><span class="ni-l">Profile</span></button>
```

Replace with:
```html
    <button class="ni act" onclick="S.goHome()"><span class="ni-i" data-icon="home"></span><span class="ni-l">Learn</span></button>
    <button class="ni" onclick="S.goProgress()"><span class="ni-i" data-icon="chart"></span><span class="ni-l">Progress</span></button>
    <button class="ni" onclick="S.goSearch()"><span class="ni-i" data-icon="search"></span><span class="ni-l">Search</span></button>
    <button class="ni" onclick="S.goProfile()"><span class="ni-i" data-icon="user"></span><span class="ni-l">Profile</span></button>
```

**Progress (around lines 791-794):** same pattern — three buttons become four, Search is third (no `act`, since Progress is active).

```html
    <button class="ni ni-lt" onclick="S.goHome()"><span class="ni-i" data-icon="home"></span><span class="ni-l">Learn</span></button>
    <button class="ni ni-lt act" onclick="S.goProgress()"><span class="ni-i" data-icon="chart"></span><span class="ni-l">Progress</span></button>
    <button class="ni ni-lt" onclick="S.goSearch()"><span class="ni-i" data-icon="search"></span><span class="ni-l">Search</span></button>
    <button class="ni ni-lt" onclick="S.goProfile()"><span class="ni-i" data-icon="user"></span><span class="ni-l">Profile</span></button>
```

**Profile (around lines 833-835):** same pattern.

```html
    <button class="ni ni-lt" onclick="S.goHome()"><span class="ni-i" data-icon="home"></span><span class="ni-l">Learn</span></button>
    <button class="ni ni-lt" onclick="S.goProgress()"><span class="ni-i" data-icon="chart"></span><span class="ni-l">Progress</span></button>
    <button class="ni ni-lt" onclick="S.goSearch()"><span class="ni-i" data-icon="search"></span><span class="ni-l">Search</span></button>
    <button class="ni ni-lt act" onclick="S.goProfile()"><span class="ni-i" data-icon="user"></span><span class="ni-l">Profile</span></button>
```

### Step 4: Add `#search` screen DOM

Find the `<div class="sc" id="progress">` block (around line 789). Insert the new `#search` screen IMMEDIATELY AFTER the `</div>` that closes `#progress` (and before `<div class="sc" id="prof">`):

```html
<div class="sc" id="search">
  <div class="sx-head">
    <input class="sx-input" id="sx-input" placeholder="Search words…" autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false" oninput="S.onSearchInput()">
    <button class="sx-clear" id="sx-clear" onclick="S.clearSearch()" style="display:none">×</button>
  </div>
  <div class="sx-body" id="sx-body"></div>
  <div class="bnav bnav-lt">
    <button class="ni ni-lt" onclick="S.goHome()"><span class="ni-i" data-icon="home"></span><span class="ni-l">Learn</span></button>
    <button class="ni ni-lt" onclick="S.goProgress()"><span class="ni-i" data-icon="chart"></span><span class="ni-l">Progress</span></button>
    <button class="ni ni-lt act" onclick="S.goSearch()"><span class="ni-i" data-icon="search"></span><span class="ni-l">Search</span></button>
    <button class="ni ni-lt" onclick="S.goProfile()"><span class="ni-i" data-icon="user"></span><span class="ni-l">Profile</span></button>
  </div>
</div>
```

### Step 5: Add search index + match logic

Find (around line 3198, after `buildOverflowSession()` closes):

```js
function buildOverflowSession(){
  // ... existing function ...
  return{cards:session,breakdown:{new:newCount,preview:previewCount,weak:weakCount}};
}
```

Insert immediately after (at module scope):

```js
// ═══════════════ DICTIONARY SEARCH ═══════════════

// Normalize for matching: lowercase + strip diacritics (ć→c, ž→z, etc.)
function _sxNorm(s){return(s||'').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'');}

// Build the flat searchable index for the current language.
// Returns array of {type, word, source, english, normSource, normEnglish}
function _sxIndex(){
  const idx=[];
  UNITS.forEach(u=>{
    u.words.forEach(w=>{
      idx.push({type:'word',word:w,unit:u,source:w.l,english:w.e,normSource:_sxNorm(w.l),normEnglish:_sxNorm(w.e)});
    });
  });
  VERBS.forEach(v=>{
    idx.push({type:'verb',verb:v,source:v.inf,english:v.en,normSource:_sxNorm(v.inf),normEnglish:_sxNorm(v.en)});
  });
  return idx;
}

// Cached index (rebuild when language changes)
let _SX_CACHE=null,_SX_LANG=null;
function sxIndex(){if(_SX_CACHE&&_SX_LANG===curLang)return _SX_CACHE;_SX_CACHE=_sxIndex();_SX_LANG=curLang;return _SX_CACHE;}

// Score: 3=exact, 2=prefix, 1=substring, 0=no match
function _sxScore(haystack,needle){
  if(haystack===needle)return 3;
  if(haystack.startsWith(needle))return 2;
  if(haystack.indexOf(needle)>=0)return 1;
  return 0;
}

// Search returns array of {entry, score} sorted by score desc then alpha asc
function sxSearch(query){
  const q=_sxNorm(query.trim());
  if(!q)return[];
  const idx=sxIndex();
  const results=[];
  idx.forEach(e=>{
    const sS=_sxScore(e.normSource,q);
    const sE=_sxScore(e.normEnglish,q);
    const score=Math.max(sS,sE);
    if(score>0)results.push({entry:e,score});
  });
  results.sort((a,b)=>b.score-a.score||a.entry.source.localeCompare(b.entry.source));
  return results;
}
```

### Step 6: Commit

```bash
git add index.html
git commit -m "Add Dictionary Search scaffolding (CSS, DOM, nav, index)"
```

---

## Task 2: Render logic — goSearch, render, expand, debounce

**File:** `index.html`

### Step 1: Add `goSearch` + render methods on `S`

Find the existing `goProgress()` method (around line 4772 — search the file). Insert these new methods IMMEDIATELY AFTER `goProgress`'s closing `},`:

```js
goSearch(){
  this.goScr('search');
  // Re-render results to refresh mastery state, then focus input
  const input=document.getElementById('sx-input');
  this.renderSearchResults(input.value||'');
  setTimeout(()=>{if(input)input.focus();},50);
},

clearSearch(){
  const input=document.getElementById('sx-input');
  input.value='';
  document.getElementById('sx-clear').style.display='none';
  this.renderSearchResults('');
  input.focus();
},

_sxDebounce:null,
_sxExpanded:null,

onSearchInput(){
  const v=document.getElementById('sx-input').value;
  document.getElementById('sx-clear').style.display=v?'':'none';
  clearTimeout(this._sxDebounce);
  this._sxDebounce=setTimeout(()=>this.renderSearchResults(v),120);
},

renderSearchResults(query){
  const el=document.getElementById('sx-body');
  const q=(query||'').trim();
  if(!q){
    const idx=sxIndex();
    el.innerHTML='<div class="sx-empty">Type a word in '+esc(langName())+' or English to look it up.<br><span style="color:var(--g5);font-size:12px">'+idx.length+' entries available</span></div>';
    this._sxExpanded=null;
    return;
  }
  const results=sxSearch(q);
  if(results.length===0){
    el.innerHTML='<div class="sx-empty">No results for "<strong style="color:var(--text-2)">'+esc(q)+'</strong>".</div>';
    this._sxExpanded=null;
    return;
  }
  // Cap to a reasonable number for performance — 80 is plenty
  const shown=results.slice(0,80);
  let h='';
  shown.forEach((r,i)=>{
    const e=r.entry;
    const isExpanded=this._sxExpanded===i;
    h+='<div class="sx-row'+(isExpanded?' expanded':'')+'" onclick="S.toggleSearchExpand('+i+')">';
    h+='<div class="sx-row-collapsed">';
    h+='<div class="sx-source'+(e.type==='verb'?' verb-tag':'')+'">'+esc(e.source)+'</div>';
    h+='<div class="sx-trans">'+esc(e.english)+'</div>';
    h+='</div>';
    if(isExpanded){h+=this._renderSearchExpansion(e);}
    h+='</div>';
  });
  el.innerHTML=h;
  // Store the result list for click handlers
  this._sxLastResults=shown;
},

toggleSearchExpand(i){
  this._sxExpanded=(this._sxExpanded===i)?null:i;
  const q=document.getElementById('sx-input').value;
  this.renderSearchResults(q);
},

_renderSearchExpansion(e){
  let h='<div class="sx-expand">';
  h+='<div class="sx-expand-word">'+esc(e.source)+spkBtn(e.source,curLang)+'</div>';
  h+='<div class="sx-expand-trans">'+esc(e.english)+'</div>';
  // Meta chips
  const chips=[];
  if(e.type==='word'){
    if(e.unit.lv)chips.push('<span class="sx-meta-chip lvl">'+esc(e.unit.lv)+'</span>');
    chips.push('<span class="sx-meta-chip">'+esc(e.unit.ic||'')+' '+esc(e.unit.t)+'</span>');
    // Mastery state for this word (use 'se' direction as canonical)
    const c=st.fc[fcKey(e.word.id,'se')];
    let mast='new',label='Not yet seen';
    if(c&&c.reps>=2&&c.ivl>=21){mast='mastered';label='Mastered';}
    else if(c&&c.reps>=2){mast='familiar';label='Familiar';}
    else if(c&&c.reps>=1){mast='learning';label='Learning';}
    chips.push('<span class="sx-meta-chip mast-'+mast+'">'+label+'</span>');
  }else{
    chips.push('<span class="sx-meta-chip">Verb · base form</span>');
  }
  h+='<div class="sx-expand-meta">'+chips.join('')+'</div>';
  // Verb conjugation table — keys are ja/ti/on/mi/vi/oni
  if(e.type==='verb'&&e.verb.conj){
    h+='<div class="sx-conj">';
    const PRON_LABEL={ja:'ja',ti:'ti',on:'on/ona',mi:'mi',vi:'vi',oni:'oni'};
    ['ja','ti','on','mi','vi','oni'].forEach(k=>{
      if(e.verb.conj[k]){
        h+='<div class="sx-conj-p">'+(PRON_LABEL[k]||k)+'</div><div class="sx-conj-v">'+esc(e.verb.conj[k])+'</div>';
      }
    });
    h+='</div>';
  }
  h+='</div>';
  return h;
},
```

### Step 2: Invalidate the index cache when language changes

Find the `setLang()` function (search for `function setLang`). At the end (or after `LANG_DATA[code]` operations), add:

```js
  _SX_CACHE=null;
```

This forces the search index to rebuild for the new language.

### Step 3: Commit

```bash
git add index.html
git commit -m "Implement Dictionary Search render + interactions"
```

---

## Task 3: Smoke + deploy

- [ ] Open the app. Tap Search in bottom nav. Confirm:
  - Empty state shows "Type a word in Serbian/Italian or English to look it up."
  - Input is focused.
  - Typing "pro" filters to results containing "pro" (case + diacritic insensitive).
  - Typing "obecavati" (no diacritics) finds "obećavati".
  - "X" clear button appears when input has text.
  - Tapping a row expands it inline with word + translation + 🔊 + CEFR chip + unit chip + mastery chip.
  - For verbs (e.g., type "biti"), the expansion includes a conjugation table.
  - Audio plays on speaker tap.
  - Bottom nav has 4 buttons across Home/Progress/Search/Profile.
- [ ] Cherry-pick onto main and push.
