#!/usr/bin/env python3
"""Regenerate static/card.png, the site-wide share image (og:image) for every page that is not a
post: the home page, lists, the resume, the notebook.

    uv run --with pillow --with fonttools --with brotli tools/og-card/render.py

A text card in the post cards' style (posts.py draws both): role, name and a one-line lead on the
left of the deep Moss card, the home page's gem on the right. Edit this script, not the PNG; the
output is deterministic.
"""
import hashlib
import tomllib

from PIL import Image

from posts import H, ROOT, W, background, draw_text

_CONFIG = tomllib.loads((ROOT / "config.toml").read_text())
KICKER = f"{_CONFIG['extra']['author']['role'].upper()} · NU1LPTR"
LEAD = "Program analysis, LLVM, fuzzing, and network security. Palo Alto Networks; Ph.D. from Michigan."


def card():
    im = background(hashlib.sha256(b"/").digest())
    draw_text(im, KICKER, "Shengtuo Hu", LEAD, byline="Blog  ·  Projects  ·  Resume")
    return im.resize((W, H), Image.Resampling.LANCZOS)


if __name__ == "__main__":
    out = ROOT / "static" / "card.png"
    card().save(out, optimize=True)
    print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")
