// Extract everything Zeka can speak from index.html, as Cyrillic text for the voice.
//
//   node tools/audio/extract.js > tools/audio/staging/items.json
//
// Why Cyrillic: Microsoft's sr-RS voices expect Serbian in Cyrillic. The May 2026
// pipeline fed them Latin text, plus bare fragments such as "ćeš" or "psu", and
// the result mispronounced words or read the wrong thing. Here every item is a
// whole word, phrase or sentence, converted letter-for-letter (Serbian Latin and
// Cyrillic map one-to-one; the course has no foreign letters and no split
// digraphs — see EXCEPTIONS if that ever changes).
//
// Output: [{key, latin, cyr, kind, lv, en, src}] — key is the lowercase Latin
// text the app looks clips up by.
const fs = require('fs');
const path = require('path');

const HTML = path.join(__dirname, '..', '..', 'index.html');
const src = fs.readFileSync(HTML, 'utf8').replace(/\r\n/g, '\n');

function grab(name) {
  const i = src.indexOf('\nconst ' + name + '=[');
  if (i < 0) throw new Error('const ' + name + ' not found in index.html');
  const j = src.indexOf('\n];', i);
  return src.slice(i + 1, j + 3);
}
const D = new Function(['U_SR', 'V_SR', 'SENT_SR', 'CLOZE_SR', 'READ_SR'].map(grab).join('\n') +
  '\nreturn {U_SR,V_SR,SENT_SR,CLOZE_SR,READ_SR};')();

// Latin → Cyrillic. Digraphs first. EXCEPTIONS holds words where n+j, l+j or d+ž
// are two letters (e.g. "injekcija" → "инјекција"); none occur in the course today.
const EXCEPTIONS = { injekcija: 'инјекција', konjugacija: 'конјугација', nadživeti: 'надживети', podžupan: 'поджупан' };
const MAP = { lj: 'љ', nj: 'њ', 'dž': 'џ', a: 'а', b: 'б', c: 'ц', 'č': 'ч', 'ć': 'ћ', d: 'д', 'đ': 'ђ', e: 'е', f: 'ф', g: 'г', h: 'х',
  i: 'и', j: 'ј', k: 'к', l: 'л', m: 'м', n: 'н', o: 'о', p: 'п', r: 'р', s: 'с', 'š': 'ш', t: 'т', u: 'у', v: 'в', z: 'з', 'ž': 'ж' };
function word2cyr(w) {
  const low = w.toLowerCase();
  if (EXCEPTIONS[low]) return matchCase(w, EXCEPTIONS[low]);
  let out = '';
  for (let i = 0; i < low.length; i++) {
    const two = low.slice(i, i + 2);
    if (two.length === 2 && MAP[two]) { out += MAP[two]; i++; continue; }
    out += MAP[low[i]] !== undefined ? MAP[low[i]] : low[i];
  }
  return matchCase(w, out);
}
function matchCase(orig, cyr) {
  // Capitalise the first letter if the Latin word was capitalised (names, sentence starts)
  return /^[A-ZČĆŠŽĐ]/.test(orig) ? cyr.charAt(0).toUpperCase() + cyr.slice(1) : cyr;
}
function toCyr(text) { return text.replace(/[A-Za-zČĆŠŽĐčćšžđ]+/g, word2cyr); }

const items = new Map();
function add(latin, kind, lv, en, srcTag, cyrGiven) {
  latin = (latin || '').trim();
  if (!latin) return;
  if (/[qwxyQWXY0-9]/.test(latin)) { console.error('skip (foreign letters/digits): ' + latin); return; }
  const key = latin.toLowerCase();
  if (items.has(key)) return; // first source wins; same text = same clip
  const cyr = cyrGiven ? cyrGiven.trim() : toCyr(latin);
  items.set(key, { key, latin, cyr, kind, lv: lv || '', en: en || '', src: srcTag });
}

// Words: the unit's own Cyrillic is authoritative
D.U_SR.forEach(u => u.w.forEach((w, i) => add(w[1], 'word', u.lv, w[2], 'w' + (u.id * 100 + i), w[0])));
D.V_SR.forEach(v => add(v.inf, 'word', '', v.en, 'v:' + v.inf));
// Sentences
D.U_SR.forEach(u => (u.p || []).forEach((p, i) => add(p[0], 'sentence', u.lv, p[1], 'u' + u.id + 'p' + i)));
D.SENT_SR.forEach(s => add(s.sr, 'sentence', s.lv, s.en, 's' + s.id));
D.CLOZE_SR.forEach(s => add(s.sr, 'sentence', s.lv, s.en, 'g' + s.id));
D.READ_SR.forEach(r => r.s.forEach((x, i) => add(x.sr, 'sentence', r.lv, x.en, 'r' + r.id + '.' + i)));

const out = [...items.values()];
process.stdout.write(JSON.stringify(out, null, 1) + '\n');
const byKind = out.reduce((a, x) => (a[x.kind] = (a[x.kind] || 0) + 1, a), {});
console.error('items: ' + out.length + ' ' + JSON.stringify(byKind) + ' · characters: ' + out.reduce((a, x) => a + x.cyr.length, 0));
