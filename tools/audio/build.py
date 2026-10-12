"""Zeka listening audio: generate, check, review, publish.

    python tools/audio/build.py trial
        A/B comparison of the old method (Latin text) and the new one (Cyrillic
        text) on ~20 items, using Microsoft's free Edge voices. Local only, for
        listening — nothing from here ships. Opens as tools/audio/trial/index.html.

    python tools/audio/build.py generate --engine azure [--verify] [--kinds word,sentence] [--levels A1,A2] [--limit N]
        Synthesise every item from extract.js into tools/audio/staging/clips/.
        Resumable: existing clips are skipped. --engine azure needs the env vars
        AZURE_SPEECH_KEY and AZURE_SPEECH_REGION (a Microsoft Azure "Speech"
        resource; its output is licensed for use in apps). --verify sends each
        clip back through Azure speech-to-text and flags any whose transcript
        doesn't match the text, so a person only has to listen to those plus a
        sample. --engine edge uses the free Edge endpoint (no account, not
        licensed for commercial use — fine for local testing only).

    python tools/audio/build.py review
        (Re)write tools/audio/staging/review.html: play each clip, mark it OK or
        flag it, then download your decisions as zeka-audio-review.json.

    python tools/audio/build.py publish path/to/zeka-audio-review.json
        Copy approved clips into voice/sr/ and merge them into voice/manifest.json,
        which is what the app reads. Flagged clips are removed from the manifest.
        Only approved clips are ever published.
"""
import argparse, asyncio, hashlib, html, json, os, random, re, shutil, subprocess, sys, time, unicodedata
import urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path(__file__).resolve().parent
STAGING = TOOLS / 'staging'
CLIPS = STAGING / 'clips'
TRIAL = TOOLS / 'trial'
VOICE_DIR = ROOT / 'voice'

VOICE = 'sr-RS-SophieNeural'
RATE = {'word': '-10%', 'sentence': '-5%', 'slow': '-35%'}

# ─── text helpers ──────────────────────────────────────────────────────────────
C2L = {'љ': 'lj', 'њ': 'nj', 'џ': 'dž', 'а': 'a', 'б': 'b', 'ц': 'c', 'ч': 'č', 'ћ': 'ć', 'д': 'd', 'ђ': 'đ', 'е': 'e', 'ф': 'f',
       'г': 'g', 'х': 'h', 'и': 'i', 'ј': 'j', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's',
       'ш': 'š', 'т': 't', 'у': 'u', 'в': 'v', 'з': 'z', 'ж': 'ž'}


def fold(text):
    """Lowercase Latin, no diacritics, no punctuation — for comparing a transcript with the source."""
    t = ''.join(C2L.get(ch, ch) for ch in text.lower())
    t = t.replace('đ', 'd').replace('dž', 'dz')
    t = unicodedata.normalize('NFD', t)
    t = ''.join(ch for ch in t if unicodedata.category(ch) != 'Mn')
    t = re.sub(r'[^a-z\s]', ' ', t)
    return t.split()


def wer(ref, hyp):
    """Word error rate between two token lists (edit distance / reference length)."""
    if not ref:
        return 0.0 if not hyp else 1.0
    d = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        prev, d[0] = d[0], i
        for j, h in enumerate(hyp, 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (r != h))
            prev, d[j] = d[j], cur
    return d[len(hyp)] / len(ref)


def clip_id(engine, voice, rate, text):
    return hashlib.sha1(f'{engine}|{voice}|{rate}|{text}'.encode('utf-8')).hexdigest()[:16]


def load_items():
    out = subprocess.run(['node', str(TOOLS / 'extract.js')], capture_output=True, text=True, encoding='utf-8', check=True)
    sys.stderr.write(out.stderr)
    return json.loads(out.stdout)


def ssml(text, voice, rate):
    # Leading/trailing silence is trimmed to 80 ms so a tap plays the word at once
    # (untrimmed clips carry over a second of dead air around a short word).
    lang = '-'.join(voice.split('-')[:2])
    return ('<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="%s">'
            '<voice name="%s"><mstts:silence type="Leading-exact" value="80ms"/><mstts:silence type="Tailing-exact" value="80ms"/>'
            '<prosody rate="%s">%s</prosody></voice></speak>') % (lang, voice, rate, html.escape(text))


