#!/usr/bin/env python3
"""Regenerate content/projects/card.png, the /projects/ page's share image.

    uv run --with pillow --with resvg-py tools/og-card/projects.py

Same terminal as the site card (render.py, whose helpers this reuses), with
the project icons on the right. The icons come from the page itself: the SVGs
in content/projects/ (rendered with resvg, no browser needed) plus two raster
icons copied here from their own repos, icons/rllvm.png (rllvm's
site/assets/images/logo-short.png) and icons/chromatron.png (chromatron's
web/apple-touch-icon.png). Duna, from content/projects/duna.svg, sits on the
status line. If a project's icon changes, update the copy here and rerun.
"""
import io
import re
from pathlib import Path

import resvg_py
from PIL import Image, ImageDraw, ImageFilter

from render import BODY, H, PAD_L, SAGE, W, background, finish, font, save, tracked

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUNDLE = ROOT / "content" / "projects"

TILE, GAP, RADIUS = 132, 22, 30
# (source, tile background, glow colour), in the page's card order.
ICONS = [
    (HERE / "icons" / "rllvm.png", (255, 255, 255), (42, 123, 255)),
    (BUNDLE / "grammar-mutator.svg", None, (91, 69, 214)),
    (BUNDLE / "my-resume.svg", None, (100, 116, 139)),
    (HERE / "icons" / "chromatron.png", None, (255, 42, 85)),
    (BUNDLE / "cairn.svg", None, (160, 122, 85)),
    (BUNDLE / "htb.svg", None, (111, 179, 0)),
]
# Duna's coat, as css/projects.css colours her on the page.
DUNA = {"--coat": "#9aa3ad", "--stripe": "#59626d", "--light": "#eceff2",
        "--iris": "#e3a72f", "--nose": "#e48b8b", "--cat-edge": "rgb(255 255 255 / .2)",
        "--cat-shadow": "rgb(0 0 0 / .35)"}


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


def main():
    img = background()
    glow_layer = Image.new("L", (W, H), 0)
    sharp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd, sd = ImageDraw.Draw(glow_layer), ImageDraw.Draw(sharp)
    f30, f104 = font(30), font(104, bold=True)

    # Same rhythm as the site card: prompt, the one bold line, quiet body text.
    y = 74 + 22.5
    px = PAD_L
    for text, alpha in (("~ $ ", 140), ("ls ~/projects", 255)):
        sd.text((px, y), text, font=f30, fill=SAGE + (alpha,), anchor="lm")
        gd.text((px, y), text, font=f30, fill=alpha, anchor="lm")
        px += f30.getlength(text)

    tracked(sd, (PAD_L, 186.2), "Projects", f104, SAGE + (255,), -0.03 * 104)
    tracked(gd, (PAD_L, 186.2), "Projects", f104, 255, -0.03 * 104)

    for i, line in enumerate(("Compiler tooling, fuzzing,", "a game I loved as a kid,",
                              "and notes from breaking", "things on purpose.")):
        sd.text((PAD_L, 290 + i * 46.5), line, font=f30, fill=BODY + (255,), anchor="lm")

    sd.text((PAD_L, 503), "~ $", font=f30, fill=SAGE + (140,), anchor="lm")
    gd.text((PAD_L, 503), "~ $", font=f30, fill=140, anchor="lm")
    cx = PAD_L + f30.getlength("~ $ ")
    sd.rectangle([cx, 503 - 17, cx + 17, 503 + 17], fill=SAGE + (255,))
    gd.rectangle([cx, 503 - 17, cx + 17, 503 + 17], fill=255)

    finish(img, glow_layer, sharp, "shengtuo.me/projects")

    # Icons go on after the CRT pass so the scanlines don't muddy them. Each
    # tile casts a soft glow in its project's colour, like the cards on hover.
    img = img.convert("RGBA")
    x0 = W - PAD_L - (3 * TILE + 2 * GAP)
    y0 = 128
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    spots = []
    for i, (source, bg, colour) in enumerate(ICONS):
        x = x0 + (i % 3) * (TILE + GAP)
        y = y0 + (i // 3) * (TILE + GAP)
        gdraw.rounded_rectangle([x + 10, y + 22, x + TILE - 10, y + TILE + 6], RADIUS, fill=colour + (150,))
        spots.append((tile(source, bg), (x, y)))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(14)))
    for art, xy in spots:
        img.alpha_composite(art, xy)

    # Duna, sitting on the status line under the last column.
    duna = svg_image(BUNDLE / "duna.svg", 92, DUNA)
    img.alpha_composite(duna, (W - PAD_L - 92 - 8, H - 52 - duna.height + 6))

    # Full colour: a 256-colour palette spent on the greens greys out the icons.
    save(img.convert("RGB"), "content/projects/card.png", quantize=False)


if __name__ == "__main__":
    main()
