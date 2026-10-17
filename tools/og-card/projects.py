#!/usr/bin/env python3
"""Regenerate content/projects/card.png, the /projects/ page's share image.

    uv run --with pillow --with fonttools --with brotli --with resvg-py tools/og-card/projects.py

A text card in the post cards' style (posts.py draws the card), with the six project icons in a
3 x 2 grid where a post's gem would be, and Duna sitting on the my-resume tile as she does on the
page. The icons come from the page itself: the SVGs in content/projects/ (rendered with resvg, no
browser needed) plus two raster icons copied here from their own repos, icons/rllvm.png (rllvm's
site/assets/images/logo-short.png) and icons/chromatron.png (chromatron's
web/apple-touch-icon.png). If a project's icon changes, update the copy here and rerun. Saved in
full color, since a palette would grey out the icons.
"""
import io
import re
from pathlib import Path

import resvg_py
from PIL import Image, ImageDraw, ImageFilter

from posts import H, ROOT, W, background, draw_text, frame

HERE = Path(__file__).resolve().parent
BUNDLE = ROOT / "content" / "projects"

TILE, GAP, RADIUS = 112, 18, 26
# (source, tile background), in the page's card order.
ICONS = [
    (HERE / "icons" / "rllvm.png", (255, 255, 255)),
    (BUNDLE / "grammar-mutator.svg", None),
    (BUNDLE / "my-resume.svg", None),
    (HERE / "icons" / "chromatron.png", None),
    (BUNDLE / "cairn.svg", None),
    (BUNDLE / "htb.svg", None),
]
# Duna's coat, as facet's cast colors her.
DUNA = {"--coat": "#9aa3ad", "--stripe": "#59626d", "--light": "#eceff2",
        "--iris": "#e3a72f", "--nose": "#e48b8b", "--cat-edge": "rgb(255 255 255 / .2)",
        "--cat-shadow": "rgb(0 0 0 / .35)"}
INTRO = "Compiler tooling, fuzzing, a game I loved as a kid, and notes from breaking things on purpose."


def svg_image(path, width, colours=None):
    """Render an SVG at `width` px. CSS variables are substituted first, and the
    pose overlays that the page shows only on hover (Duna's raised paw and
    closed lids) are dropped."""
    svg = path.read_text()
    svg = re.sub(r'<g class="cat-(wave|lids)">.*?</g>\s*(?=<g class="cat-|</svg>)', "", svg, flags=re.S)
    for name, value in (colours or {}).items():
        svg = svg.replace(f"var({name})", value)
    return Image.open(io.BytesIO(resvg_py.svg_to_bytes(svg_string=svg, width=width))).convert("RGBA")


def tile(source, bg):
    size = TILE * 2  # draw at 2x, scale down for clean rounded edges
    if source.suffix == ".svg":
        art = svg_image(source, size)
    else:
        art = Image.open(source).convert("RGBA").resize((size, size), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), bg + (255,) if bg else (0, 0, 0, 0))
    canvas.alpha_composite(art)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], RADIUS * 2, fill=255)
    canvas.putalpha(mask)
    return canvas.resize((TILE, TILE), Image.LANCZOS)


def card():
    im = background(None, gem=False)
    draw_text(im, f"PROJECTS · {len(ICONS)}", "Projects", INTRO, site="shengtuo.me/projects")
    im = im.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    # The grid sits where a post's gem would, vertically centered, each tile on a soft shadow.
    x0 = W - 64 - (3 * TILE + 2 * GAP)
    y0 = (H - (2 * TILE + GAP)) // 2 + 30
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    spots = []
    for i, (source, bg) in enumerate(ICONS):
        x, y = x0 + (i % 3) * (TILE + GAP), y0 + (i // 3) * (TILE + GAP)
        sd.rounded_rectangle([x + 6, y + 14, x + TILE - 6, y + TILE + 8], RADIUS, fill=(0, 0, 0, 110))
        spots.append((tile(source, bg), (x, y)))
    im.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(12)))
    for art, xy in spots:
        im.alpha_composite(art, xy)
    # Duna, sitting on the my-resume tile (top right).
    duna = svg_image(BUNDLE / "duna.svg", 78, DUNA)
    im.alpha_composite(duna, (x0 + 2 * (TILE + GAP) + TILE // 2 - 39, y0 - duna.height + 14))
    # Nothing leaks past the rounded card.
    out = Image.new("RGBA", (W, H), im.getpixel((0, 0)))
    out.paste(im, (0, 0), frame().resize((W, H), Image.Resampling.LANCZOS))
    return out.convert("RGB")


if __name__ == "__main__":
    out = BUNDLE / "card.png"
    card().save(out, optimize=True)
    print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")
