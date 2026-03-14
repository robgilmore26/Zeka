# Usernames & Friends Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace name/email profile with username-based social system — usernames, friend codes, friend requests, and friend profile viewing.

**Architecture:** All data in Firestore root collections (`usernames/`, `friendCodes/`, `friendRequests/`). Client-side logic only, no Cloud Functions. Single-file app (`index.html`).

**Tech Stack:** Firebase Firestore (compat SDK), vanilla JS, CSS

---

### Task 1: Update Firestore Security Rules

**Where:** Firebase Console → Firestore → Rules

**Step 1: Update rules in Firebase Console**

Navigate to https://console.firebase.google.com → Zeka project → Firestore → Rules. Replace with:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null && request.auth.uid == userId;
    }
    match /usernames/{username} {
      allow read: if request.auth != null;
      allow create: if request.auth != null && request.resource.data.uid == request.auth.uid;
      allow delete: if request.auth != null && resource.data.uid == request.auth.uid;
    }
    match /friendCodes/{code} {
      allow read: if request.auth != null;
      allow create: if request.auth != null && request.resource.data.uid == request.auth.uid;
    }
    match /friendRequests/{userId} {
      allow read: if request.auth != null && request.auth.uid == userId;
      allow write: if request.auth != null;
    }
  }
}
```

**Step 2: Publish and verify**

Click "Publish". Verify no errors.

**Step 3: Commit a note**

```bash
git commit --allow-empty -m "docs: updated Firestore rules for usernames, friendCodes, friendRequests collections"
```

---

### Task 2: Add Username Setup CSS

**Files:**
- Modify: `index.html` CSS section (~line 226-253)

**Step 1: Add CSS for username setup, friends list, add-friend modal, friend profile view**

Add after the existing `/* PROFILE */` CSS block (after line 253, before `/* REVIEW */`):

```css
/* USERNAME SETUP */
.uname-setup{padding:20px 22px;text-align:center}
.uname-setup input{width:100%;padding:14px;border:2px solid var(--g3);border-radius:14px;font-size:17px;font-family:var(--font);font-weight:600;color:var(--g7);outline:none;margin:10px 0;box-sizing:border-box}
.uname-setup input:focus{border-color:var(--blue)}
.uname-err{color:var(--red);font-size:12px;font-weight:600;min-height:18px}
.uname-ok{color:var(--green);font-size:12px;font-weight:600}
.uname-save{padding:12px 32px;border:none;border-radius:14px;background:var(--green);color:#fff;font-size:16px;font-weight:800;cursor:pointer;box-shadow:0 4px 0 var(--green-d)}
.uname-save:disabled{opacity:.4;cursor:default}
.uname-save:active:not(:disabled){transform:translateY(2px);box-shadow:0 2px 0 var(--green-d)}
.p-uname{font-size:16px;font-weight:600;opacity:.9;margin-top:2px}
.p-code{display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,.15);padding:4px 12px;border-radius:10px;font-size:13px;font-weight:700;margin-top:8px;cursor:pointer}
.p-code:active{background:rgba(255,255,255,.25)}