# ─── engines ───────────────────────────────────────────────────────────────────
class Azure:
    name = 'azure'

    def __init__(self):
        self.key = os.environ.get('AZURE_SPEECH_KEY')
        self.region = os.environ.get('AZURE_SPEECH_REGION')
        if not self.key or not self.region:
            sys.exit('Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION (from your Azure Speech resource) first.')

    def _post(self, url, body, headers, tries=6):
        for attempt in range(tries):
            req = urllib.request.Request(url, data=body, headers={'Ocp-Apim-Subscription-Key': self.key, 'User-Agent': 'zeka-audio', **headers})
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    return r.read()
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503) and attempt < tries - 1:
                    wait = float(e.headers.get('Retry-After') or 0) or min(60, 2 ** attempt * 3)
                    time.sleep(wait)
                    continue
                raise RuntimeError(f'HTTP {e.code}: {e.read()[:200]!r}')
        raise RuntimeError('gave up after retries')

    def tts(self, text, voice, rate, fmt='audio-24khz-48kbitrate-mono-mp3'):
        url = f'https://{self.region}.tts.speech.microsoft.com/cognitiveservices/v1'
        return self._post(url, ssml(text, voice, rate).encode('utf-8'),
                          {'Content-Type': 'application/ssml+xml', 'X-Microsoft-OutputFormat': fmt})

    def stt(self, wav, lang='sr-RS'):
        url = (f'https://{self.region}.stt.speech.microsoft.com/speech/recognition/conversation/'
               f'cognitiveservices/v1?language={lang}&format=simple')
        res = json.loads(self._post(url, wav, {'Content-Type': 'audio/wav; codecs=audio/pcm; samplerate=16000', 'Accept': 'application/json'}))
        return res.get('DisplayText', '') if res.get('RecognitionStatus') == 'Success' else ''


class Edge:
    name = 'edge'

    def __init__(self):
        try:
            import edge_tts  # noqa: F401
        except ImportError:
            sys.exit('pip install edge-tts   (only needed for --engine edge and the trial)')

    def tts(self, text, voice, rate):
        import edge_tts

        async def run():
            buf = bytearray()
            async for chunk in edge_tts.Communicate(text, voice, rate=rate).stream():
                if chunk['type'] == 'audio':
                    buf.extend(chunk['data'])
            return bytes(buf)
        for attempt in range(4):
            try:
                data = asyncio.run(run())
                if data:
                    return data
            except Exception:
                if attempt == 3:
                    raise
            time.sleep(2 * (attempt + 1))
        raise RuntimeError('empty audio')


