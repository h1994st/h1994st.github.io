"""Generate the Chromatron Remake post's architecture diagram (wide + tall).

The diagram is drawn as a Chromatron board: each stage is a game tile, the
original game is white light, the Rust engine is a prism that splits it into
the Mac (red) and browser (blue) targets, and my feedback is a green beam.
Both themes and the animation live inside the SVG (prefers-color-scheme,
prefers-reduced-motion), because the post embeds it with <img>.

Run from the repo root: python3 tools/chromatron-post/arch.py
"""

from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "content/blog/chromatron-remake"

STYLE = """
  <style>
    svg {
      --p1: #ffffff; --p2: #f1f3f9; --p3: #e7eaf3; --edge: rgba(27,35,64,.10);
      --grid: #1b2340; --grid-o: .06;
      --tile1: #ffffff; --tile1-o: .95; --tile2: #eef1f8; --tile2-o: .95; --tile-edge: rgba(27,35,64,.16);
      --ink: #1b2340; --sub: #5b6585; --key: #46506e;
      --white: #9aa4c4; --red: #f0213a; --green: #08b85a; --blue: #2457ff; --spark: #f2a900;
      --hot-white: #5c6890; --hot-red: #b8001c; --hot-green: #00813d; --hot-blue: #0a35c8;
      --glow-o: .28;
    }
    @media (prefers-color-scheme: dark) {
      svg {
        --p1: #1a2142; --p2: #0b0d18; --p3: #06070b; --edge: rgba(220,230,255,.06);
        --grid: #96aaff; --grid-o: .07;
        --tile1: #aabeff; --tile1-o: .12; --tile2: #788cdc; --tile2-o: .03; --tile-edge: rgba(220,230,255,.16);
        --ink: #e1e8ff; --sub: #a9b6dc; --key: #a9b6dc;
        --white: #ffffff; --red: #ff2234; --green: #18ff76; --blue: #2860ff; --spark: #ffe23c;
        --hot-white: #ffffff; --hot-red: #ffc8c4; --hot-green: #d2ffe2; --hot-blue: #d6e2ff;
        --glow-o: .45;
      }
    }
    text { font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif; }
    .name { fill: var(--ink); font-size: 14px; font-weight: 750; }
    .sub { fill: var(--sub); font-size: 12px; font-weight: 500; }
    .key { fill: var(--key); font-size: 12px; font-weight: 500; }
    .s1 { stop-color: var(--p1); } .s2 { stop-color: var(--p2); } .s3 { stop-color: var(--p3); }
    .t1 { stop-color: var(--tile1); stop-opacity: var(--tile1-o); }
    .t2 { stop-color: var(--tile2); stop-opacity: var(--tile2-o); }
    .gridline { stroke: var(--grid); stroke-opacity: var(--grid-o); }
    .panel-edge { fill: none; stroke: var(--edge); }
    .tile { fill: url(#glass); stroke: var(--tile-edge); }
    .icon { fill: none; stroke: var(--ink); stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
    .icon-fill { fill: var(--ink); }
    .spark { fill: var(--spark); }
    .glow { fill: none; stroke-width: 9; stroke-linecap: round; opacity: var(--glow-o); filter: url(#blur); }
    .core { fill: none; stroke-width: 2.6; stroke-linecap: round; }
    .photon { fill: none; stroke-width: 4.5; stroke-linecap: round; stroke-dasharray: 2 34;
              animation: flow 1.6s linear infinite; }
    .white { stroke: var(--white); } .red { stroke: var(--red); } .green { stroke: var(--green); } .blue { stroke: var(--blue); }
    .photon.white { stroke: var(--hot-white); } .photon.red { stroke: var(--hot-red); }
    .photon.green { stroke: var(--hot-green); } .photon.blue { stroke: var(--hot-blue); }
    .ring { fill: none; stroke-width: 2.6; }
    .halo { animation: pulse 2.4s ease-in-out infinite; }
    .rays { stroke-width: 2; stroke-linecap: round; animation: pulse 2.4s ease-in-out infinite; }
    .twinkle { animation: pulse 1.8s ease-in-out infinite; }
    @keyframes flow { to { stroke-dashoffset: -36; } }
    @keyframes pulse { 0%, 100% { opacity: .35; } 50% { opacity: 1; } }
    @media (prefers-reduced-motion: reduce) {
      .photon, .halo, .rays, .twinkle { animation: none; }
    }
  </style>"""


