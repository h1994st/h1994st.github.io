#!/usr/bin/env python3
"""Regenerate the site icon: static/favicon.svg, static/favicon.ico and static/apple-touch-icon.png.

    uv run --with fonttools --with brotli --with resvg-py --with pillow tools/icon/render.py

"0xHu" in Geist Mono Bold (facet's monospace, read from the submodule) on a deep Moss tile, the
same Moss as the share cards. The letters are outlined into the SVG, so the icon never depends on
an installed font. The SVG tile has rounded corners; the apple-touch icon is full-bleed because iOS
rounds it itself. Edit this script, not the files; output is deterministic.
"""
import io
from pathlib import Path

import resvg_py
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
FONT = ROOT / "static/vendor/facet/dist/fonts/geist-mono.woff2"
TEXT, SIZE, TRACK = "0xHu", 23.5, -0.6  # em size and tracking in px of the 64 px tile
INK = "#cfddc2"  # pale Moss, oklch(0.88 0.04 130)
TOP, BOTTOM = "#4b5f37", "#2a381c"  # deep Moss gradient, around oklch(0.42 0.06 130)


def outline(text):
    """Path data for `text`, centered on the 64 x 64 tile."""
    font = instantiateVariableFont(TTFont(FONT), {"wght": 700})
    glyphs, cmap, upm = font.getGlyphSet(), font.getBestCmap(), font["head"].unitsPerEm
    k = SIZE / upm
    names = [cmap[ord(c)] for c in text]
    width = sum(font["hmtx"][n][0] for n in names) * k + TRACK * (len(names) - 1)
    bounds = BoundsPen(glyphs)
    glyphs[cmap[ord("H")]].draw(bounds)
    x, base = (64 - width) / 2, 32 + bounds.bounds[3] * k / 2
    pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
    for n in names:
        glyphs[n].draw(TransformPen(pen, (k, 0, 0, -k, x, base)))
        x += font["hmtx"][n][0] * k + TRACK
    return pen.getCommands()


def svg(path, radius):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{TOP}"/>'
        f'<stop offset="1" stop-color="{BOTTOM}"/></linearGradient></defs>'
        f'<rect width="64" height="64" rx="{radius}" fill="url(#g)"/><path d="{path}" fill="{INK}"/></svg>\n'
    )


def png(source, size):
    return Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=source, width=size)))).convert("RGBA")


def main():
    path = outline(TEXT)
    tile = svg(path, 15)
    (ROOT / "static/favicon.svg").write_text(tile)
    png(tile, 48).save(ROOT / "static/favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    png(svg(path, 0), 180).convert("RGB").save(ROOT / "static/apple-touch-icon.png", optimize=True)


if __name__ == "__main__":
    main()
