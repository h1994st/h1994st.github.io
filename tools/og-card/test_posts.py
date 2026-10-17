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


def test_the_gem_stays_inside_the_card():
    rnd = random.Random(1)
    for poly in posts.gem(rnd, (620, 60, 1140, 570)):
        for x, y in poly:
            assert 600 <= x <= 1160 and 40 <= y <= 590


def test_many_gems_have_facets_and_stay_in_their_box():
    for seed in range(200):
        polys = posts.gem(random.Random(seed), (620, 60, 1140, 570))
        assert len(polys) >= 5, seed
        for poly in polys:
            assert len(poly) >= 3
            for x, y in poly:
                assert 620 <= x <= 1140 and 60 <= y <= 570, seed


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