def defs(w, h):
    return f"""
  <defs>
    <radialGradient id="panel" cx="45%" cy="35%" r="80%">
      <stop class="s1" offset="0"/><stop class="s2" offset=".55"/><stop class="s3" offset="1"/>
    </radialGradient>
    <linearGradient id="glass" x1="0" y1="0" x2="0" y2="1">
      <stop class="t1" offset="0"/><stop class="t2" offset="1"/>
    </linearGradient>
    <pattern id="grid" width="36" height="36" patternUnits="userSpaceOnUse">
      <path class="gridline" d="M36 0H0V36" fill="none"/>
    </pattern>
    <filter id="blur" filterUnits="userSpaceOnUse" x="0" y="0" width="{w}" height="{h}">
      <feGaussianBlur stdDeviation="4"/>
    </filter>
  </defs>
  <rect width="{w}" height="{h}" rx="18" fill="url(#panel)"/>
  <rect width="{w}" height="{h}" rx="18" fill="url(#grid)"/>
  <rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="17.5" class="panel-edge"/>"""


def beam(d, colour):
    return (f'\n  <path class="glow {colour}" d="{d}"/>'
            f'\n  <path class="core {colour}" d="{d}"/>'
            f'\n  <path class="photon {colour}" d="{d}"/>')


def tile(cx, cy, s=64):
    h = s / 2
    return f'\n  <rect class="tile" x="{cx-h}" y="{cy-h}" width="{s}" height="{s}" rx="14"/>'


def label(x, y, name, sub, anchor="middle"):
    out = f'\n  <text class="name" x="{x}" y="{y}" text-anchor="{anchor}">{name}</text>'
    for i, line in enumerate(sub):
        out += f'\n  <text class="sub" x="{x}" y="{y + 18 + 15 * i}" text-anchor="{anchor}">{line}</text>'
    return out


# --- icons, each drawn around (cx, cy) inside a ~32px box -------------------

def old_mac(cx, cy):
    return (f'\n  <rect class="icon" x="{cx-12}" y="{cy-15}" width="24" height="30" rx="3.5"/>'
            f'\n  <rect class="icon" x="{cx-8}" y="{cy-11}" width="16" height="12" rx="1.5"/>'
            f'\n  <path class="icon" d="M{cx+1} {cy+8}H{cx+7}"/>'
            f'\n  <circle class="spark twinkle" cx="{cx-5}" cy="{cy+8}" r="1.6"/>')


def magnifier(cx, cy):
    return (f'\n  <circle class="icon" cx="{cx-3}" cy="{cy-3}" r="10"/>'
            f'\n  <path class="icon" d="M{cx+4.5} {cy+4.5}L{cx+13} {cy+13}" stroke-width="3"/>'
            f'\n  <text class="icon-fill" x="{cx-3}" y="{cy+0.5}" text-anchor="middle" '
            f'font-size="8.5" font-weight="800" font-family="ui-monospace, Menlo, monospace">01</text>')


def terminal(cx, cy):
    return (f'\n  <rect class="icon" x="{cx-15}" y="{cy-11}" width="30" height="23" rx="3.5"/>'
            f'\n  <path class="icon" d="M{cx-9} {cy-3}L{cx-4} {cy+1.5}L{cx-9} {cy+6}M{cx-1} {cy+6}H{cx+6}"/>'
            f'\n  <path class="spark twinkle" d="M{cx+14} {cy-22}l2.2 5.3 5.3 2.2-5.3 2.2-2.2 5.3-2.2-5.3-5.3-2.2 5.3-2.2z"/>')


def prism(cx, cy):
    return (f'\n  <path class="icon" d="M{cx} {cy-15}L{cx+15} {cy+11}H{cx-15}Z" stroke-width="2"/>'
            f'\n  <path class="icon" d="M{cx-3} {cy-6}L{cx+5} {cy+8}" stroke-opacity=".35"/>')


def target(cx, cy, colour):
    rays = "".join(
        f"M{cx + dx * 15} {cy + dy * 15}L{cx + dx * 20} {cy + dy * 20}"
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (.71, .71), (-.71, .71), (.71, -.71), (-.71, -.71)))
    return (f'\n  <circle class="glow {colour} halo" cx="{cx}" cy="{cy}" r="10"/>'
            f'\n  <circle class="ring {colour}" cx="{cx}" cy="{cy}" r="10"/>'
            f'\n  <circle class="{colour}" cx="{cx}" cy="{cy}" r="3.5" style="fill: var(--{colour}); stroke: none"/>'
            f'\n  <path class="rays {colour}" d="{rays}"/>')


def controller(cx, cy):
    return (f'\n  <path class="icon" d="M{cx-11} {cy-9}H{cx+11}a7 7 0 0 1 7 6.5l1 7.5a4.5 4.5 0 0 1-8 3.2l-3.2-3.7H{cx-8.2}'
            f'l-3.2 3.7a4.5 4.5 0 0 1-8-3.2l1-7.5A7 7 0 0 1 {cx-11} {cy-9}Z"/>'
            f'\n  <path class="icon" d="M{cx-11} {cy-1}h7M{cx-7.5} {cy-4.5}v7"/>'
            f'\n  <circle class="icon-fill" cx="{cx+6}" cy="{cy-2.5}" r="1.9"/>'
            f'\n  <circle class="icon-fill" cx="{cx+10}" cy="{cy+1.5}" r="1.9"/>')


