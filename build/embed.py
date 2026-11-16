"""
Embed the photographs with DINOv2, a self-supervised vision model that goes by shape, texture and colour, and write
the "photo look" embedding column. Adapted from knack-countries' build/embed.py.

  python embed.py [folder]      (needs numpy, torch, transformers, pillow; folder defaults to ..)

Writes the full-size vectors to build/photo-look-full.npy (not a column; NaN rows for any landmark without a photograph)
and the 64-number version to <folder>/photo-look.npy, and sets the column in <folder>/columns.json. The 64-number
version is made as the Knack app does (src/lib/engine/embed.ts, reduce): unit-length vectors, centre, PCA to 64
numbers, scale so the mean squared norm is 1; it is worked out over the landmarks, and the
others are rows of NaN, as the app writes them.

The photographs are not all square, so each is shown to the model whole: scaled to fit 224x224 and padded with the
colour of its own border (no centre crop, which would cut off the top of a tower or the ends of a bridge, and no squashing).
The class token (final layer norm) is used.
"""
import json, sys
from pathlib import Path
import numpy as np, torch
from PIL import Image
from transformers import AutoModel

HERE = Path(__file__).resolve().parent
COLUMN, FILE, MODEL, OF = 'photo look', 'photo-look.npy', 'facebook/dinov2-base', 'photo'
MEAN, STD = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]

def reduce(v, dims=64):
    u = v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-12)
    z = (u - u.mean(0)).astype(np.float64)
    _, _, vt = np.linalg.svd(z, full_matrices=False)
    p = z @ vt[:dims].T
    return (p / np.sqrt((p ** 2).sum(1).mean())).astype(np.float32)

def square(path, side=224):
    im = Image.open(path).convert('RGB')
    a = np.asarray(im)
    edge = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]]).mean(0).astype(np.uint8)
    im.thumbnail((side, side), Image.BICUBIC)
    out = Image.new('RGB', (side, side), tuple(int(x) for x in edge))
    out.paste(im, ((side - im.width) // 2, (side - im.height) // 2))
    return np.asarray(out, dtype=np.float32) / 255

@torch.no_grad()
def run(paths):
    model = AutoModel.from_pretrained(MODEL).eval()
    out = []
    for s in range(0, len(paths), 16):
        x = (np.stack([square(p) for p in paths[s:s + 16]]) - np.array(MEAN, dtype=np.float32)) / np.array(STD, dtype=np.float32)
        out.append(model(pixel_values=torch.from_numpy(x).permute(0, 3, 1, 2)).pooler_output.numpy())
    return np.concatenate(out)

if __name__ == '__main__':
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent
    rows = [json.loads(l) for l in open(root / 'rows.jsonl') if l.strip()]
    have = [i for i, r in enumerate(rows) if r.get(OF)]
    full_have = run([root / rows[i][OF] for i in have])
    full = np.full((len(rows), full_have.shape[1]), np.nan, dtype=np.float32)
    small = np.full((len(rows), 64), np.nan, dtype=np.float32)
    full[have], small[have] = full_have, reduce(full_have)
    np.save(HERE / 'photo-look-full.npy', full)
    np.save(root / FILE, small)
    meta = json.load(open(root / 'columns.json'))
    col = {'name': COLUMN, 'type': 'embedding', 'file': FILE, 'of': OF, 'model': MODEL}
    meta['columns'] = [c for c in meta['columns'] if c['name'] != COLUMN] + [col]
    with open(root / 'columns.json', 'w') as f: f.write(json.dumps(meta, indent=1, ensure_ascii=False) + '\n')
    print(COLUMN, full_have.shape, 'for', len(have), 'of', len(rows), '->', FILE, flush=True)