/* FRIENDS */
.fr-sec{padding:8px 22px 12px}
.fr-hdr{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.fr-hdr-t{font-size:16px;font-weight:800;color:var(--g7)}
.fr-add-btn{padding:8px 14px;border:none;border-radius:10px;background:var(--blue);color:#fff;font-size:13px;font-weight:700;cursor:pointer}
.fr-add-btn:active{opacity:.8}
.fr-empty{text-align:center;color:var(--g4);font-size:14px;padding:20px 0}
.fr-row{display:flex;align-items:center;gap:12px;padding:12px;border:2px solid var(--g2);border-radius:14px;margin-bottom:8px;cursor:pointer;transition:.15s}
.fr-row:active{background:var(--g1)}
.fr-av{width:40px;height:40px;border-radius:50%;background:var(--g1);display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0}
.fr-inf{flex:1;min-width:0}
.fr-nm{font-size:14px;font-weight:800;color:var(--g7)}
.fr-sub{font-size:11px;color:var(--g5);margin-top:1px}
.fr-elo{font-size:14px;font-weight:800;color:var(--blue)}

/* FRIEND REQUESTS */
.fr-req{border-color:var(--blue);background:#f0f8ff}
.fr-req-acts{display:flex;gap:8px;flex-shrink:0}
.fr-req-btn{padding:6px 12px;border:none;border-radius:8px;font-size:12px;font-weight:700;cursor:pointer}
.fr-req-acc{background:var(--green);color:#fff}
.fr-req-dec{background:var(--g2);color:var(--g5)}

/* ADD FRIEND MODAL */
.modal-bg{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.5);z-index:200;display:flex;align-items:flex-end;justify-content:center}
.modal-box{background:var(--w);border-radius:20px 20px 0 0;width:100%;max-width:430px;max-height:70vh;overflow-y:auto;padding:20px 22px 40px}
.modal-hdr{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
.modal-hdr h3{font-size:18px;font-weight:800;margin:0}
.modal-x{background:none;border:none;font-size:24px;cursor:pointer;color:var(--g5);padding:4px}
.modal-tabs{display:flex;gap:0;margin-bottom:16px;border-bottom:2px solid var(--g2)}
.modal-tab{flex:1;padding:10px;text-align:center;font-size:14px;font-weight:700;color:var(--g4);cursor:pointer;border-bottom:3px solid transparent;margin-bottom:-2px;background:none;border-top:none;border-left:none;border-right:none}
.modal-tab.act{color:var(--blue);border-bottom-color:var(--blue)}
.modal-body{min-height:120px}
.modal-input{width:100%;padding:12px;border:2px solid var(--g3);border-radius:12px;font-size:15px;font-family:var(--font);font-weight:600;outline:none;margin-bottom:10px;box-sizing:border-box}
.modal-input:focus{border-color:var(--blue)}
.modal-result{padding:12px;border:2px solid var(--g2);border-radius:12px;display:flex;align-items:center;gap:12px}
.modal-send{padding:8px 16px;border:none;border-radius:10px;background:var(--blue);color:#fff;font-size:13px;font-weight:700;cursor:pointer;flex-shrink:0}
.modal-send:disabled{opacity:.4}
.modal-msg{text-align:center;font-size:13px;color:var(--g5);padding:10px 0}
.modal-code-display{text-align:center;padding:20px 0}
.modal-code-big{font-size:32px;font-weight:800;letter-spacing:3px;color:var(--g7);margin-bottom:10px}
.modal-code-copy{padding:10px 20px;border:2px solid var(--g2);border-radius:12px;background:var(--w);font-size:14px;font-weight:700;cursor:pointer;color:var(--g7)}
.modal-code-copy:active{background:var(--g1)}

/* FRIEND PROFILE VIEW */
.fp-back{display:flex;align-items:center;gap:8px;padding:12px 22px;cursor:pointer;color:var(--blue);font-weight:700;font-size:14px;background:none;border:none;font-family:var(--font)}
```

**Step 2: Commit**

```bash
git add index.html
git commit -m "style: add CSS for username setup, friends list, modal, friend profile"
```

---

### Task 3: Add Username & Friend Code Generation Functions

**Files:**
- Modify: `index.html` JS section, after `fbSaveCloud` function (~line 1595)

**Step 1: Add helper functions**

Insert after the `fbSaveCloud` closing brace:

```javascript
// ═══════════════ USERNAME & FRIENDS ═══════════════
function genFriendCode(){
  const chars='ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  let c='ZK-';
  for(let i=0;i<4;i++)c+=chars[Math.floor(Math.random()*chars.length)];
  return c;
}

async function setUsername(name){
  if(!fbUser)throw new Error('Not signed in');
  const uname=name.toLowerCase().trim();
  if(!/^[a-z0-9_]{3,20}$/.test(uname))throw new Error('3-20 chars, letters/numbers/underscores only');
  // Check 30-day limit
  const userDoc=await fbDb.collection('users').doc(fbUser.uid).get();
  if(userDoc.exists){
    const data=userDoc.data();
    if(data.usernameSetAt){
      const days=(Date.now()-data.usernameSetAt.toMillis())/(1000*60*60*24);
      if(days<30)throw new Error('Can only change username every 30 days');
    }
    // Delete old username doc
    if(data.username){
      await fbDb.collection('usernames').doc(data.username).delete().catch(()=>{});
    }
  }
  // Check uniqueness
  const existing=await fbDb.collection('usernames').doc(uname).get();
  if(existing.exists&&existing.data().uid!==fbUser.uid)throw new Error('Username taken');
  // Generate friend code if needed
  let code=userDoc.exists&&userDoc.data().friendCode?userDoc.data().friendCode:null;
  if(!code){
    code=genFriendCode();
    await fbDb.collection('friendCodes').doc(code).set({uid:fbUser.uid});
  }
  // Save username doc
  await fbDb.collection('usernames').doc(uname).set({uid:fbUser.uid});
  // Update user doc
  await fbDb.collection('users').doc(fbUser.uid).set({
    username:uname,
    friendCode:code,
    usernameSetAt:firebase.firestore.FieldValue.serverTimestamp()
  },{merge:true});
  return{username:uname,friendCode:code};
}

async function searchUser(query){
  const uname=query.toLowerCase().trim();
  if(!uname)return null;
  const doc=await fbDb.collection('usernames').doc(uname).get();
  if(!doc.exists)return null;
  const uid=doc.data().uid;
  if(uid===fbUser.uid)return null;// can't add yourself
  const userDoc=await fbDb.collection('users').doc(uid).get();
  if(!userDoc.exists)return null;
  const d=userDoc.data();
  return{uid,username:d.username,elo:d.langs&&d.langs[d.activeLang||'sr']?d.langs[d.activeLang||'sr'].elo:1000,friendCode:d.friendCode};
}

async function lookupFriendCode(code){
  const doc=await fbDb.collection('friendCodes').doc(code.toUpperCase().trim()).get();
  if(!doc.exists)return null;
  const uid=doc.data().uid;
  if(uid===fbUser.uid)return null;
  const userDoc=await fbDb.collection('users').doc(uid).get();
  if(!userDoc.exists)return null;
  const d=userDoc.data();
  return{uid,username:d.username,elo:d.langs&&d.langs[d.activeLang||'sr']?d.langs[d.activeLang||'sr'].elo:1000};
}

async function sendFriendRequest(targetUid,myUsername){
  const reqRef=fbDb.collection('friendRequests').doc(targetUid);
  const doc=await reqRef.get();
  const reqs=doc.exists?(doc.data().requests||[]):[];
  // Don't duplicate
  if(reqs.some(r=>r.fromUid===fbUser.uid))throw new Error('Request already sent');
  reqs.push({fromUid:fbUser.uid,fromUsername:myUsername,sentAt:Date.now()});
  await reqRef.set({requests:reqs});
}

async function acceptFriend(fromUid){
  // Add to both friends lists
  const myRef=fbDb.collection('users').doc(fbUser.uid);
  const theirRef=fbDb.collection('users').doc(fromUid);
  const myDoc=await myRef.get();
  const theirDoc=await theirRef.get();
  const myFriends=myDoc.exists?(myDoc.data().friends||[]):[];
  const theirFriends=theirDoc.exists?(theirDoc.data().friends||[]):[];
  if(!myFriends.includes(fromUid))myFriends.push(fromUid);
  if(!theirFriends.includes(fbUser.uid))theirFriends.push(fbUser.uid);
  await myRef.set({friends:myFriends},{merge:true});
  await theirRef.set({friends:theirFriends},{merge:true});
  // Remove request
  await removeRequest(fromUid);
}

async function declineRequest(fromUid){
  await removeRequest(fromUid);
}

async function removeRequest(fromUid){
  const reqRef=fbDb.collection('friendRequests').doc(fbUser.uid);
  const doc=await reqRef.get();
  if(!doc.exists)return;
  const reqs=(doc.data().requests||[]).filter(r=>r.fromUid!==fromUid);
  await reqRef.set({requests:reqs});
}

async function loadFriendRequests(){
  if(!fbUser)return[];
  try{
    const doc=await fbDb.collection('friendRequests').doc(fbUser.uid).get();
    return doc.exists?(doc.data().requests||[]):[];
  }catch(e){return[];}
}

async function loadFriendProfiles(friendUids){
  if(!friendUids||!friendUids.length)return[];
  const profiles=[];
  for(const uid of friendUids){
    try{
      const doc=await fbDb.collection('users').doc(uid).get();
      if(doc.exists){
        const d=doc.data();
        // Find most active language (highest XP)
        let activeLang='sr',maxXp=0;
        if(d.langs){
          for(const[lang,data]of Object.entries(d.langs)){
            if(data.xp>maxXp){maxXp=data.xp;activeLang=lang;}
          }
        }
        const langData=d.langs&&d.langs[activeLang]?d.langs[activeLang]:{};
        profiles.push({uid,username:d.username||'unknown',elo:langData.elo||1000,xp:langData.xp||0,
          streak:langData.streak||0,completed:(langData.completed||[]).length,
          wordsLearned:Object.keys(langData.ws||{}).filter(k=>(langData.ws||{})[k].c>0).length,
          activeLang,friendCode:d.friendCode});
      }
    }catch(e){}
  }
  return profiles;
}
```

**Step 2: Commit**

```bash
git add index.html
git commit -m "feat: add username, friend code, friend request Firestore functions"
```

---

### Task 4: Rebuild Profile HTML

**Files:**
- Modify: `index.html` profile section (~line 398-424)

**Step 1: Replace the profile screen HTML**

Replace the entire `<div class="sc" id="prof">...</div>` block with:

```html
<div class="sc" id="prof">
  <div class="ptop">
    <div class="pav" id="p-avatar"><img src="icon-192.png" style="width:60px;height:60px;border-radius:16px" alt="Zeka"></div>
    <div class="pnm" id="p-name"></div>
    <div class="p-uname" id="p-uname"></div>
    <div class="pjn" id="p-lvl">Novice</div>
    <div class="pelo" id="p-elo">1000</div>
    <div class="pelbl">ELO Rating</div>
    <div class="p-code" id="p-code" onclick="S.copyCode()" style="display:none"><span id="p-code-val"></span> <span>📋</span></div>
  </div>
  <div class="uname-setup" id="uname-setup" style="display:none">
    <div style="font-size:16px;font-weight:700;color:var(--g7)">Choose a username</div>
    <input type="text" id="uname-inp" placeholder="e.g. polyglot_pro" maxlength="20" autocomplete="off" autocapitalize="off" oninput="S.checkUname()">
    <div class="uname-err" id="uname-err"></div>
    <button class="uname-save" id="uname-btn" disabled onclick="S.saveUname()">Save Username</button>
  </div>
  <div class="psg">
    <div class="psc"><div class="psc-i">🔥</div><div class="psc-v" id="p-str">0</div><div class="psc-l">Streak</div></div>
    <div class="psc"><div class="psc-i">⚡</div><div class="psc-v" id="p-xp">0</div><div class="psc-l">Total XP</div></div>
    <div class="psc"><div class="psc-i">📚</div><div class="psc-v" id="p-les">0</div><div class="psc-l">Lessons</div></div>
    <div class="psc"><div class="psc-i">🏆</div><div class="psc-v" id="p-wrd">0</div><div class="psc-l">Words</div></div>
  </div>
  <div class="fr-sec" id="fr-sec">
    <div class="fr-hdr"><span class="fr-hdr-t" id="fr-hdr-t">Friends</span><button class="fr-add-btn" onclick="S.openAddFriend()">+ Add Friend</button></div>
    <div id="fr-reqs"></div>
    <div id="fr-list"></div>
  </div>
  <div class="pach" id="p-ach"></div>
  <div class="sync-sec">
    <button class="sync-btn" id="sync-btn" onclick="fbSignOut()" style="display:none">Sign Out</button>
    <div id="g-signin-prof" style="display:flex;justify-content:center"></div>
    <div class="sync-status" id="sync-status"></div>
  </div>
  <div class="bnav bnav-lt">
    <button class="ni ni-lt" onclick="S.goHome()"><span class="ni-i">🏠</span><span class="ni-l">Learn</span></button>
    <button class="ni ni-lt" onclick="S.goReview()"><span class="ni-i">📝</span><span class="ni-l">Review</span></button>
    <button class="ni ni-lt act" onclick="S.goProfile()"><span class="ni-i">👤</span><span class="ni-l">Profile</span></button>
  </div>
</div>
```

**Step 2: Commit**

```bash
git add index.html
git commit -m "feat: rebuild profile HTML with username, friend code, friends section"
```

---

### Task 5: Rebuild goProfile() and Add Friend UI Methods

**Files:**
- Modify: `index.html` JS — replace `goProfile()` and add new methods to the `S` object (~line 2133)

**Step 1: Replace `goProfile()` in the S object**

Replace the existing `goProfile(){...}` method with the following (before the closing `};` of the S object):

```javascript
async goProfile(){
  // Stats
  document.getElementById('p-elo').textContent=st.elo;
  document.getElementById('p-lvl').textContent=ELO.lvl(st.elo);
  document.getElementById('p-str').textContent=st.streak;
  document.getElementById('p-xp').textContent=st.xp;
  document.getElementById('p-les').textContent=st.completed.length;
  document.getElementById('p-wrd').textContent=Object.keys(st.ws).filter(k=>st.ws[k].c>0).length;
  // Username
  const setup=document.getElementById('uname-setup');
  const unameEl=document.getElementById('p-uname');
  const codeEl=document.getElementById('p-code');
  const nameEl=document.getElementById('p-name');
  if(fbUser){
    const doc=await fbDb.collection('users').doc(fbUser.uid).get();
    const data=doc.exists?doc.data():{};
    if(data.username){
      nameEl.textContent='';
      unameEl.textContent='@'+data.username;
      setup.style.display='none';
      if(data.friendCode){
        codeEl.style.display='';
        document.getElementById('p-code-val').textContent=data.friendCode;
      }
      // Load friends
      this.loadFriends(data.friends||[]);
    }else{
      nameEl.textContent='Welcome!';
      unameEl.textContent='';
      setup.style.display='';
      codeEl.style.display='none';
    }
  }else{
    nameEl.textContent='Guest';
    unameEl.textContent='';
    setup.style.display='none';
    codeEl.style.display='none';
  }
  // Achievements
  const ach=document.getElementById('p-ach');
  const a=[{i:'🎯',n:'First Lesson',d:'Complete 1 lesson',u:st.completed.length>=1},
    {i:'🔥',n:'On Fire',d:'3-day streak',u:st.streak>=3},{i:'💯',n:'Century',d:'Earn 100 XP',u:st.xp>=100},
    {i:'📚',n:'Scholar',d:'Complete 10 units',u:st.completed.length>=10},
    {i:'🏆',n:'Polyglot',d:'Complete 20 units',u:st.completed.length>=20},
    {i:'👑',n:'Master',d:'All '+UNITS.length+' units done',u:st.completed.length>=UNITS.length},
    {i:'⚡',n:'Lightning',d:'Earn 500 XP',u:st.xp>=500},
    {i:'🧠',n:'Big Brain',d:'Reach ELO 1500',u:st.elo>=1500},
    {i:'🌟',n:'Expert',d:'Reach ELO 1900',u:st.elo>=1900}];
  ach.innerHTML='<div class="psect">Achievements</div>'+a.map(x=>
    '<div class="arow '+(x.u?'':'lk')+'"><div class="arow-i">'+x.i+'</div><div class="arow-inf"><div class="arow-n">'+x.n+'</div><div class="arow-d">'+x.d+'</div></div><div>'+(x.u?'✅':'🔒')+'</div></div>').join('');
  this.goScr('prof');
  updateSyncUI();
},

checkUname(){
  const inp=document.getElementById('uname-inp');
  const err=document.getElementById('uname-err');
  const btn=document.getElementById('uname-btn');
  const v=inp.value.toLowerCase().trim();
  if(!v){err.textContent='';btn.disabled=true;return;}
  if(!/^[a-z0-9_]{3,20}$/.test(v)){
    err.textContent='3-20 characters, letters/numbers/underscores only';
    err.className='uname-err';btn.disabled=true;return;
  }
  err.textContent='Checking...';err.className='uname-err';btn.disabled=true;
  clearTimeout(this._unameTimer);
  this._unameTimer=setTimeout(async()=>{
    try{
      const doc=await fbDb.collection('usernames').doc(v).get();
      if(doc.exists&&doc.data().uid!==fbUser.uid){
        err.textContent='Username taken';err.className='uname-err';btn.disabled=true;
      }else{
        err.textContent='Available!';err.className='uname-ok';btn.disabled=false;
      }
    }catch(e){err.textContent='Error checking';err.className='uname-err';}
  },500);
},

async saveUname(){
  const inp=document.getElementById('uname-inp');
  const err=document.getElementById('uname-err');
  const btn=document.getElementById('uname-btn');
  btn.disabled=true;btn.textContent='Saving...';
  try{
    await setUsername(inp.value);
    this.goProfile();
  }catch(e){
    err.textContent=e.message;err.className='uname-err';
    btn.disabled=false;btn.textContent='Save Username';
  }
},

copyCode(){
  const code=document.getElementById('p-code-val').textContent;
  navigator.clipboard.writeText(code).then(()=>{
    const el=document.getElementById('p-code');
    el.querySelector('span:last-child').textContent='✅';
    setTimeout(()=>{el.querySelector('span:last-child').textContent='📋';},1500);
  }).catch(()=>{});
},

async loadFriends(friendUids){
  const reqsEl=document.getElementById('fr-reqs');
  const listEl=document.getElementById('fr-list');
  const hdrEl=document.getElementById('fr-hdr-t');
  // Load pending requests
  const reqs=await loadFriendRequests();
  if(reqs.length){
    reqsEl.innerHTML=reqs.map(r=>
      '<div class="fr-row fr-req"><div class="fr-av">👤</div><div class="fr-inf"><div class="fr-nm">@'+r.fromUsername+'</div><div class="fr-sub">wants to be friends</div></div><div class="fr-req-acts"><button class="fr-req-btn fr-req-acc" onclick="S.acceptReq(\''+r.fromUid+'\')">Accept</button><button class="fr-req-btn fr-req-dec" onclick="S.declineReq(\''+r.fromUid+'\')">Decline</button></div></div>'
    ).join('');
  }else{reqsEl.innerHTML='';}
  // Load friend profiles
  if(!friendUids.length){
    hdrEl.textContent='Friends';
    listEl.innerHTML='<div class="fr-empty">No friends yet. Add friends to see their progress!</div>';
    return;
  }
  hdrEl.textContent='Friends ('+friendUids.length+')';
  listEl.innerHTML='<div class="fr-empty">Loading...</div>';
  const profiles=await loadFriendProfiles(friendUids);
  const flags={sr:'rs',it:'it'};
  listEl.innerHTML=profiles.map(p=>{
    const flagCode=flags[p.activeLang]||'rs';
    return '<div class="fr-row" onclick="S.viewFriend(\''+p.uid+'\')"><div class="fr-av">👤</div><div class="fr-inf"><div class="fr-nm">@'+p.username+'</div><div class="fr-sub"><img src="https://flagcdn.com/w20/'+flagCode+'.png" style="height:12px;vertical-align:-1px"> '+p.xp+' XP</div></div><div class="fr-elo">'+p.elo+'</div></div>';
  }).join('');
},

async acceptReq(fromUid){
  try{await acceptFriend(fromUid);this.goProfile();}catch(e){}
},

async declineReq(fromUid){
  try{await declineRequest(fromUid);this.goProfile();}catch(e){}
},

openAddFriend(){
  const bg=document.createElement('div');bg.className='modal-bg';bg.id='add-fr-modal';
  bg.onclick=e=>{if(e.target===bg)bg.remove();};
  bg.innerHTML='<div class="modal-box"><div class="modal-hdr"><h3>Add Friend</h3><button class="modal-x" onclick="document.getElementById(\'add-fr-modal\').remove()">✕</button></div><div class="modal-tabs"><button class="modal-tab act" onclick="S.frTab(\'search\')">Search</button><button class="modal-tab" onclick="S.frTab(\'code\')">Friend Code</button></div><div class="modal-body" id="fr-modal-body"></div></div>';
  document.body.appendChild(bg);
  this.frTab('search');
},

frTab(tab){
  document.querySelectorAll('.modal-tab').forEach((t,i)=>t.classList.toggle('act',i===(tab==='search'?0:1)));
  const body=document.getElementById('fr-modal-body');
  if(tab==='search'){
    body.innerHTML='<input class="modal-input" id="fr-search-inp" placeholder="Enter username..." autocomplete="off" autocapitalize="off"><div id="fr-search-result" class="modal-msg">Type a username to search</div>';
    document.getElementById('fr-search-inp').addEventListener('input',()=>{
      clearTimeout(this._frSearchT);
      this._frSearchT=setTimeout(()=>this.doFrSearch(),500);
    });
  }else{
    const code=document.getElementById('p-code-val');
    const myCode=code?code.textContent:'';
    body.innerHTML='<div class="modal-code-display"><div style="font-size:13px;color:var(--g5);margin-bottom:6px">Your friend code</div><div class="modal-code-big">'+myCode+'</div><button class="modal-code-copy" onclick="navigator.clipboard.writeText(\''+myCode+'\');this.textContent=\'Copied!\'">Copy Code</button></div><div style="border-top:2px solid var(--g2);margin:16px 0;padding-top:16px"><div style="font-size:13px;color:var(--g5);margin-bottom:8px">Enter a friend\'s code</div><input class="modal-input" id="fr-code-inp" placeholder="e.g. ZK-A7X3" autocomplete="off" autocapitalize="off" style="text-transform:uppercase"><div id="fr-code-result" class="modal-msg"></div></div>';
    document.getElementById('fr-code-inp').addEventListener('input',()=>{
      clearTimeout(this._frCodeT);
      this._frCodeT=setTimeout(()=>this.doCodeLookup(),500);
    });
  }
},

async doFrSearch(){
  const inp=document.getElementById('fr-search-inp');
  const res=document.getElementById('fr-search-result');
  if(!inp.value.trim()){res.innerHTML='<div class="modal-msg">Type a username to search</div>';return;}
  res.innerHTML='<div class="modal-msg">Searching...</div>';
  const user=await searchUser(inp.value);
  if(!user){res.innerHTML='<div class="modal-msg">No user found</div>';return;}
  res.innerHTML='<div class="modal-result"><div class="fr-av">👤</div><div class="fr-inf"><div class="fr-nm">@'+user.username+'</div><div class="fr-sub">ELO '+user.elo+'</div></div><button class="modal-send" onclick="S.sendReq(\''+user.uid+'\')">Send Request</button></div>';
},

async doCodeLookup(){
  const inp=document.getElementById('fr-code-inp');
  const res=document.getElementById('fr-code-result');
  const v=inp.value.trim();
  if(v.length<6){res.innerHTML='';return;}
  res.innerHTML='<div class="modal-msg">Looking up...</div>';
  const user=await lookupFriendCode(v);
  if(!user){res.innerHTML='<div class="modal-msg">No user found with that code</div>';return;}
  res.innerHTML='<div class="modal-result"><div class="fr-av">👤</div><div class="fr-inf"><div class="fr-nm">@'+user.username+'</div><div class="fr-sub">ELO '+user.elo+'</div></div><button class="modal-send" onclick="S.sendReq(\''+user.uid+'\')">Send Request</button></div>';
},

async sendReq(targetUid){
  const myDoc=await fbDb.collection('users').doc(fbUser.uid).get();
  const myUsername=myDoc.exists?myDoc.data().username:'unknown';
  try{
    await sendFriendRequest(targetUid,myUsername);
    const btn=document.querySelector('.modal-send');
    if(btn){btn.textContent='Sent!';btn.disabled=true;}
  }catch(e){
    const btn=document.querySelector('.modal-send');
    if(btn){btn.textContent=e.message;btn.disabled=true;}
  }
},

async viewFriend(uid){
  const doc=await fbDb.collection('users').doc(uid).get();
  if(!doc.exists)return;
  const d=doc.data();
  let activeLang='sr',maxXp=0;
  if(d.langs){for(const[lang,data]of Object.entries(d.langs)){if(data.xp>maxXp){maxXp=data.xp;activeLang=lang;}}}
  const ld=d.langs&&d.langs[activeLang]?d.langs[activeLang]:{};
  const flags={sr:'rs',it:'it'};
  const flagCode=flags[activeLang]||'rs';
  const b=document.getElementById('lbody')||document.getElementById('prof');
  // Show as modal
  const bg=document.createElement('div');bg.className='modal-bg';bg.id='fp-modal';
  bg.onclick=e=>{if(e.target===bg)bg.remove();};
  const wl=Object.keys(ld.ws||{}).filter(k=>(ld.ws||{})[k].c>0).length;
  bg.innerHTML='<div class="modal-box"><button class="fp-back" onclick="document.getElementById(\'fp-modal\').remove()">← Back</button><div class="ptop"><div class="pav"><img src="icon-192.png" style="width:60px;height:60px;border-radius:16px"></div><div class="pnm">@'+(d.username||'unknown')+'</div><div class="pjn"><img src="https://flagcdn.com/w20/'+flagCode+'.png" style="height:12px;vertical-align:-1px"> '+LANG_DATA[activeLang].name+'</div><div class="pelo">'+(ld.elo||1000)+'</div><div class="pelbl">ELO Rating</div></div><div class="psg"><div class="psc"><div class="psc-i">🔥</div><div class="psc-v">'+(ld.streak||0)+'</div><div class="psc-l">Streak</div></div><div class="psc"><div class="psc-i">⚡</div><div class="psc-v">'+(ld.xp||0)+'</div><div class="psc-l">Total XP</div></div><div class="psc"><div class="psc-i">📚</div><div class="psc-v">'+((ld.completed||[]).length)+'</div><div class="psc-l">Lessons</div></div><div class="psc"><div class="psc-i">🏆</div><div class="psc-v">'+wl+'</div><div class="psc-l">Words</div></div></div></div>';
  document.body.appendChild(bg);
},
```

**Step 2: Commit**

```bash
git add index.html
git commit -m "feat: implement profile UI with username setup, friends list, add friend modal, friend view"
```

---

### Task 6: Update Firestore Security Rules & Test End-to-End

**Step 1: Update Firestore rules** (Firebase Console — see Task 1)

**Step 2: Test username creation**
- Sign in on zeka.one
- Go to Profile tab
- Set a username
- Verify it shows `@username` and a friend code

**Step 3: Test friend code copy**
- Tap the friend code badge
- Verify clipboard copy works

**Step 4: Test add friend modal**
- Tap "+ Add Friend"
- Test both Search and Friend Code tabs
- Send a request

**Step 5: Bump cache and push**

```bash
# Update sw.js cache version
# git add and push all changes
```

---

### Task 7: Final Commit & Push

**Step 1: Bump service worker cache**

In `sw.js` line 1, increment the cache version.

**Step 2: Final commit and push**

```bash
git add index.html sw.js
git commit -m "feat: usernames & friends system — profiles, friend codes, requests, friend viewing"
git push
```