def legend(x, y):
    out = ""
    for i, (colours, text) in enumerate([(["white"], "white light: the original game"),
                                         (["red", "blue"], "red and blue: what came out"),
                                         (["green"], "green: me, playing and reporting back")]):
        yy = y + 24 * i
        if len(colours) == 1:
            out += f'\n  <path class="core {colours[0]}" d="M{x} {yy}H{x+24}"/>'
        else:
            out += f'\n  <path class="core red" d="M{x} {yy}H{x+10}"/>\n  <path class="core blue" d="M{x+14} {yy}H{x+24}"/>'
        out += f'\n  <text class="key" x="{x+34}" y="{yy+4}">{text}</text>'
    return out


TITLE = """
  <title id="t">How Chromatron Remake was made</title>
  <desc id="d">Drawn as a Chromatron board. White light from the original PowerPC app passes through Ghidra, which decompiles it, and Claude Code, which reads it and writes the Rust. The Rust engine is a prism that splits the light into a red beam lighting the four Mac apps and a blue beam lighting the browser version. A green beam runs from the browser to me as the player, and from me back to Claude Code as feedback.</desc>"""


def wide():
    w, h = 760, 400
    s = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">{TITLE}{STYLE}{defs(w, h)}'
    y1, y2 = 124, 286
    # beams under the tiles
    s += beam(f"M108 {y1}H216", "white") + beam(f"M280 {y1}H388", "white") + beam(f"M452 {y1}H560", "white")
    s += beam(f"M624 {y1}H680", "red") + beam(f"M592 {y1+32}V{y2-32}", "blue")
    s += beam(f"M560 {y2}H452", "green") + beam(f"M420 {y2-32}V{y1+32}", "green")
    # row 1: labels above the tiles, so vertical beams below stay clear
    for cx, name, sub in [(76, "Chromatron.app", ["PowerPC, 2003"]), (248, "Ghidra", ["decompiles it"]),
                          (420, "Claude Code", ["reads it, writes Rust"]), (592, "Rust engine", ["one for all four"]),
                          (712, "4 Mac apps", ["Apple Silicon"])]:
        s += label(cx, 50, name, sub)
    s += tile(76, y1) + old_mac(76, y1)
    s += tile(248, y1) + magnifier(248, y1)
    s += tile(420, y1) + terminal(420, y1)
    s += tile(592, y1) + prism(592, y1)
    s += tile(712, y1) + target(712, y1, "red")
    # row 2
    s += tile(592, y2) + target(592, y2, "blue")
    s += tile(420, y2) + controller(420, y2)
    s += label(592, y2 + 56, "In the browser", ["phones too"])
    s += label(420, y2 + 56, "Me", ["playing it"])
    s += legend(40, 262)
    return s + "\n</svg>\n"


def tall():
    w, h = 360, 700
    s = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">{TITLE}{STYLE}{defs(w, h)}'
    x = 60
    ys = [60, 170, 280, 390]
    bottom = 520
    s += beam(f"M{x} 92V138", "white") + beam(f"M{x} 202V248", "white") + beam(f"M{x} 312V358", "white")
    s += beam(f"M{x-8} 422V{bottom-32}", "red")
    s += beam(f"M{x+12} 422V452H200V{bottom-32}", "blue")
    s += beam(f"M232 {bottom}H278", "green")
    s += beam(f"M310 {bottom-32}V236H84V248", "green")
    for y, name, sub, icon in [(ys[0], "Chromatron.app", ["PowerPC, 2003"], old_mac),
                               (ys[1], "Ghidra", ["decompiles it"], magnifier),
                               (ys[2], "Claude Code", ["reads it, writes Rust"], terminal),
                               (ys[3], "Rust engine", ["one for all four games"], prism)]:
        s += tile(x, y) + icon(x, y) + label(104, y - 2, name, sub, "start")
    s += tile(x, bottom) + target(x, bottom, "red")
    s += tile(200, bottom) + target(200, bottom, "blue")
    s += tile(310, bottom) + controller(310, bottom)
    s += label(x, bottom + 56, "4 Mac apps", ["Apple Silicon"])
    s += label(200, bottom + 56, "Browser", ["phones too"])
    s += label(310, bottom + 56, "Me", ["playing it"])
    s += legend(24, 630)
    return s + "\n</svg>\n"


open(f"{OUT}/how-wide.svg", "w").write(wide())
open(f"{OUT}/how-tall.svg", "w").write(tall())
