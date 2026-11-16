# Landmarks

159 landmarks of the world, built and natural, on every continent: a photograph of each, its name, the country it is
in, its continent, exactly where it is, what kind of thing it is (built › religious › temple, natural › water ›
waterfall …) and, for built ones where the sources give a single year, the year it was finished. There are also two
embeddings: how the photograph looks (DINOv2) and how the name sounds (a ByT5 pronunciation model). A dataset for
[Knack](https://github.com/lorien-danger/knack). Add it by this repo's link.

Suggested decks: **Name the landmark** (photo, name), **Where in the world?** (photo, name, where it is) and
**Which country?** (photo, name, country).

| continent | landmarks | | kind | landmarks |
| --- | --- | --- | --- | --- |
| Asia | 46 | | built | 97 |
| Europe | 29 | | natural | 62 |
| North America | 26 | | | |
| Africa | 22 | | | |
| South America | 19 | | | |
| Oceania | 14 | | | |
| Antarctica | 3 | | | |

## Columns

| column | what it is | source |
| --- | --- | --- |
| name | the usual English name, from the title of its English Wikipedia article (shortened where the title is long or disambiguated: "Kilimanjaro" for Mount Kilimanjaro, "Big Ben", "Ngorongoro Crater" for the Ngorongoro Conservation Area). The list is `build/landmarks.tsv` | Wikipedia |
| photo | a photograph of it, at most 560 × 480 pixels, in `media/` | Wikimedia Commons; each file's author and licence are in [`media/credits.tsv`](media/credits.tsv) |
| country | the country it is in today: Wikidata's *country* (P17) without an end date. Wikidata gives two for the Potala Palace (Tibet and China: China is used) and the Perito Moreno Glacier (Argentina and Chile: it lies in Argentina's Los Glaciares National Park). "People's Republic of China" is written China and "Federated States of Micronesia" Micronesia. The three in Antarctica have no country, and the column is empty for them | Wikidata |
| continent | the continent its country is in, except Lake Baikal (Asia), St Basil's Cathedral (Europe) and Ahu Tongariki, which is on Easter Island in Polynesia (Oceania, though Chile governs it). Turkey's two (Pamukkale, Mount Ararat) are in Asia; Central America and the Caribbean are counted in North America | the country's continent; written in `build/build.py` |
| where it is | a place on the globe, latitude and longitude to 4 decimals: Wikidata's *coordinate location* (P625), the preferred one where there are several | Wikidata |
| what it is | a tree of kinds (below), chosen for each from Wikidata's *instance of* (P31) and the first sentence of its Wikipedia article. `build/kinds.txt` | Wikidata, Wikipedia |
| year finished | for built landmarks, the year it was finished, where the sources give one year; negative years are BC (−2560 for the Great Pyramid). Where the sources give only a century, a range of centuries, a city or complex built over a long time, or disagree, it is left empty: 58 of the 97 built landmarks have a year. Every value and every gap, with where it comes from, is in `build/years.tsv` | the article's Wikipedia infobox (completed, completion date, built), Wikidata (inception P571, date of official opening P1619), or the article's text |
| photo look | an embedding of the photograph: DINOv2 (`facebook/dinov2-base`), 64 numbers, in `photo-look.npy`. The full 768-number vectors are in `build/photo-look-full.npy` | made by `build/embed.py` |
| name sound | an embedding of how the name is said: a ByT5 pronunciation model, 64 numbers, in `name-sound.npy` | made by the Knack app's `npm run describe` |

### What it is

    built     religious  temple, church, mosque, shrine, stupa, monastery
              monument   tomb, statue, sculpture, obelisk, arch, gate, stone circle, geoglyph
              defence    castle, fort, fortress, wall
              venue      amphitheatre, opera house
              palace, tower, skyscraper, bridge, ancient city, town, hotel, parliament, square, canal
    natural   landform   mountain, volcano, hills, canyon, valley, cliff, crater, rock formation, clay pan,
                         salt flat, dunes
              water      waterfall, lake, fjord, bay, strait, river delta, reef, sinkhole, glacier, hot spring,
                         geyser

The kinds are this dataset's own grouping, made to be learnt: each landmark's kind is read from what Wikidata and
Wikipedia say it is, and where it is several things the one it is known for is used (Mount Rushmore is a sculpture,
Meteora its monasteries, Mont-Saint-Michel a town).

### Which landmarks

