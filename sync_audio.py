"""
sync_audio.py — Download missing TTS audio for all Serbian and Italian words.

Extracts every Serbian/Italian string in index.html that needs audio:
  - Unit words (the second item in word arrays)
  - Phrases (full short phrases)
  - Verb infinitives + every present-tense conjugation form
  - Noun nominatives + every case form (sg)

Downloads missing MP3s only — skips files already on disk. Run any time:

    python sync_audio.py            # both languages
    python sync_audio.py --sr       # Serbian only
    python sync_audio.py --it       # Italian only
    python sync_audio.py --check    # report missing, don't download

Recommended: install the pre-commit hook so new words are auto-fetched
before every commit (see .githooks/pre-commit).
"""
import re, os, sys, json, time, threading, urllib.request, urllib.parse, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding='utf-8')

HTML_FILE = 'index.html'
LINGVA_MIRRORS = [
    'https://lingva.ml',
    'https://translate.plausibility.cloud',
    'https://lingva.lunar.icu',
    'https://lingva.garudalinux.org',
]
MAX_RETRIES = 4
DELAY = 0.8

_mirror_idx = 0
_mirror_lock = threading.Lock()
def next_mirror():
    global _mirror_idx
    with _mirror_lock:
        host = LINGVA_MIRRORS[_mirror_idx % len(LINGVA_MIRRORS)]
        _mirror_idx += 1
        return host


def _section(html, lang):
    """Slice index.html into the per-language chunk."""
    if lang == 'sr':
        # Everything from `const U_SR=` up to (but not including) `const U_IT=`
        start = html.find('const U_SR=')
        end = html.find('const U_IT=')
        chunk = html[start:end] if start >= 0 and end > start else ''
        # Plus the SR-specific data (verbs + nouns + sentences)
        v_start = html.find('const V_SR=')
        v_end = html.find('const N_SR=')
        n_start = html.find('const N_SR=')
        s_start = html.find('const SENT_SR=')
        n_end = s_start if s_start > 0 else html.find('// ═', n_start)
        s_end_search = html.find('\n];', s_start) if s_start > 0 else -1
        s_end = s_end_search + 3 if s_end_search > 0 else len(html)
        if v_start >= 0 and v_end > v_start:
            chunk += '\n' + html[v_start:v_end]
        if n_start >= 0 and n_end > n_start:
            chunk += '\n' + html[n_start:n_end]
        if s_start >= 0 and s_end > s_start:
            chunk += '\n' + html[s_start:s_end]
        return chunk
    if lang == 'it':
        start = html.find('const U_IT=')
        # ends at the LANG_DATA block
        end = html.find('// ═', start) if html.find('// ═', start) > 0 else html.find('const LANG_DATA', start)
        return html[start:end] if start >= 0 and end > start else ''
    return ''


def extract_texts(lang):
    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        html = f.read()
    section = _section(html, lang)
    if not section:
        return []

    texts = set()

    # 1) Unit word arrays: ["s","l","e","em"] — l is index 1
    for m in re.finditer(r'\["[^"]*","([^"]+)","[^"]*","[^"]*"\]', section):
        texts.add(m.group(1))

    # 2) Phrase arrays inside p:[...]
    for block in re.finditer(r'p:\[(.*?)\]\}', section, re.DOTALL):
        for pm in re.finditer(r'\["([^"]+)","[^"]+"\]', block.group(1)):
            texts.add(pm.group(1))

    if lang == 'sr':
        # 3) Verb infinitives: {inf:'biti',...
        for m in re.finditer(r"inf:'([^']+)'", section):
            texts.add(m.group(1))
        # 4) Verb conjugations: conj:{ja:'sam',ti:'si',on:'je',mi:'smo',vi:'ste',oni:'su'}
        for m in re.finditer(r"conj:\{([^}]+)\}", section):
            for cm in re.finditer(r"\w+:'([^']+)'", m.group(1)):
                texts.add(cm.group(1))
        # 5) Noun nominatives: {nom:'čovek',...
        for m in re.finditer(r"\bnom:'([^']+)'", section):
            texts.add(m.group(1))
        # 6) Noun case forms: cases:{nom:'...',gen:'...',...}
        for m in re.finditer(r"cases:\{([^}]+)\}", section):
            for cm in re.finditer(r"\w+:'([^']+)'", m.group(1)):
                texts.add(cm.group(1))
        # 8) Full sentences from SENT_SR: {id:N,sr:'…',en:'…',…}
        for m in re.finditer(r"\bsr:'((?:[^'\\]|\\.)+)'", section):
            texts.add(m.group(1).replace("\\'", "'"))
        # 7) Sentence answer field: a:'školu'
        for m in re.finditer(r",a:'([^']+)',hint:", section):
            texts.add(m.group(1))

    # Drop empties and strip whitespace
    return sorted(t.strip() for t in texts if t and t.strip())


