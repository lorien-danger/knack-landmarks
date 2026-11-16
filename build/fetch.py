"""
Download what this dataset is made from into build/sources/, so build.py works from fixed copies (and anyone can see
exactly what it read). Run it again to take newer versions; the date is written to sources/FETCHED.

  python3 fetch.py

For each landmark in landmarks.tsv (its English Wikipedia article):
- wikidata.json: its Wikidata item (CC0), cut down to the statements used: country (P17), coordinates (P625),
  instance of (P31), continent (P30), inception (P571), date of official opening (P1619), start and end time (P580,
  P582), service entry (P729), image (P18), with the English labels of the items they point at.
- infobox.json: the infobox at the top of the Wikipedia article (wikitext, CC BY-SA 4.0), read by hand for the year
  a building was finished, and the article's revision id.
"""
import csv, json, re, sys, time, datetime, urllib.parse, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'sources'
UA = {'User-Agent': 'knack-landmarks-build/1.0 (https://github.com/lorien-danger/knack-landmarks)'}
PROPS = ['P17', 'P625', 'P31', 'P30', 'P571', 'P1619', 'P580', 'P582', 'P729', 'P18']

def get(url):
    for k in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r: return r.read()
        except Exception as e:
            print('  retry:', e, file=sys.stderr); time.sleep(5 * (k + 1))
    raise RuntimeError(url)

def api(base, **q):
    return json.loads(get(base + '?' + urllib.parse.urlencode({**q, 'format': 'json', 'formatversion': 2})))

def value(snak):
    if snak.get('snaktype') != 'value': return None
    v = snak['datavalue']['value']
    t = snak['datavalue']['type']
    if t == 'wikibase-entityid': return v['id']
    if t == 'globecoordinate': return [v['latitude'], v['longitude']]
    if t == 'time': return {'time': v['time'], 'precision': v['precision']}
    return v

def infobox(text):
    """the first {{Infobox ...}} template, by matching braces"""
    m = re.search(r'\{\{\s*Infobox', text, re.I)
    if not m: return ''
    depth, i = 0, m.start()
    while i < len(text):
        if text.startswith('{{', i): depth += 1; i += 2; continue
        if text.startswith('}}', i):
            depth -= 1; i += 2
            if depth == 0: return text[m.start():i]
            continue
        i += 1
    return text[m.start():]

if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    titles = [r['wikipedia'] for r in csv.DictReader(open(HERE / 'landmarks.tsv'), delimiter='\t')]
    wd, ib, labels_needed = {}, {}, set()
    for k in range(0, len(titles), 40):
        chunk = titles[k:k + 40]
        j = api('https://en.wikipedia.org/w/api.php', action='query', titles='|'.join(chunk), redirects=1,
                prop='pageprops|revisions', ppprop='wikibase_item', rvprop='ids|content', rvslots='main', rvsection=0)
        norm = {n['from']: n['to'] for n in j['query'].get('normalized', [])}
        redir = {n['from']: n['to'] for n in j['query'].get('redirects', [])}
        pages = {p['title']: p for p in j['query']['pages']}
        for t in chunk:
            p = pages.get(redir.get(norm.get(t, t), norm.get(t, t)))
            if not p or 'missing' in p: print('MISSING', t, file=sys.stderr); continue
            rev = p['revisions'][0]
            ib[t] = {'article': p['title'], 'revid': rev['revid'], 'qid': p['pageprops']['wikibase_item'],
                     'infobox': infobox(rev['slots']['main']['content'])}
        time.sleep(1)
    for t, info in ib.items():
        q = info['qid']
        e = json.loads(get(f'https://www.wikidata.org/wiki/Special:EntityData/{q}.json'))['entities']
        e = next(iter(e.values()))
        claims = {}
        for p in PROPS:
            for c in e.get('claims', {}).get(p, []):
                if c['rank'] == 'deprecated': continue
                v = value(c['mainsnak'])
                if v is None: continue
                quals = {qp: [value(s) for s in qs] for qp, qs in c.get('qualifiers', {}).items() if qp in ('P582', 'P580', 'P518', 'P642', 'P1480', 'P793')}
                claims.setdefault(p, []).append({'v': v, 'rank': c['rank'], **({'q': quals} if quals else {})})
                if isinstance(v, str) and re.fullmatch(r'Q\d+', v): labels_needed.add(v)
        wd[q] = {'label': e['labels'].get('en', {}).get('value'), 'description': e.get('descriptions', {}).get('en', {}).get('value'),
                 'claims': claims}
        print(q, wd[q]['label'], flush=True)
        time.sleep(0.2)
    labels, need = {}, sorted(labels_needed)
    for k in range(0, len(need), 50):
        j = api('https://www.wikidata.org/w/api.php', action='wbgetentities', ids='|'.join(need[k:k + 50]), props='labels', languages='en')
        for q, e in j['entities'].items(): labels[q] = e.get('labels', {}).get('en', {}).get('value')
    json.dump({'items': wd, 'labels': labels}, open(OUT / 'wikidata.json', 'w'), indent=1, ensure_ascii=False)
    json.dump(ib, open(OUT / 'infobox.json', 'w'), indent=1, ensure_ascii=False)
    (OUT / 'FETCHED').write_text(json.dumps({'date': datetime.date.today().isoformat()}) + '\n')
