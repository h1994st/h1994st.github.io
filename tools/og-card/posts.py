#!/usr/bin/env python3
"""Per-post share images (og:image), 1200x630, in one style.

uv run --with pillow --with fonttools --with brotli tools/og-card/posts.py [--out static/cards]

Every post under content/blog gets one. Without its own [extra] card: date and tags, title,
description and byline on the left of a deep Moss card, a generated gem on the right. With one:
the post's image stays primary on the left (card_fit = "fit": whole, ~70% wide; "fill": covering,
right third faded) and fades into the generated card. The gem is random but seeded with the post's
path (and [extra] card_seed), so builds are reproducible. Remote cards (paths not in this repo)
are fetched from https://shengtuo.me/<path>.

The output is git-ignored; CI runs this before `zola build`, and templates/partials/card.html
points each post's og:image at static/cards/<post path>.png when it exists.
"""

import argparse
import datetime
import functools
import hashlib
import io
import math
import random
import re
import sys
import tomllib
import urllib.request
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[2]
FONTS = ROOT / "static" / "vendor" / "facet" / "dist" / "fonts"
SITE = "https://shengtuo.me"
W, H = 1200, 630
S = 2  # drawn at 2x, then downsampled with Lanczos

INSET, RADIUS = 48, 36  # the rounded card frame
TEXT_X, TEXT_RIGHT = 104, 700  # the text block's left edge and the line it never crosses
BYLINE = "Shengtuo Hu  ·  nu1lptr"
EDGE = 0.12  # fit: how far, as a share of the card's width, an image's edge melts
GEM_BOX = (620, INSET, W - INSET, H - INSET)  # the frame; its rounded mask crops the gem


def oklch_to_rgb(lightness, chroma, hue):
    """OKLCH to 8-bit sRGB, clamped to the gamut (from facet's scripts/tokens.py)."""
    a = chroma * math.cos(math.radians(hue))
    b = chroma * math.sin(math.radians(hue))
    lms = [
        (lightness + 0.3963377774 * a + 0.2158037573 * b) ** 3,
        (lightness - 0.1055613458 * a - 0.0638541728 * b) ** 3,
        (lightness - 0.0894841775 * a - 1.2914855480 * b) ** 3,
    ]
    linear = [
        4.0767416621 * lms[0] - 3.3077115913 * lms[1] + 0.2309699292 * lms[2],
        -1.2684380046 * lms[0] + 2.6097574011 * lms[1] - 0.3413193965 * lms[2],
        -0.0041960863 * lms[0] - 0.7034186147 * lms[1] + 1.7076147010 * lms[2],
    ]

    def encode(x):
        x = min(max(x, 0.0), 1.0)
        x = 12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055
        return round(x * 255)

    return tuple(encode(x) for x in linear)


PAGE = (0x13, 0x16, 0x1C)
DEEP = oklch_to_rgb(0.42, 0.06, 130)
DEEPER = oklch_to_rgb(0.28, 0.05, 140)
ON = oklch_to_rgb(0.97, 0.008, 130)
MOSS = oklch_to_rgb(0.76, 0.06, 130)


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


@functools.cache
def font(name, size, **axes):
    """A facet WOFF2, decompressed in memory, at `size` (1x px) and the given variation axes."""
    tt = TTFont(FONTS / f"{name}.woff2")
    tt.flavor = None
    buf = io.BytesIO()
    tt.save(buf)
    buf.seek(0)
    f = ImageFont.truetype(buf, size * S)
    values = []
    for axis in f.get_variation_axes():
        key = axis["name"].decode().lower().replace(" ", "_")
        values.append(axes.get(key, axis["default"]))
    f.set_variation_by_axes(values)
    return f


# --- the gem ---------------------------------------------------------------------------------


