"""
Make columns.json and rows.jsonl from the fixed copies in build/sources/ and the choices made by hand here:

  landmarks.tsv  which landmarks, by their English Wikipedia article, and the name each goes by
  kinds.txt      what kind of thing each is (a path in the kind tree), read from Wikidata's "instance of" and the
                 article's first sentence
  years.tsv      the year each built landmark was finished, where a source gives one, with where it comes from
  photos.tsv     the Wikimedia Commons photograph chosen for each (fetched into media/ by photos.py)

  python3 build.py

The country is Wikidata's (P17: the current one, without an end date), with the overrides below; the place on the
globe is Wikidata's coordinate location (P625: the preferred one, else the first). The continent is the country's,
with the overrides below. Embedding columns already in columns.json are kept, so this can be rerun on its own.
"""
import csv, json, re, unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

# where Wikidata lists more than one current country
COUNTRY = {'Potala Palace': 'China', 'Perito Moreno Glacier': 'Argentina'}
# shorter, usual English names for Wikidata's labels
COUNTRY_NAME = {"People's Republic of China": 'China', 'Federated States of Micronesia': 'Micronesia'}
CONTINENT_OF = {
 'Africa': 'Egypt, Tanzania, South Africa, Mali, Ethiopia, Zimbabwe, Morocco, Libya, Tunisia, Botswana, Uganda, Madagascar, Namibia, Ivory Coast, Kenya',
 'Asia': 'India, China, Japan, Cambodia, Indonesia, Myanmar, Thailand, Vietnam, Malaysia, Singapore, Philippines, South Korea, Nepal, Sri Lanka, Bhutan, United Arab Emirates, Jordan, Turkey, Iran, Uzbekistan, Lebanon, Pakistan, Taiwan, Kazakhstan, Russia',
 'Europe': 'France, Italy, Vatican City, Spain, Greece, United Kingdom, Germany, Czech Republic, Belgium, Ireland, Croatia, Norway, Iceland, Portugal, Hungary, Romania, Switzerland',
 'North America': 'United States, Canada, Mexico, Guatemala, Costa Rica, Belize, Saint Lucia, Cuba, Haiti, Panama',
 'South America': 'Peru, Brazil, Venezuela, Argentina, Chile, Bolivia, Ecuador, Guyana, Colombia',
 'Oceania': 'Australia, New Zealand, Micronesia',
}
CONTINENT = {'Lake Baikal': 'Asia', "St Basil's Cathedral": 'Europe',
             'Ahu Tongariki': 'Oceania',  # on Easter Island (Rapa Nui), in Polynesia, though Chile governs it
             'Mount Erebus': 'Antarctica', 'Lemaire Channel': 'Antarctica', 'Deception Island': 'Antarctica'}

def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')

def tsv(name): return list(csv.DictReader(open(HERE / name), delimiter='\t'))

if __name__ == '__main__':
    wd = json.load(open(HERE / 'sources/wikidata.json')); ib = json.load(open(HERE / 'sources/infobox.json'))
    labels = wd['labels']
    kinds = dict(l.rstrip('\n').split('|') for l in open(HERE / 'kinds.txt') if l.strip())
    years = {r['name']: r['finished'] for r in tsv('years.tsv')}
    photos = {r['name']: r for r in tsv('photos.tsv')} if (HERE / 'photos.tsv').exists() else {}
    cont = {c: k for k, cs in CONTINENT_OF.items() for c in cs.split(', ')}
    rows = []
    for r in tsv('landmarks.tsv'):
        n = r['name']
        claims = wd['items'][ib[r['wikipedia']]['qid']]['claims']
        cur = [x for x in claims.get('P17', []) if 'P582' not in x.get('q', {})]
        cur = [x for x in cur if x['rank'] == 'preferred'] or cur
        country = COUNTRY.get(n) or (COUNTRY_NAME.get(labels[cur[0]['v']], labels[cur[0]['v']]) if cur else None)
        if len(cur) > 1 and n not in COUNTRY: raise SystemExit(f'{n}: more than one country')
        locs = claims['P625']
        lat, lon = ([x for x in locs if x['rank'] == 'preferred'] or locs)[0]['v']
        row = {'id': slug(n), 'name': n}
        p = photos.get(n)
        if p and p['file']: row['photo'] = f"media/{slug(n)}.jpg"
        if country: row['country'] = country
        row['continent'] = CONTINENT.get(n) or cont[country]
        row['location'] = [round(lat, 4), round(lon, 4)]
        row['kind'] = [k.strip() for k in kinds[n].split('>')]
        if years.get(n): row['finished'] = int(years[n])
        rows.append(row)
    assert len({r['id'] for r in rows}) == len(rows)
    meta_path = ROOT / 'columns.json'
    old = json.load(open(meta_path)) if meta_path.exists() else {'columns': []}
    columns = [
        {'name': 'name', 'type': 'text'},
        {'name': 'photo', 'type': 'plain', 'media': 'image'},
        {'name': 'country', 'type': 'plain'},
        {'name': 'continent', 'type': 'plain'},
        {'name': 'location', 'type': 'sphere', 'label': 'Where it is'},
        {'name': 'kind', 'type': 'tree', 'label': 'What it is'},
        {'name': 'finished', 'type': 'number', 'label': 'Year finished'},
    ]
    # what makes a column's values alike (added by embed.py and by the app) stays on the column
    near = {c['name']: c['near'] for c in old['columns'] if 'near' in c}
    for c in columns:
        if c['name'] in near: c['near'] = near[c['name']]
    meta = {'name': 'Landmarks', 'item': 'landmark', 'items': 'landmarks', 'title': 'name',
            'practices': [
                {'name': 'Name the landmark', 'columns': ['photo', 'name']},
                {'name': 'Where in the world?', 'columns': ['photo', 'name', 'location']},
                {'name': 'Which country?', 'columns': ['photo', 'name', 'country']},
            ],
            'columns': columns}
    with open(meta_path, 'w') as f: f.write(json.dumps(meta, indent=1, ensure_ascii=False) + '\n')
    with open(ROOT / 'rows.jsonl', 'w') as f:
        for row in rows: f.write(json.dumps(row, ensure_ascii=False) + '\n')
    print(len(rows), 'rows;', sum('finished' in r for r in rows), 'with a year;', sum('photo' in r for r in rows), 'with a photo')
