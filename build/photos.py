"""
Fetch the photograph chosen for each landmark (build/photos.tsv) from Wikimedia Commons, scaled to fit 560 x 480
pixels, as media/<id>.jpg, and write who made each and under what licence to media/credits.tsv.

  python3 photos.py          (needs pillow)

Most are the landmark's Wikidata image (P18); where that was taken at night, from an odd angle or showed only a
detail, another photograph on Commons was chosen by eye (photos.tsv says which). Adapted from knack-elements.
"""
import csv, io, json, re, sys, time, html, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image
from build import slug

HERE = Path(__file__).resolve().parent
MEDIA = HERE.parent / 'media'
UA = {'User-Agent': 'knack-landmarks-build/1.0 (https://github.com/lorien-danger/knack-landmarks)'}
BOX = (560, 480)

def get(url):
    for k in range(8):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r: return r.read()
        except Exception as e:
            print('  retry:', e, file=sys.stderr); time.sleep(15 * (k + 1))
    raise RuntimeError(url)

def text(s):
    """Commons metadata is HTML: keep the words"""
    t = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', s or ''))).strip()
    return re.sub(r'(Unknown author)\1', r'\1', t)

def info(name):
    q = urllib.parse.urlencode({'action': 'query', 'titles': 'File:' + name, 'prop': 'imageinfo',
                                'iiprop': 'url|extmetadata|size|user', 'iiurlwidth': BOX[0], 'format': 'json'})
    page = next(iter(json.loads(get('https://commons.wikimedia.org/w/api.php?' + q))['query']['pages'].values()))
    ii = page['imageinfo'][0]
    return ii, {k: v.get('value', '') for k, v in ii.get('extmetadata', {}).items()}

if __name__ == '__main__':
    MEDIA.mkdir(exist_ok=True)
    rows = list(csv.DictReader(open(HERE / 'photos.tsv'), delimiter='\t'))
    only = set(sys.argv[1:])
    old = {r['id']: r for r in csv.DictReader(open(MEDIA / 'credits.tsv'), delimiter='\t')} if (MEDIA / 'credits.tsv').exists() else {}
    credits = {}
    for r in rows:
        i = slug(r['name'])
        if (only and r['name'] not in only) or (not only and i in old and (MEDIA / f'{i}.jpg').exists() and old[i]['commons page'].endswith(urllib.parse.quote(r['file'].replace(' ', '_')))):
            if i in old: credits[i] = old[i]
            continue
        ii, m = info(r['file'])
        w = BOX[0] if ii['width'] / ii['height'] >= BOX[0] / BOX[1] else round(BOX[1] * ii['width'] / ii['height'])
        url = ii['thumburl'].replace(f'/{BOX[0]}px-', f'/{w}px-') if 'thumburl' in ii else ii['url']
        img = Image.open(io.BytesIO(get(url))).convert('RGB')
        img.thumbnail(BOX, Image.LANCZOS)
        img.save(MEDIA / f'{i}.jpg', quality=80, optimize=True, progressive=True)
        lic = text(m.get('LicenseShortName'))
        if not lic or re.search(r'non-?commercial|fair use|all rights', lic, re.I): raise SystemExit(f'{i}: licence {lic!r}')
        credits[i] = {'id': i, 'file': f'media/{i}.jpg', 'commons page': ii['descriptionurl'],
                      'author': text(m.get('Artist')) or text(m.get('Attribution')) or (f"{ii['user']} (uploader; the file page names no other author)" if re.search(r'own work|^$', text(m.get('Credit')), re.I) else text(m.get('Credit'))), 'licence': lic,
                      'licence link': m.get('LicenseUrl', ''), 'description': text(m.get('ImageDescription'))[:300]}
        print(i, img.size, lic, flush=True)
        time.sleep(2)
    with open(MEDIA / 'credits.tsv', 'w', newline='') as f:
        w = csv.DictWriter(f, ['id', 'file', 'commons page', 'author', 'licence', 'licence link', 'description'], delimiter='\t', lineterminator='\n')
        w.writeheader(); w.writerows(credits[slug(r['name'])] for r in rows if slug(r['name']) in credits)