# ─── generate ──────────────────────────────────────────────────────────────────
def cmd_generate(a):
    eng = Azure() if a.engine == 'azure' else Edge()
    if a.verify and eng.name != 'azure':
        sys.exit('--verify needs --engine azure (it uses Azure speech-to-text).')
    items = load_items()
    kinds = set(a.kinds.split(','))
    levels = set(a.levels.split(',')) if a.levels else None
    items = [x for x in items if x['kind'] in kinds and (not levels or x['lv'] in levels or not x['lv'])]
    if a.limit:
        items = items[:a.limit]
    CLIPS.mkdir(parents=True, exist_ok=True)
    results_path = STAGING / 'results.json'
    results = json.loads(results_path.read_text('utf-8')) if results_path.exists() else {}
    done = 0
    verify = a.verify
    tts_fail_run = stt_fail_run = 0
    started = time.time()
    print(f'{len(items)} item(s) to voice with {VOICE} ({eng.name}){" + speech-to-text check" if verify else ""}', file=sys.stderr)
    for n, it in enumerate(items, 1):
        rate = RATE[it['kind']]
        f = clip_id(eng.name, VOICE, rate, it['cyr'])
        rec = results.get(it['key'], {})
        if rec.get('f') == f and (CLIPS / f'{f}.mp3').exists() and (not verify or 'stt' in rec or 'stt_error' in rec):
            continue
        try:
            mp3 = CLIPS / f'{f}.mp3'
            if not mp3.exists():
                mp3.write_bytes(eng.tts(it['cyr'], VOICE, rate))
            rec = {**it, 'f': f, 'engine': eng.name, 'voice': VOICE}
            if it['kind'] == 'sentence':
                s = clip_id(eng.name, VOICE, RATE['slow'], it['cyr'])
                if not (CLIPS / f'{s}.mp3').exists():
                    (CLIPS / f'{s}.mp3').write_bytes(eng.tts(it['cyr'], VOICE, RATE['slow']))
                rec['s'] = s
            tts_fail_run = 0
        except Exception as e:
            results[it['key']] = {**it, 'error': str(e)[:200]}
            print(f'  ! {it["latin"]}: {e}', file=sys.stderr)
            tts_fail_run += 1
            if tts_fail_run >= 5:
                results_path.write_text(json.dumps(results, ensure_ascii=False, indent=1), 'utf-8')
                sys.exit('Stopped: 5 clips in a row failed. Check AZURE_SPEECH_KEY and AZURE_SPEECH_REGION '
                         '(the region is the short name shown under Keys and Endpoint, e.g. westeurope), then run the same command again — it resumes.')
            continue
        if verify:
            # The check is a safety net, not a gate: if it fails, the clip is kept and simply marked for listening.
            try:
                wav = eng.tts(it['cyr'], VOICE, rate, fmt='riff-16khz-16bit-mono-pcm')
                heard = eng.stt(wav)
                score = wer(fold(it['latin']), fold(heard))
                limit = 0.0 if it['kind'] == 'word' else 0.2
                rec.update(stt=heard, wer=round(score, 3), status='pass' if heard and score <= limit else 'check')
                stt_fail_run = 0
            except Exception as e:
                rec.update(stt_error=str(e)[:200], status='check')
                stt_fail_run += 1
                if stt_fail_run >= 5:
                    verify = False
                    print('  ! speech-to-text check failed 5 times in a row; continuing without it '
                          '(remaining clips will all be marked for listening). Error: ' + str(e)[:160], file=sys.stderr)
        results[it['key']] = rec
        done += 1
        if n % 25 == 0:
            results_path.write_text(json.dumps(results, ensure_ascii=False, indent=1), 'utf-8')
            el = time.time() - started
            eta = el / max(done, 1) * (len(items) - n)
            print(f'  {n}/{len(items)}  ·  about {int(eta // 60)} min left', file=sys.stderr)
    results_path.write_text(json.dumps(results, ensure_ascii=False, indent=1), 'utf-8')
    errors = sum(1 for r in results.values() if 'error' in r)
    checks = sum(1 for r in results.values() if r.get('status') == 'check')
    print(f'generated {done} new clip(s); {len(results)} items in staging; {checks} flagged by the automatic check; {errors} error(s)')
    write_review(results)


# ─── review page ───────────────────────────────────────────────────────────────
def write_review(results=None):
    if results is None:
        results = json.loads((STAGING / 'results.json').read_text('utf-8'))
    rows = [r for r in results.values() if r.get('f') and 'error' not in r]
    rows.sort(key=lambda r: ({'check': 0}.get(r.get('status'), 1), r['kind'] != 'word', r.get('lv') or 'Z', r['latin'].lower()))
    page = (TOOLS / 'review_template.html').read_text('utf-8').replace('/*__ROWS__*/[]', json.dumps(rows, ensure_ascii=False))
    (STAGING / 'review.html').write_text(page, 'utf-8')
    print(f'review page: {STAGING / "review.html"}  ({len(rows)} clips)')


def cmd_review(a):
    write_review()


# ─── publish ───────────────────────────────────────────────────────────────────
def cmd_publish(a):
    decisions = json.loads(Path(a.review).read_text('utf-8'))
    approved, flagged = set(decisions.get('approved', [])), {x['f'] for x in decisions.get('flagged', [])}
    results = json.loads((STAGING / 'results.json').read_text('utf-8'))
    out_dir = VOICE_DIR / 'sr'
    out_dir.mkdir(parents=True, exist_ok=True)
    man_path = VOICE_DIR / 'manifest.json'
    manifest = json.loads(man_path.read_text('utf-8')) if man_path.exists() else {'v': 1, 'clips': {}}
    added = removed = 0
    for key, r in results.items():
        f = r.get('f')
        if not f:
            continue
        if f in flagged and key in manifest['clips']:
            del manifest['clips'][key]; removed += 1
        if f not in approved:
            continue
        entry = {'f': f'sr/{f}.mp3'}
        shutil.copy2(CLIPS / f'{f}.mp3', out_dir / f'{f}.mp3')
        if r.get('s') and (CLIPS / f'{r["s"]}.mp3').exists():
            shutil.copy2(CLIPS / f'{r["s"]}.mp3', out_dir / f'{r["s"]}.mp3')
            entry['s'] = f'sr/{r["s"]}.mp3'
        manifest['clips'][key] = entry
        added += 1
    manifest.update(v=1, voice=VOICE, updated=time.strftime('%Y-%m-%d'))
    man_path.write_text(json.dumps(manifest, ensure_ascii=False, separators=(',', ':')), 'utf-8')
    # drop clip files nothing points at any more
    live = {Path(e[k]).name for e in manifest['clips'].values() for k in ('f', 's') if k in e}
    for p in out_dir.glob('*.mp3'):
        if p.name not in live:
            p.unlink()
    print(f'published {added} clip(s), removed {removed}; manifest now has {len(manifest["clips"])} entries')


