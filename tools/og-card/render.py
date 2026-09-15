#!/usr/bin/env python3
"""Regenerate static/card.png, the site-wide Open Graph / Twitter share image.

    uv run --with pillow tools/og-card/render.py

static/card.png overrides themes/duckquill/static/card.png -- the theme's own
"Duckquill" artwork. Without it, every share of every page shows someone else's
branding.

The design reuses the CRT treatment from themes/duckquill/sass/_crt.scss and the
accent colours from config.toml, so the card reads as part of the site. If
accent_color_dark changes there, change SAGE here.

Geometry below mirrors the CSS box model this was first prototyped in: each text
row is a line box of `font-size * line-height`, positioned by its vertical centre.
"""
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1200, 630
PAD_L, PAD_T = 88, 74

# --- palette (all derived from the site, none invented) ---------------------
SAGE = (146, 179, 165)        # accent_color_dark, #92b3a5
BODY = (179, 160, 143)        # lifted taupe; plain #918072 loses contrast here
GLOW_NEAR = (146, 179, 165)   # .crt pre --text-shadow-1
GLOW_FAR = (129, 195, 167)    # --text-shadow-2, hsl(154.5 35.7% 63.7%)
FOOT_BG, FOOT_FG = SAGE, (16, 33, 27)
GRAD = ((0.00, (0x35, 0x42, 0x3b)), (0.62, (0x17, 0x21, 0x1d)), (1.00, (0x0b, 0x10, 0x0e)))

FONTS = ["/System/Library/Fonts/Menlo.ttc", "/Library/Fonts/Menlo.ttc",
         "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"]


def font(size, bold=False):
    for path in FONTS:
        try:
            return ImageFont.truetype(path, size, index=1 if bold else 0)
        except OSError:
            continue
    raise SystemExit("No monospace font found; add one to FONTS in this script.")


def background():
    """CSS: radial-gradient(ellipse 120% 140% at 30% 34%, ...) -- per-pixel."""
    cx, cy, rx, ry = 0.30 * W, 0.34 * H, 1.20 * W, 1.40 * H
    px = bytearray(W * H * 3)
    for y in range(H):
        dy = ((y - cy) / ry) ** 2
        row = y * W * 3
        for x in range(W):
            t = (((x - cx) / rx) ** 2 + dy) ** 0.5
            t = 1.0 if t > 1.0 else t
            for i in range(len(GRAD) - 1):       # locate the stop pair
                t0, c0 = GRAD[i]
                t1, c1 = GRAD[i + 1]
                if t <= t1 or i == len(GRAD) - 2:
                    k = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
                    k = 0.0 if k < 0 else (1.0 if k > 1 else k)
                    o = row + x * 3
                    px[o] = int(c0[0] + (c1[0] - c0[0]) * k)
                    px[o + 1] = int(c0[1] + (c1[1] - c0[1]) * k)
                    px[o + 2] = int(c0[2] + (c1[2] - c0[2]) * k)
                    break
    return Image.frombytes("RGB", (W, H), bytes(px))


def tracked(draw, xy, text, fnt, fill, tracking=0.0):
    """Pillow has no letter-spacing; monospace makes it a fixed advance."""
    x, y = xy
    if not tracking:
        draw.text((x, y), text, font=fnt, fill=fill, anchor="lm")
        return
    adv = fnt.getlength("M") + tracking
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill, anchor="lm")
        x += adv


def main():
    img = background()

    # Text goes on its own layer so the CRT glow can be blurred from its alpha.
    glow_layer = Image.new("L", (W, H), 0)
    sharp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd, sd = ImageDraw.Draw(glow_layer), ImageDraw.Draw(sharp)

    f30, f104, f22 = font(30), font(104, bold=True), font(22)

    # Line boxes: y is the centre, matching `font-size * line-height` flow.
    rows = [
        # (y_centre, prompt, command, font, tracking, glows)
        (74 + 22.5, "~ $ ", "whoami", f30, 0.0, True),
        (289.4 + 22.5, "~ $ ", "whatis nu1lptr", f30, 0.0, True),
    ]
    for y, prompt, cmd, fnt, tr, glow in rows:
        px_ = PAD_L
        for text, alpha in ((prompt, 140), (cmd, 255)):      # .prompt is opacity .55
            col = SAGE + (alpha,)
            sd.text((px_, y), text, font=fnt, fill=col, anchor="lm")
            if glow:
                gd.text((px_, y), text, font=fnt, fill=alpha, anchor="lm")
            px_ += fnt.getlength(text)

    # The one bold element; everything else stays quiet.
    tracked(sd, (PAD_L, 186.2), "Shengtuo Hu", f104, SAGE + (255,), -0.03 * 104)
    tracked(gd, (PAD_L, 186.2), "Shengtuo Hu", f104, 255, -0.03 * 104)

    # p { text-shadow: none } -- deliberately not added to the glow layer.
    for i, line in enumerate(("Security researcher. Program analysis, LLVM,",
                              "fuzzing, and network security.")):
        sd.text((PAD_L, 357.65 + i * 46.5), line, font=f30, fill=BODY + (255,), anchor="lm")

    # Prompt + block cursor.
    sd.text((PAD_L, 487.9), "~ $", font=f30, fill=SAGE + (140,), anchor="lm")
    gd.text((PAD_L, 487.9), "~ $", font=f30, fill=140, anchor="lm")
    cx = PAD_L + f30.getlength("~ $ ")
    sd.rectangle([cx, 487.9 - 17, cx + 17, 487.9 + 17], fill=SAGE + (255,))
    gd.rectangle([cx, 487.9 - 17, cx + 17, 487.9 + 17], fill=255)

    # .crt pre text-shadow: 0 0 .25rem, 0 0 .75rem (CSS blur radius ~= 2*sigma)
    for sigma, colour, strength in ((1.5, GLOW_NEAR, 0.50), (5.0, GLOW_FAR, 1.00)):
        mask = glow_layer.filter(ImageFilter.GaussianBlur(sigma)).point(
            lambda v, s=strength: int(v * s))
        img.paste(Image.new("RGB", (W, H), colour), (0, 0), mask)
    img.paste(sharp, (0, 0), sharp)

    # .scanlines::before -- 2px on, 2px off, black at .16
    lines = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lines)
    for y in range(0, H, 4):
        ld.rectangle([0, y, W, y + 1], fill=(0, 0, 0, 41))
    img.paste(lines, (0, 0), lines)

    # tmux status line, not macOS traffic lights.
    foot_h = 52
    fd = ImageDraw.Draw(img)
    fd.rectangle([0, H - foot_h, W, H], fill=FOOT_BG)
    y = H - foot_h / 2
    fd.text((PAD_L, y), "[nu1lptr]", font=font(22, bold=True), fill=FOOT_FG, anchor="lm")
    fd.text((PAD_L + font(22, bold=True).getlength("[nu1lptr]  "), y), "1:zsh*",
            font=f22, fill=FOOT_FG, anchor="lm")
    fd.text((W - PAD_L, y), "shengtuo.me", font=f22, fill=FOOT_FG, anchor="rm")

    # The art is a narrow band of greens, so a 256-colour palette is lossless
    # to the eye and roughly halves the file.
    out = __import__("pathlib").Path(__file__).resolve().parents[2] / "static" / "card.png"
    img.quantize(colors=256, method=Image.MEDIANCUT,
                 dither=Image.FLOYDSTEINBERG).save(out, optimize=True)
    print(f"wrote {out.relative_to(out.parents[1])} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