def safe_filename(text):
    return urllib.parse.quote(text, safe='')


def missing_files(texts, out_dir):
    todo = []
    for t in texts:
        fpath = os.path.join(out_dir, safe_filename(t) + '.mp3')
        if not (os.path.exists(fpath) and os.path.getsize(fpath) > 100):
            todo.append(t)
    return todo


def fetch_one(text, lang, out_dir):
    fname = safe_filename(text) + '.mp3'
    fpath = os.path.join(out_dir, fname)
    if os.path.exists(fpath) and os.path.getsize(fpath) > 100:
        return 'skip'
    enc = urllib.parse.quote(text)
    last_err = ''
    for attempt in range(MAX_RETRIES):
        host = next_mirror()
        try:
            url = f'{host}/api/v1/audio/{lang}/{enc}'
            req = urllib.request.Request(url, headers={'User-Agent': 'Zeka-TTS/1.0'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
            if data.get('audio') and len(data['audio']) > 0:
                with open(fpath, 'wb') as f:
                    f.write(bytes(data['audio']))
                return 'ok'
            last_err = 'empty_response'
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(DELAY * (2 ** attempt))
                continue
            last_err = f'http_{e.code}'
        except Exception as e:
            last_err = type(e).__name__
            time.sleep(DELAY)
    return f'failed:{last_err}'


def sync_lang(lang, check_only=False):
    out_dir = os.path.join('audio', lang)
    os.makedirs(out_dir, exist_ok=True)
    print(f'\n=== {lang.upper()} ===')
    texts = extract_texts(lang)
    todo = missing_files(texts, out_dir)
    print(f'Total strings: {len(texts)}  |  Already cached: {len(texts) - len(todo)}  |  Missing: {len(todo)}')

    if not todo:
        return 0, 0
    if check_only:
        print('\nMissing audio for:')
        for t in todo[:50]:
            print(f'  - {t}')
        if len(todo) > 50:
            print(f'  ... and {len(todo)-50} more')
        return len(todo), 0

    done, failed = 0, []
    for i, text in enumerate(todo, 1):
        result = fetch_one(text, lang, out_dir)
        if result == 'ok':
            done += 1
            if done % 10 == 0 or done == len(todo):
                print(f'  [{done}/{len(todo)}] downloading...')
        elif result != 'skip':
            failed.append((text, result))
        time.sleep(DELAY)

    if failed:
        print(f'  FAILED ({len(failed)}):')
        for t, r in failed[:10]:
            print(f'    [{r}] {t}')
    print(f'  Done. Downloaded: {done}, failed: {len(failed)}')
    return done, len(failed)


def main():
    args = sys.argv[1:]
    langs = []
    check_only = '--check' in args
    if '--sr' in args:
        langs = ['sr']
    elif '--it' in args:
        langs = ['it']
    else:
        langs = ['sr', 'it']

    if not os.path.exists(HTML_FILE):
        print(f'ERROR: {HTML_FILE} not found. Run from the project root.')
        sys.exit(1)

    total_added = 0
    total_failed = 0
    for lang in langs:
        added, failed = sync_lang(lang, check_only)
        total_added += added
        total_failed += failed

    if check_only:
        print(f'\nCheck complete. Missing total: {total_added}')
        sys.exit(1 if total_added > 0 else 0)

    print(f'\nAll done. Added: {total_added}, failed: {total_failed}')
    sys.exit(0 if total_failed == 0 else 2)


if __name__ == '__main__':
    main()
