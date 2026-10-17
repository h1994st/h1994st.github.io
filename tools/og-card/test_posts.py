"""uv run --with pytest --with pillow --with fonttools --with brotli pytest tools/og-card -q"""

import random
import subprocess
from pathlib import Path

from PIL import Image

import posts

ROOT = Path(__file__).resolve().parents[2]


def meta(**kw):
    base = {"title": "rllvm: From Capture to Query", "description": "A short description.",
            "date": "2026-09-21", "tags": ["LLVM", "Rust"], "extra": {}}
    base.update(kw)
    return base


def test_same_post_same_image():
    a = posts.render_post(meta(), "/blog/x/", None)
    b = posts.render_post(meta(), "/blog/x/", None)
    assert a.size == (1200, 630) and a.tobytes() == b.tobytes()


def test_other_post_or_seed_changes_the_gem():
    a = posts.render_post(meta(), "/blog/x/", None).tobytes()
    assert posts.render_post(meta(), "/blog/y/", None).tobytes() != a
    assert posts.render_post(meta(extra={"card_seed": 2}), "/blog/x/", None).tobytes() != a


def test_long_and_missing_descriptions():
    for m in (meta(description=""), meta(description="word " * 200), meta(title="T " * 80)):
        assert posts.render_post(m, "/blog/x/", None).size == (1200, 630)


def test_own_card_fit_and_fill_keep_the_left_side():
    own = Image.new("RGB", (1200, 630), (250, 10, 10))
    fit = posts.render_post(meta(extra={"card": "c.png"}), "/blog/x/", own)
    fill = posts.render_post(meta(extra={"card": "c.png", "card_fit": "fill"}), "/blog/x/", own)
    # the post's own image dominates the left side in both modes
    for im in (fit, fill):
        r, g, b = im.getpixel((300, 315))
        assert r > 200 and g < 80
    # fit leaves the right edge to the generated card; fill fades into it
    assert fit.getpixel((1080, 315))[0] < 150


def test_fit_keeps_the_whole_image_and_melts_from_its_edge():
    own = Image.new("RGB", (1200, 630), (250, 10, 10))
    fit = posts.render_post(meta(extra={"card": "c.png"}), "/blog/x/", own)
    # fitted to 70% of the inner card (1104 px wide): 773 x 406, from x = 48
    width = round(0.7 * (1200 - 96))
    # no pixel of the image itself fades, right up to its edge
    for f in (0.05, 0.5, 0.95):
        assert fit.getpixel((48 + round(f * width), 315)) == (250, 10, 10), f
    # past the edge, its last column melts into the card over ~10-15% of the card's width
    past = 48 + width + 0.06 * 1200
    r, g, b = fit.getpixel((round(past), 315))
    assert 60 < r < 250, r
    assert fit.getpixel((48 + width + round(0.16 * 1200), 315))[0] < 150


def test_the_gem_stays_inside_the_card():
    rnd = random.Random(1)
    for poly in posts.gem(rnd, posts.GEM_BOX):
        for x, y in poly:
            assert 620 <= x <= 1152 and 48 <= y <= 582


def test_many_gems_have_facets_and_stay_in_their_box():
    for seed in range(200):
        polys = posts.gem(random.Random(seed), posts.GEM_BOX)
        assert len(polys) >= 5, seed
        for poly in polys:
            assert len(poly) >= 3
            for x, y in poly:
                assert 620 <= x <= 1152 and 48 <= y <= 582, seed
    assert posts.GEM_BOX == (620, 48, 1152, 582)  # the card frame: the rounded mask crops the gem


def test_text_stays_left_of_the_gem_for_real_posts():
    """The longest real title and description (and the extremes) never cross x = 700."""
    metas = [posts.post_meta(p) for p in posts.post_paths(ROOT / "content")]
    longest_title = max(metas, key=lambda m: len(m["title"]))
    longest_desc = max(metas, key=lambda m: len(m["description"]))
    for m in (longest_title, longest_desc, meta(title="T " * 80, description="word " * 200),
              meta(title="Supercalifragilisticexpialidocious" * 3), meta(description=""),
              meta(tags=["Reverse Engineering", "Claude Code", "Static Analysis", "Rust"])):
        boxes = posts.text_boxes(m)
        assert boxes["title"], m["title"]
        for name, box in boxes.items():
            if name == "site":
                continue  # "shengtuo.me" sits at the bottom right by design
            for left, top, right, bottom in box:
                assert right <= 700, (name, m["title"])
                assert bottom <= 630 - 48, (name, m["title"])


def test_post_paths_and_urls():
    paths = posts.post_paths(ROOT / "content")
    names = {p.relative_to(ROOT / "content").as_posix() for p in paths}
    assert "blog/shell-upgrade.md" in names
    assert "blog/chromatron-remake/index.md" in names
    assert not any(n.endswith("_index.md") for n in names)
    urls = {posts.post_url(p, ROOT / "content") for p in paths}
    assert {"blog/shell-upgrade", "blog/chromatron-remake", "blog/htb/editor"} <= urls


def test_cli_writes_a_card_per_post(tmp_path):
    subprocess.run(["uv", "run", "--with", "pillow", "--with", "fonttools", "--with", "brotli",
                    "tools/og-card/posts.py", "--out", str(tmp_path)], cwd=ROOT, check=True)
    assert (tmp_path / "blog" / "shell-upgrade.png").is_file()
    assert (tmp_path / "blog" / "chromatron-remake.png").is_file()
    assert (tmp_path / "blog" / "htb" / "editor.png").is_file()
    assert Image.open(tmp_path / "blog" / "from-capture-to-query.png").size == (1200, 630)