Chosen to be widely known, spread over the continents rather than weighted to Europe, and a mix of built and natural.
Some famous ones were left out:

- Ones that lie across a border, whose country would be two answers: Victoria Falls, Iguazu Falls, Niagara Falls,
  Mount Everest, K2, the Matterhorn, Lake Titicaca, the Dead Sea.
- Ones whose Commons photographs showed them only at night, from an odd angle or in a detail: the Hassan II Mosque, the
  Sheikh Zayed Grand Mosque and the Bayterek Tower; and Karnak, the Avenue of the Baobabs and the Marble Caves
  (no clear photograph, or no article).
- The Dome of the Rock and other places whose country is disputed.

## Photographs

Most photographs are the landmark's main image on Wikidata (P18), which is usually the one at the top of its Wikipedia
article. Where there were several, or the main one was taken at night, from an odd angle, or showed only a detail
(the Sigiriya frescoes, a gate of Neuschwanstein), another was chosen by eye. For five (Tianzi Mountains, Fushimi
Inari-taisha, the Cliffs of Moher, the Space Needle and the Sky Tower) none of Wikidata's was right, and one was chosen
from a Commons search. `build/photos.tsv` names every file and where it was found.

The files were downloaded from Wikimedia Commons and scaled to fit 560 × 480 pixels (about 7 MB in all).
Their licences: CC BY-SA 4.0 (66), CC BY-SA 3.0 (34, three of them the German port), public domain (16), CC BY 2.0
(12), CC BY 2.5 (6), CC0 (6), CC BY-SA 2.0 (6, one the Austrian port), CC BY-SA 2.5 (5, one the Dutch port), Free Art
License (3), CC BY 3.0 (2), CC BY 4.0 (2) and the Korea Open Government Licence Type 1 (1, Gyeongbokgung; attribution
only). Where a file page names no author, the uploader is credited and marked as such. Author, licence, Commons page and description for every file are in
[`media/credits.tsv`](media/credits.tsv).

## Licence

The data (`columns.json`, `rows.jsonl`, the `.npy` files) is drawn from Wikidata (CC0) and Wikipedia (CC BY-SA 4.0),
so it is shared under [Creative Commons Attribution-ShareAlike 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
(`LICENSE`). Attribution: Wikidata; Wikipedia contributors, the English Wikipedia article of each landmark (the
revision read is in `build/sources/infobox.json`).

Each photograph in `media/` keeps its own licence, listed with its author in `media/credits.tsv`. The build scripts in
`build/` may be used freely.

## Checked by hand

- Every photograph, by eye, against its landmark: about 250 Wikidata images and 70 Commons search results were looked
  at, and the one that shows the landmark as people know it, whole and in daylight, was chosen.
- Every place on the globe lies inside its country's border (tested against the shapes in
  [knack-countries](https://github.com/lorien-danger/knack-countries)); the ones that fall just outside are on a
  coast or in the Vatican, which that scale cannot resolve.
- Whole rows read one by one against what is known of them: the Great Pyramid, Angkor Wat, the Eiffel Tower, the Golden
  Gate Bridge, the Burj Khalifa, Tikal Temple I, Uluru, Kaieteur Falls, Deadvlei, Nan Madol, Ahu Tongariki and Mount
  Erebus. Names, countries, places, kinds and years are right.
- Every year, against the infobox or statement it was read from (`build/years.tsv` quotes each).
- The photo look embedding, by its nearest neighbours: the CN Tower is nearest the Space Needle, the Sky Tower and the
  Tokyo Skytree; Murchison Falls nearest Kaieteur Falls, the Rhine Falls and Gullfoss.
- In the Knack app, at phone size: the Columns screen for every column, and each suggested deck practised for
  about fifteen questions.

## Building it

`build/` makes the dataset. It needs Python 3; `photos.py` also needs pillow, and `embed.py` needs numpy, torch,
transformers and pillow.

    cd build
    python3 fetch.py      # download the sources into build/sources/ (already there: the copies used)
    python3 build.py      # columns.json and rows.jsonl
    python3 photos.py     # the photographs chosen in photos.tsv -> media/, with media/credits.tsv
    python3 embed.py      # photo look (DINOv2): photo-look.npy and its column
    # name sound: from a checkout of the Knack app,  npm run describe -- <this folder> name

`build.py` keeps the embedding columns already in `columns.json`, so it can be rerun on its own.