def _hull(points):
    """Convex hull, counter-clockwise (monotone chain)."""
    pts = sorted(set(points))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _clip(poly, box):
    """Sutherland-Hodgman: `poly` clipped to the rectangle `box`."""
    x0, y0, x1, y1 = box
    edges = (
        (lambda p: p[0] >= x0, lambda a, b: (x0, a[1] + (b[1] - a[1]) * (x0 - a[0]) / (b[0] - a[0]))),
        (lambda p: p[0] <= x1, lambda a, b: (x1, a[1] + (b[1] - a[1]) * (x1 - a[0]) / (b[0] - a[0]))),
        (lambda p: p[1] >= y0, lambda a, b: (a[0] + (b[0] - a[0]) * (y0 - a[1]) / (b[1] - a[1]), y0)),
        (lambda p: p[1] <= y1, lambda a, b: (a[0] + (b[0] - a[0]) * (y1 - a[1]) / (b[1] - a[1]), y1)),
    )
    out = list(poly)
    for inside, cut in edges:
        if not out:
            break
        src, out = out, []
        for i, cur in enumerate(src):
            prev = src[i - 1]
            if inside(cur):
                if not inside(prev):
                    out.append(cut(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(cut(prev, cur))
    return out


def _faces(rnd, box):
    """The gem's faces as (3D points, x/y/z), before projection and clipping."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    # an irregular convex outline: 5 to 11 vertices, jittered in angle and radius
    while True:
        n = rnd.randint(5, 11)
        rot = rnd.uniform(0, math.tau)
        outline = []
        for i in range(n):
            a = rot + (i + rnd.uniform(-0.3, 0.3)) * math.tau / n
            r = rnd.uniform(0.8, 1.0)
            outline.append((r * math.cos(a), r * math.sin(a)))
        outline = _hull(outline)
        if len(outline) >= 5:
            break
    # an off-center apex, and 1 to 3 rings of facets stepping in toward it
    apex = (rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3))
    rings = [[(x, y, 0.0) for x, y in outline]]
    count = rnd.randint(1, 3)
    for k in range(1, count + 1):
        t = k / (count + 1) * rnd.uniform(0.85, 1.15) + 0.12
        z = 0.15 + 0.55 * (1 - (1 - t) ** 2)
        rings.append([(x + (apex[0] - x) * t, y + (apex[1] - y) * t, z) for x, y in outline])
    cut = rnd.choice(("fan", "ring", "mixed"))
    faces = []
    for k in range(count):
        outer, inner = rings[k], rings[k + 1]
        split = cut == "fan" or (cut == "mixed" and rnd.random() < 0.5)
        for i in range(len(outer)):
            j = (i + 1) % len(outer)
            if split:  # each band cut into triangles, the diagonal alternating
                if i % 2:
                    faces += [[outer[i], outer[j], inner[i]], [outer[j], inner[j], inner[i]]]
                else:
                    faces += [[outer[i], outer[j], inner[j]], [outer[i], inner[j], inner[i]]]
            else:
                faces.append([outer[i], outer[j], inner[j], inner[i]])
    top = rings[-1]
    if cut == "ring" or (cut == "mixed" and rnd.random() < 0.5):
        faces.append(list(top))  # a flat table
    else:
        peak = (apex[0], apex[1], top[0][2] + 0.18)
        faces += [[top[i], top[(i + 1) % len(top)], peak] for i in range(len(top))]
    # random stretch, rotation and size; placed right of the text and nudged clear of it, so a
    # large gem is cropped by the box on the right, top or bottom
    sx, sy = rnd.uniform(0.75, 1.25), rnd.uniform(0.75, 1.25)
    turn = rnd.uniform(0, math.tau)
    c, s = math.cos(turn), math.sin(turn)
    size = min(w, h) * rnd.uniform(0.42, 0.62)
    cx, cy = x0 + w * rnd.uniform(0.5, 0.66), y0 + h * rnd.uniform(0.42, 0.58)

    def place(p):
        x, y, z = p[0] * sx, p[1] * sy, p[2]
        return (cx + size * (x * c - y * s), cy + size * (x * s + y * c), z * size)

    faces = [[place(p) for p in f] for f in faces]
    left = min(p[0] for f in faces for p in f)
    shift = max(0.0, x0 + 0.2 * w - left)
    return [[(x + shift, y, z) for x, y, z in f] for f in faces]


def _shade(face):
    """How much a face turns toward a light at the top left (and in front), 0..1."""
    (ax, ay, az), (bx, by, bz), (qx, qy, qz) = face[0], face[1], face[2]
    ux, uy, uz = bx - ax, by - ay, bz - az
    vx, vy, vz = qx - ax, qy - ay, qz - az
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    if nz < 0:
        nx, ny, nz = -nx, -ny, -nz
    norm = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    lx, ly, lz = -0.55, -0.65, 0.52
    ln = math.sqrt(lx * lx + ly * ly + lz * lz)
    return max(0.0, (nx * lx + ny * ly + nz * lz) / (norm * ln))


def _gem(rnd, box):
    """The gem's faces as (polygon, shade 0..1), clipped to `box`; empty faces dropped."""
    faces = _faces(rnd, box)
    shades = [_shade(f) for f in faces]
    lo, hi = min(shades), max(shades)
    out = []
    for f, v in zip(faces, shades):
        poly = _clip([(x, y) for x, y, _ in f], box)
        if len(poly) >= 3:
            out.append((poly, (v - lo) / (hi - lo) if hi > lo else 0.5))
    return out


def gem(rnd, box):
    """A generated faceted gem inside `box` (1x px): its faces as polygons, clipped to the box."""
    return [poly for poly, _ in _gem(rnd, box)]


def _draw_gem(d, rnd, box):
    edge = mix(DEEP, ON, 0.14)
    for poly, lit in _gem(rnd, box):
        fill = mix(DEEP, MOSS, 0.05 + 0.6 * lit)
        d.polygon([(x * S, y * S) for x, y in poly], fill=fill, outline=edge, width=S)


# --- the card --------------------------------------------------------------------------------


def _seed(path, extra):
    return hashlib.sha256((path + str(extra.get("card_seed") or "")).encode()).digest()


def frame():
    mask = Image.new("L", (W * S, H * S), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (INSET * S, INSET * S, (W - INSET) * S - 1, (H - INSET) * S - 1), radius=RADIUS * S, fill=255)
    return mask


def background(seed, gem=True):
    """A generated card at 2x: page color around a rounded deep Moss card, fading to a deeper
    green, a dot grid that brightens to the right and, if `gem`, the gem seeded by `seed`."""
    c = Image.new("RGB", (W * S, H * S), PAGE)
    d = ImageDraw.Draw(c)
    for x in range(0, W * S, S):
        d.line((x, 0, x, H * S), fill=mix(DEEP, DEEPER, (x / (W * S)) ** 1.4), width=S)
    for gx in range(560, W, 28):
        for gy in range(80, H - 80, 28):
            a = max(0.0, (gx - 560) / 600)
            r = 1.6 * S
            d.ellipse((gx * S - r, gy * S - r, gx * S + r, gy * S + r), fill=mix(DEEP, MOSS, 0.12 + 0.4 * a))
    if gem:
        _draw_gem(d, random.Random(seed), GEM_BOX)
    out = Image.new("RGB", (W * S, H * S), PAGE)
    out.paste(c, (0, 0), frame())
    return out


def _background(path, extra):
    return background(_seed(path, extra))


def _wrap(text, f, width, lines):
    """`text` wrapped to `width` (2x px) in at most `lines` lines, the last one ending in an
    ellipsis when cut. Words wider than a line are broken."""
    words = []
    for word in text.split():
        while f.getlength(word) > width:
            k = len(word)
            while k > 1 and f.getlength(word[:k]) > width:
                k -= 1
            words.append(word[:k])
            word = word[k:]
        if word:
            words.append(word)
    out, cur = [], ""
    for word in words:
        t = f"{cur} {word}".strip()
        if f.getlength(t) <= width or not cur:
            cur = t
        else:
            out.append(cur)
            cur = word
    if cur:
        out.append(cur)
    if len(out) > lines:
        out = out[:lines]
        last = out[-1].rstrip(".,;:") + "…"
        while f.getlength(last) > width and " " in last:
            last = last.rsplit(" ", 1)[0].rstrip(".,;:") + "…"
        while f.getlength(last) > width and len(last) > 1:
            last = last[:-2] + "…"
        out[-1] = last
    return out


def _date(value):
    if isinstance(value, datetime.datetime):
        value = value.date()
    elif not isinstance(value, datetime.date):
        value = datetime.date.fromisoformat(str(value)[:10])
    return f"{value:%b} {value.day}, {value.year}"


def _runs(kicker, title, description, byline, site):
    """Every text run on a text card: name -> [(xy at 2x, text, font, fill)]."""
    x = TEXT_X * S
    width = (TEXT_RIGHT - TEXT_X) * S
    mono = font("geist-mono", 22)
    runs = {"meta": [], "title": [], "description": [], "byline": [], "site": []}
    if kicker:
        runs["meta"].append(((x, 104 * S), kicker, mono, mix(DEEP, ON, 0.8)))
    serif = font("source-serif-4", 70, weight=600, optical_size=60)
    y = 154
    for line in _wrap(title or "", serif, width, 3):
        runs["title"].append(((x, y * S), line, serif, ON))
        y += 82
    sans = font("geist", 28)
    y += 12
    for line in _wrap(description or "", sans, width, 2 if y > 330 else 3):
        runs["description"].append(((x, y * S), line, sans, mix(DEEP, ON, 0.85)))
        y += 40
    runs["byline"].append(((x, (H - 112) * S), byline, font("geist", 26, weight=500), ON))
    runs["site"].append((((W - 104) * S - mono.getlength(site), (H - 108) * S), site, mono, mix(DEEP, ON, 0.8)))
    return runs


def _layout(m):
    """A post's text runs: date and as many of its first three tags as fit, then the title,
    description and byline."""
    width = (TEXT_RIGHT - TEXT_X) * S
    mono = font("geist-mono", 22)
    tags = list(m.get("tags") or [])[:3]
    while True:
        line = " · ".join([_date(m["date"])] + tags).upper() if m.get("date") else " · ".join(tags).upper()
        if not tags or mono.getlength(line) <= width:
            break
        tags.pop()
    return _runs(line, m.get("title"), m.get("description"), BYLINE, "shengtuo.me")


def draw_text(im, kicker, title, description, byline=None, site="shengtuo.me"):
    """Draw a text card's left side onto `im` (a 2x background)."""
    d = ImageDraw.Draw(im)
    for runs in _runs(kicker, title, description, byline or BYLINE, site).values():
        for xy, text, f, fill in runs:
            d.text(xy, text, font=f, fill=fill)


def text_boxes(m):
    """Each text group's line boxes at 1x, (left, top, right, bottom)."""
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    return {name: [tuple(v / S for v in d.textbbox(xy, text, font=f)) for xy, text, f, _ in runs]
            for name, runs in _layout(m).items()}


def _fade(width, height, start, end):
    """An L mask, opaque left of `start` (fraction of width) and clear right of `end`."""
    row = bytes(255 - round(255 * min(1.0, max(0.0, (x / width - start) / (end - start))))
                for x in range(width))
    return Image.frombytes("L", (width, 1), row).resize((width, height), Image.Resampling.NEAREST)


def _own(im, own, fit):
    """The post's own image over the generated card. `fill` covers the card and its right part
    fades; `fit` keeps the whole image opaque and melts it from its right edge: the last column
    of pixels is stretched sideways over EDGE of the card's width, fading out."""
    iw, ih = (W - 2 * INSET) * S, (H - 2 * INSET) * S
    own = own.convert("RGB")
    if fit == "fill":
        pic = ImageOps.fit(own, (iw, ih), Image.Resampling.LANCZOS, centering=(0.0, 0.5))
        mask = _fade(iw, ih, 0.55, 0.90)
        pos = (INSET * S, INSET * S)
    else:
        scale = min(0.7 * iw / own.width, ih / own.height)
        size = (round(own.width * scale), round(own.height * scale))
        image = own.resize(size, Image.Resampling.LANCZOS)
        band = round(EDGE * W * S)
        pic = Image.new("RGB", (size[0] + band, size[1]))
        pic.paste(image, (0, 0))
        pic.paste(image.crop((size[0] - 1, 0, size[0], size[1])).resize((band, size[1])), (size[0], 0))
        mask = _fade(pic.width, size[1], size[0] / pic.width, 1.0)
        pos = (INSET * S, INSET * S + (ih - size[1]) // 2)
    layer = Image.new("RGB", im.size, PAGE)
    layer.paste(pic, pos)
    m = Image.new("L", im.size, 0)
    m.paste(mask, pos)
    im.paste(layer, (0, 0), ImageChops.multiply(m, frame()))


def render_post(meta, path, own):
    """The share image for the post at `path` (its URL path); `own` is its [extra] card, if any."""
    extra = meta.get("extra") or {}
    im = _background(path, extra)
    if own is not None:
        _own(im, own, extra.get("card_fit", "fit"))
    else:
        d = ImageDraw.Draw(im)
        for runs in _layout(meta).values():
            for xy, text, f, fill in runs:
                d.text(xy, text, font=f, fill=fill)
    return im.resize((W, H), Image.Resampling.LANCZOS)


# --- the posts -------------------------------------------------------------------------------


def front_matter(md):
    text = md.read_text(encoding="utf-8")
    match = re.match(r"\+\+\+\s*\n(.*?)\n\+\+\+", text, re.S)
    return tomllib.loads(match[1]) if match else {}


def post_paths(content):
    """Every post's Markdown file under content/blog (sections' _index.md and drafts left out)."""
    return sorted(p for p in (content / "blog").rglob("*.md")
                  if p.name != "_index.md" and not front_matter(p).get("draft"))


def post_meta(md):
    fm = front_matter(md)
    return {"title": fm.get("title", ""), "description": fm.get("description", ""),
            "date": fm.get("date"), "tags": (fm.get("taxonomies") or {}).get("tags", []),
            "extra": fm.get("extra") or {}}


def _slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def post_url(md, content):
    """The post's path as Zola serves it, without slashes: blog/<slug> (blog/htb/<slug>)."""
    fm = front_matter(md)
    if fm.get("path"):
        return fm["path"].strip("/")
    rel = md.relative_to(content)
    bundle = md.name == "index.md"
    sections = rel.parts[:-2] if bundle else rel.parts[:-1]
    slug = fm.get("slug") or (rel.parts[-2] if bundle else md.stem)
    return "/".join([*(_slugify(s) for s in sections), _slugify(slug)])


def own_card(md, card):
    """The post's own [extra] card: in its bundle, else under static/, else from the live site.
    None (with a warning) when it cannot be read."""
    for candidate in ([md.parent / card] if md.name == "index.md" else []) + [ROOT / "static" / card]:
        if candidate.is_file():
            return Image.open(candidate)
    url = f"{SITE}/{card.lstrip('/')}"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return Image.open(io.BytesIO(r.read()))
    except Exception as e:  # offline, 404, not an image: fall back to a text card
        print(f"warning: {md.relative_to(ROOT)}: cannot fetch {url} ({e}); drawing a text card",
              file=sys.stderr)
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, default=ROOT / "static" / "cards")
    out = ap.parse_args().out
    content = ROOT / "content"
    for md in post_paths(content):
        m = post_meta(md)
        url = post_url(md, content)
        card = m["extra"].get("card")
        im = render_post(m, f"/{url}/", own_card(md, card) if card else None)
        dest = out / f"{url}.png"
        dest.parent.mkdir(parents=True, exist_ok=True)
        im.save(dest, optimize=True)
        print(f"wrote {dest} ({dest.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
