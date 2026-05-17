"""
sync_audio.py — Generate TTS audio for every Serbian/Italian word in
index.html using Microsoft Edge's neural TTS voices.

Why Edge TTS: significantly better Serbian quality than Google Translate
TTS (which Lingva proxies). sr-RS-NicholasNeural is a real neural voice
that sounds like a native Serbian speaker, not "an American reading
Serbian." Italian uses it-IT-DiegoNeural.

Free, no API key required. Uses Microsoft's public Edge TTS endpoint.

INSTALL once:
    pip install edge-tts

USAGE:
    python sync_audio.py            # both languages, missing only
    python sync_audio.py --sr       # Serbian only
    python sync_audio.py --it       # Italian only
    python sync_audio.py --regen    # regenerate ALL files (overwrite existing)
    python sync_audio.py --check    # list missing, don't download

Pre-commit hook (.githooks/pre-commit) runs this automatically when
index.html is staged, so new words/sentences/verbs always get audio.

If you ever want to fall back to Lingva (the previous provider),
the old script is at sync_audio_lingva.py.
"""
import asyncio, re, os, sys, urllib.parse

sys.stdout.reconfigure(encoding='utf-8')

try:
    import edge_tts
except ImportError:
    print('ERROR: edge-tts not installed. Run: pip install edge-tts', file=sys.stderr)
    sys.exit(1)

HTML_FILE = 'index.html'
VOICES = {
    'sr': 'sr-RS-NicholasNeural',
    'it': 'it-IT-DiegoNeural',
}
RATE = '-5%'      # slightly slower than native — better for learners
CONCURRENCY = 1   # serial — edge-tts has shown text/audio swaps under concurrent requests


def _section(html, lang):
    """Slice index.html into the per-language chunk."""
    if lang == 'sr':
        start = html.find('const U_SR=')
        end = html.find('const U_IT=')
        chunk = html[start:end] if start >= 0 and end > start else ''
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
    for m in re.finditer(r'\["[^"]*","([^"]+)","[^"]*","[^"]*"\]', section):
        texts.add(m.group(1))
    for block in re.finditer(r'p:\[(.*?)\]\}', section, re.DOTALL):
        for pm in re.finditer(r'\["([^"]+)","[^"]+"\]', block.group(1)):
            texts.add(pm.group(1))
    if lang == 'sr':
        for m in re.finditer(r"inf:'([^']+)'", section):
            texts.add(m.group(1))
        for m in re.finditer(r"conj:\{([^}]+)\}", section):
            for cm in re.finditer(r"\w+:'([^']+)'", m.group(1)):
                texts.add(cm.group(1))
        for m in re.finditer(r"\bnom:'([^']+)'", section):
            texts.add(m.group(1))
        for m in re.finditer(r"cases:\{([^}]+)\}", section):
            for cm in re.finditer(r"\w+:'([^']+)'", m.group(1)):
                texts.add(cm.group(1))
        for m in re.finditer(r"\bsr:'((?:[^'\\]|\\.)+)'", section):
            texts.add(m.group(1).replace("\\'", "'"))
        for m in re.finditer(r",a:'([^']+)',hint:", section):
            texts.add(m.group(1))
    return sorted(t.strip() for t in texts if t and t.strip())


def safe_filename(text):
    # MUST match JavaScript's encodeURIComponent exactly. JS leaves these
    # unencoded but Python's quote(safe='') encodes them, causing 404s:
    #   !  '  (  )  *
    return urllib.parse.quote(text, safe="!'()*")


def missing_files(texts, out_dir, regen=False):
    if regen:
        return list(texts)
    todo = []
    for t in texts:
        fpath = os.path.join(out_dir, safe_filename(t) + '.mp3')
        if not (os.path.exists(fpath) and os.path.getsize(fpath) > 100):
            todo.append(t)
    return todo


async def synth_one(text, lang, out_dir, sem):
    fpath = os.path.join(out_dir, safe_filename(text) + '.mp3')
    voice = VOICES[lang]
    async with sem:
        for attempt in range(3):
            try:
                communicate = edge_tts.Communicate(text, voice, rate=RATE)
                await communicate.save(fpath)
                if os.path.getsize(fpath) > 100:
                    return ('ok', text)
            except Exception as e:
                if attempt == 2:
                    return ('fail', text, str(e))
                await asyncio.sleep(1.0 * (attempt + 1))
    return ('fail', text, 'all retries failed')


async def sync_lang(lang, regen=False, check_only=False):
    out_dir = os.path.join('audio', lang)
    os.makedirs(out_dir, exist_ok=True)
    print(f'\n=== {lang.upper()} (voice: {VOICES[lang]}) ===')
    texts = extract_texts(lang)
    todo = missing_files(texts, out_dir, regen)
    label = 'Regenerating' if regen else 'Missing'
    print(f'Total strings: {len(texts)}  |  Cached: {len(texts) - len(todo)}  |  {label}: {len(todo)}')

    if not todo:
        return 0, 0
    if check_only:
        for t in todo[:50]:
            print(f'  - {t}')
        if len(todo) > 50:
            print(f'  ... and {len(todo)-50} more')
        return len(todo), 0

    sem = asyncio.Semaphore(CONCURRENCY)
    tasks = [synth_one(t, lang, out_dir, sem) for t in todo]
    done = 0
    failed = []
    for i, fut in enumerate(asyncio.as_completed(tasks), 1):
        result = await fut
        if result[0] == 'ok':
            done += 1
            if done % 25 == 0 or done == len(todo):
                print(f'  [{done}/{len(todo)}] synthesizing...')
        else:
            failed.append(result)
    if failed:
        print(f'  FAILED ({len(failed)}):')
        for r in failed[:10]:
            print(f'    [{r[2]}] {r[1]}')
    print(f'  Done. Generated: {done}, failed: {len(failed)}')
    return done, len(failed)


def main():
    args = sys.argv[1:]
    check_only = '--check' in args
    regen = '--regen' in args
    if '--sr' in args:
        langs = ['sr']
    elif '--it' in args:
        langs = ['it']
    else:
        langs = ['sr', 'it']
    if not os.path.exists(HTML_FILE):
        print(f'ERROR: {HTML_FILE} not found. Run from project root.', file=sys.stderr)
        sys.exit(1)
    total_added = 0
    total_failed = 0
    for lang in langs:
        added, failed = asyncio.run(sync_lang(lang, regen=regen, check_only=check_only))
        total_added += added
        total_failed += failed
    if check_only:
        print(f'\nCheck complete. Missing total: {total_added}')
        sys.exit(1 if total_added > 0 else 0)
    print(f'\nAll done. Generated: {total_added}, failed: {total_failed}')
    sys.exit(0 if total_failed == 0 else 2)


if __name__ == '__main__':
    main()