# ─── trial: old method vs new, by ear ──────────────────────────────────────────
TRIAL_KEYS = ['zdravo', 'hvala', 'da', 'ne', 'dobar dan', 'doviđenja', 'knjiga', 'kuća', 'ključ', 'čaša', 'džepu', 'đak', 'ljubav',
              'inženjer', 'budžet', 'dobro jutro', 'kako si?']
TRIAL_SENTENCES = ['pitala sam te sinoć.', 'ne znam da li ću stići. videćemo.', 'idem u školu.', 'gde ste bili juče?',
                   'zovem se marko i živim u beogradu.', 'kad ćeš doći?']


def cmd_trial(a):
    eng = Edge()
    items = {x['key']: x for x in load_items()}
    picks = [items[k] for k in TRIAL_KEYS + TRIAL_SENTENCES if k in items]
    if len(picks) < 10:
        picks += random.sample([x for x in items.values() if x['kind'] == 'word'], 10)
    TRIAL.mkdir(parents=True, exist_ok=True)
    variants = [
        ('before', 'Before (May): male voice, Latin text', 'sr-RS-NicholasNeural', 'latin', '-5%'),
        ('sophie', 'New: female voice, Cyrillic text', 'sr-RS-SophieNeural', 'cyr', None),
        ('nicholas', 'New: male voice, Cyrillic text', 'sr-RS-NicholasNeural', 'cyr', None),
        ('slow', 'New, slow (sentences)', 'sr-RS-SophieNeural', 'cyr', RATE['slow']),
    ]
    rows = []
    for it in picks:
        row = {'latin': it['latin'], 'cyr': it['cyr'], 'en': it['en'], 'kind': it['kind'], 'clips': {}}
        for vid, _, voice, field, rate in variants:
            if vid == 'slow' and it['kind'] != 'sentence':
                continue
            rate = rate or RATE[it['kind']]
            f = f"{vid}-{clip_id('edge', voice, rate, it[field])}.mp3"
            if not (TRIAL / f).exists():
                (TRIAL / f).write_bytes(eng.tts(it[field], voice, rate))
            row['clips'][vid] = f
        rows.append(row)
        print(f'  {it["latin"]}', file=sys.stderr)
    page = (TOOLS / 'trial_template.html').read_text('utf-8')
    page = page.replace('/*__ROWS__*/[]', json.dumps(rows, ensure_ascii=False)).replace(
        '/*__VARIANTS__*/[]', json.dumps([{'id': v[0], 'label': v[1]} for v in variants], ensure_ascii=False))
    (TRIAL / 'index.html').write_text(page, 'utf-8')
    print(f'trial page: {TRIAL / "index.html"}  ({len(rows)} items)')


def main():
    for stream in (sys.stdout, sys.stderr):  # Serbian text in the Windows console
        try:
            stream.reconfigure(encoding='utf-8')
        except Exception:
            pass
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)
    g = sub.add_parser('generate')
    g.add_argument('--engine', choices=['azure', 'edge'], default='azure')
    g.add_argument('--verify', action='store_true')
    g.add_argument('--kinds', default='word,sentence')
    g.add_argument('--levels', default='')
    g.add_argument('--limit', type=int, default=0)
    g.set_defaults(fn=cmd_generate)
    sub.add_parser('review').set_defaults(fn=cmd_review)
    pb = sub.add_parser('publish')
    pb.add_argument('review')
    pb.set_defaults(fn=cmd_publish)
    sub.add_parser('trial').set_defaults(fn=cmd_trial)
    a = p.parse_args()
    a.fn(a)


if __name__ == '__main__':
    main()
