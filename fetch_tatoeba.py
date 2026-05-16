"""
fetch_tatoeba.py — Pull Serbian sentences with English translations from
the Tatoeba corpus, filter to drill-suitable candidates, and emit a JS
array ready to paste into index.html (the SENT_SR block).

USAGE
-----
1. First time: download the Tatoeba sentence + links dumps:

     curl -O https://downloads.tatoeba.org/exports/sentences.tar.bz2
     curl -O https://downloads.tatoeba.org/exports/links.tar.bz2
     tar xjf sentences.tar.bz2
     tar xjf links.tar.bz2

   These are large (~1 GB combined). Place them in this directory.

2. Run:

     python fetch_tatoeba.py [--max N] [--min-words N] [--max-words N]

   Default: filters to 4-10 words per sentence, takes 200 best by
   heuristic (short, common vocab, ends with period).

3. Copy the printed JS array and paste over the existing SENT_SR block
   in index.html. Pre-existing IDs are preserved if you keep the first
   seed entries.

WHY A SCRIPT INSTEAD OF AUTO-FETCH
-----------------------------------
Tatoeba's dumps are too large to download + parse on every commit, and
the content needs a human pass (quality control, blank selection,
focus tagging). This script gets you to a curated list quickly.
"""
import sys, csv, os, json, argparse, re
from collections import defaultdict

SENTENCES_FILE = 'sentences.csv'
LINKS_FILE = 'links.csv'

# Common Serbian function words to skip when choosing a "blank" candidate
SKIP_BLANK = set('ja ti on ona ono mi vi oni one ovo to ono u na za o sa s i ili a ali ne da li'.split())


def parse_sentences():
    """Load all sentences indexed by id."""
    rows = {}
    with open(SENTENCES_FILE, 'r', encoding='utf-8') as f:
        for row in csv.reader(f, delimiter='\t'):
            if len(row) < 3:
                continue
            sid, lang, text = row[0], row[1], row[2]
            if lang in ('srp', 'eng'):
                rows[sid] = {'lang': lang, 'text': text}
    return rows


def parse_links():
    """Load translation links (id1, id2)."""
    pairs = []
    with open(LINKS_FILE, 'r', encoding='utf-8') as f:
        for row in csv.reader(f, delimiter='\t'):
            if len(row) < 2:
                continue
            pairs.append((row[0], row[1]))
    return pairs


def pair_sentences(rows, links):
    """Return list of (serbian, english) tuples."""
    pairs = []
    seen = set()
    for a, b in links:
        if a in rows and b in rows:
            ra, rb = rows[a], rows[b]
            if ra['lang'] == 'srp' and rb['lang'] == 'eng':
                key = ra['text']
                if key not in seen:
                    pairs.append((ra['text'], rb['text']))
                    seen.add(key)
            elif ra['lang'] == 'eng' and rb['lang'] == 'srp':
                key = rb['text']
                if key not in seen:
                    pairs.append((rb['text'], ra['text']))
                    seen.add(key)
    return pairs


def estimate_level(sr_text, en_text):
    """Crude CEFR estimate from word count."""
    n = len(sr_text.split())
    if n <= 4:
        return 'A1'
    if n <= 6:
        return 'A2'
    if n <= 9:
        return 'B1'
    if n <= 12:
        return 'B2'
    return 'C1'


def choose_blank(sr_text):
    """Pick a meaningful word to blank — prefer longer, content words."""
    tokens = [t.strip('.,!?;:') for t in sr_text.split()]
    candidates = [t for t in tokens if t and t.lower() not in SKIP_BLANK and len(t) >= 4]
    if not candidates:
        candidates = [t for t in tokens if t and len(t) >= 3]
    if not candidates:
        return tokens[-1] if tokens else None
    # Prefer the longest candidate (typically the noun/verb)
    return max(candidates, key=len)


def filter_pair(sr, en, min_words, max_words):
    n = len(sr.split())
    if n < min_words or n > max_words:
        return False
    # Skip sentences with quotation marks (often dialogue, hard to drill)
    if any(ch in sr for ch in '"“”'):
        return False
    # Skip sentences without a final period (often incomplete)
    if not sr.rstrip().endswith(('.', '!', '?')):
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--max', type=int, default=200, help='Max sentences to emit')
    ap.add_argument('--min-words', type=int, default=4)
    ap.add_argument('--max-words', type=int, default=10)
    ap.add_argument('--start-id', type=int, default=100, help='First ID for generated sentences (keeps seed IDs intact)')
    args = ap.parse_args()

    if not os.path.exists(SENTENCES_FILE):
        print(f'ERROR: {SENTENCES_FILE} not found. See header comment for download instructions.', file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(LINKS_FILE):
        print(f'ERROR: {LINKS_FILE} not found.', file=sys.stderr)
        sys.exit(1)

    print('Parsing sentences...', file=sys.stderr)
    rows = parse_sentences()
    print(f'Loaded {len(rows)} SR/EN sentences.', file=sys.stderr)

    print('Parsing links...', file=sys.stderr)
    links = parse_links()
    print(f'Loaded {len(links)} translation links.', file=sys.stderr)

    print('Pairing...', file=sys.stderr)
    pairs = pair_sentences(rows, links)
    print(f'Found {len(pairs)} SR/EN pairs.', file=sys.stderr)

    # Filter
    filtered = [(sr, en) for sr, en in pairs if filter_pair(sr, en, args.min_words, args.max_words)]
    print(f'After filtering: {len(filtered)} candidates.', file=sys.stderr)

    # Group by estimated level and take a spread
    by_lv = defaultdict(list)
    for sr, en in filtered:
        by_lv[estimate_level(sr, en)].append((sr, en))

    # Take roughly equal counts per level, up to max
    levels = ['A1', 'A2', 'B1', 'B2', 'C1']
    per_lv = max(1, args.max // len(levels))
    chosen = []
    for lv in levels:
        pool = by_lv.get(lv, [])
        # Prefer shorter within level
        pool.sort(key=lambda p: len(p[0]))
        chosen.extend([(sr, en, lv) for sr, en in pool[:per_lv]])
    chosen = chosen[:args.max]

    # Emit as JS array
    print('// === Generated sentences from Tatoeba — review before merging ===', file=sys.stderr)
    print(f'// {len(chosen)} sentences selected from {len(filtered)} candidates', file=sys.stderr)
    print()
    cur_id = args.start_id
    for sr, en, lv in chosen:
        blank = choose_blank(sr)
        if not blank:
            continue
        sr_esc = sr.replace("'", "\\'")
        en_esc = en.replace("'", "\\'")
        blank_esc = blank.replace("'", "\\'")
        print(f"{{id:{cur_id},sr:'{sr_esc}',en:'{en_esc}',lv:'{lv}',focus:'tatoeba',blanks:['{blank_esc}']}},")
        cur_id += 1


if __name__ == '__main__':
    main()
