import pytest
from conftest import site_paths


def real_pages(public_dir):
    out = []
    for p in site_paths():
        f = public_dir / p.lstrip("/") / ("index.html" if p.endswith("/") else "")
        if 'http-equiv="refresh"' not in f.read_text():
            out.append(p)
    return out


def test_pages(public_dir, site_url, page_factory):
    """Each page loads once; theme and width switch in place: no sideways scroll, no errors, and
    every code block in a post or note has a copy button."""
    page = page_factory()
    for path in real_pages(public_dir):
        page.errors.clear()
        page.goto(f"{site_url}{path}")
        if path.startswith(("/blog/", "/notebook/")):
            assert page.locator("pre .f-code-copy").count() == page.locator("pre").count(), path
        page.evaluate("document.fonts.ready.then(() => 1)")
        for theme in ("dark", "light"):
            page.evaluate(f"document.documentElement.dataset.theme = '{theme}'")
            for width in (390, 860, 1280):
                page.set_viewport_size({"width": width, "height": 900})
                sw, iw = page.evaluate("[document.documentElement.scrollWidth, innerWidth]")
                assert sw <= iw, f"sideways scroll on {path} {theme} {width}px"
        assert page.errors == [], (path, page.errors)


CONTRAST = """([sel]) => {
  // Paints every background from <html> down to the element, alpha included, so text on a
  // card or a tinted badge is measured against what is really behind it, then the text on top.
  // Also returns the element's height: contrast on something not drawn means nothing.
  const el = document.querySelector(sel);
  const x = document.createElement('canvas').getContext('2d', { willReadFrequently: true });
  const paint = (c) => { x.fillStyle = 'rgb(0 0 0 / 0)'; x.fillStyle = c; x.fillRect(0, 0, 1, 1); };
  const read = () => [...x.getImageData(0, 0, 1, 1).data].slice(0, 3);
  const chain = [];
  for (let n = el; n; n = n.parentElement) chain.unshift(n);
  paint('#fff');
  for (const n of chain) paint(getComputedStyle(n).backgroundColor);
  const bg = read();
  paint(getComputedStyle(el).color);
  const fg = read();
  const lum = (c) => { const [r, g, b] = c.map(v => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
  const [a, b] = [lum(fg), lum(bg)];
  return [(Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05), el.getBoundingClientRect().height];
}"""

# Site-owned text styles, by page; facet's own tokens on the plain page are covered by .f-meta,
# .site-lead and "article p" (fg-2 at two alphas, and the accent link color).
CONTRAST_TARGETS = {
    "/": [".site-lead"],
    "/blog/shell-upgrade/": [".f-meta", "article p"],
    "/projects/#grammar-mutator": [".site-pj-card .site-pj-star", ".site-pj-yr", ".site-pj-body p",
                                   ".site-pj-sheet .site-pj-star"],
    "/resume/": ["#experience .f-resume__date", "#experience .f-resume__org", "#experience .f-resume__loc",
                 "#experience .f-timeline p", ".site-rs-dissertation", ".f-pubs__venue", ".f-pubs__authors",
                 ".f-resume__skills dt", "#service .f-lines li > span:first-child"],
    "/blog/from-capture-to-query/": [".ffi-crossings .ffi-fn", ".ffi-crossings .ffi-where", ".ffi-life .ffi-side",
                                     ".ffi-life .is-fault .ffi-what", ".ffi-return", ".ffi-funnel .ffi-label"],
    "/blog/whole-program-bitcode/": [".bc-ledger .bc"],
    "/blog/beyond-single-bitcode-file/": [".substrate-card small", ".substrate-outputs span"],
}


@pytest.mark.parametrize("path", CONTRAST_TARGETS)
def test_text_contrast(site_url, page_factory, path):
    """Each page loads once and switches theme in place, with transitions off so no color is
    caught halfway; every target is drawn and reaches 4.5:1 in both themes."""
    page = page_factory()
    page.goto(f"{site_url}{path}")
    page.add_style_tag(content="*, ::before, ::after { transition: none !important; }")
    if "#" in path:
        page.wait_for_selector("dialog[open]")
    failures = []
    for theme in ("dark", "light"):
        page.evaluate(f"document.documentElement.dataset.theme = '{theme}'")
        for sel in CONTRAST_TARGETS[path]:
            ratio, height = page.evaluate(CONTRAST, [sel])
            if ratio < 4.5 or height <= 0:
                failures.append((sel, theme, round(ratio, 2), height))
    assert failures == [], (path, failures)


def test_only_facet_dist_is_published(public_dir):
    # ignored_static's "[!d]*" glob lets any new top-level facet entry starting with "d" through.
    assert sorted(p.name for p in (public_dir / "vendor/facet").iterdir()) == ["dist"]


def test_site_icons_are_linked_and_published(public_dir):
    head = (public_dir / "index.html").read_text()
    for name in ("favicon.ico", "favicon.svg", "apple-touch-icon.png"):
        assert f"/{name}" in head and (public_dir / name).is_file(), name


@pytest.mark.parametrize("path", ["/", "/blog/shell-upgrade/", "/projects/"])
def test_nav_fits_on_phones(site_url, page_factory, path):
    """The fixed nav pill holds every item, theme toggle included, without scrolling sideways."""
    page = page_factory(width=390, theme="light")  # "Light" is the toggle's widest label
    page.goto(f"{site_url}{path}")
    page.evaluate("document.fonts.ready.then(() => 1)")
    for width in (390, 360):
        page.set_viewport_size({"width": width, "height": 900})
        sw, cw = page.evaluate("(n => [n.scrollWidth, n.clientWidth])(document.querySelector('nav.f-nav'))")
        assert sw <= cw, (path, width, sw, cw)
        box = page.locator("[data-f-theme-toggle]").bounding_box()
        assert box["x"] >= 0 and box["x"] + box["width"] <= width, (path, width, box)
    btn = page.locator(".site-search-open")
    assert btn.get_attribute("aria-label") == "Search"
    btn.click()  # the magnifier still opens search
    page.wait_for_selector("#site-search[open]")
