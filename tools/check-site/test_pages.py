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
    """Each page loads once; theme and width switch in place: no sideways scroll, no errors."""
    page = page_factory()
    for path in real_pages(public_dir):
        page.errors.clear()
        page.goto(f"{site_url}{path}")
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
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}"""


@pytest.mark.parametrize("theme", ["dark", "light"])
@pytest.mark.parametrize("path, sel", [("/", ".site-lead"), ("/blog/shell-upgrade/", ".f-meta"),
                                       ("/blog/shell-upgrade/", "article p"),
                                       ("/projects/", ".site-pj-star"), ("/projects/", ".site-pj-yr"),
                                       ("/projects/", ".site-pj-body p"),
                                       ("/projects/#grammar-mutator", ".site-pj-sheet .site-pj-star"),
                                       ("/resume/", "#experience .f-resume__date"),
                                       ("/resume/", "#experience .f-resume__org"),
                                       ("/resume/", "#experience .f-resume__loc"),
                                       ("/resume/", "#experience .f-timeline p"),
                                       ("/resume/", ".site-rs-dissertation"),
                                       ("/resume/", ".f-pubs__venue"), ("/resume/", ".f-pubs__authors"),
                                       ("/resume/", ".f-resume__skills dt"),
                                       ("/resume/", "#service .f-lines li > span:first-child"),
                                       ("/blog/from-capture-to-query/", ".ffi-crossings .ffi-fn"),
                                       ("/blog/from-capture-to-query/", ".ffi-crossings .ffi-where"),
                                       ("/blog/from-capture-to-query/", ".ffi-life .ffi-side"),
                                       ("/blog/from-capture-to-query/", ".ffi-life .is-fault .ffi-what"),
                                       ("/blog/from-capture-to-query/", ".ffi-return"),
                                       ("/blog/from-capture-to-query/", ".ffi-funnel .ffi-label"),
                                       ("/blog/from-capture-to-query/", ".ffi-fig figcaption"),
                                       ("/blog/whole-program-bitcode/", ".bc-ledger .bc"),
                                       ("/blog/beyond-single-bitcode-file/", ".substrate-card small"),
                                       ("/blog/beyond-single-bitcode-file/", ".substrate-outputs span"),
                                       ("/blog/chromatron-remake/", ".f-gallery__label"),
                                       ("/blog/chromatron-remake/", ".site-video ~ .f-meta"),
                                       ("/notebook/", ".site-notebook-toc a")])
def test_text_contrast(site_url, page_factory, theme, path, sel):
    page = page_factory(theme=theme)
    page.goto(f"{site_url}{path}")
    page.wait_for_selector(sel, state="attached")
    ratio = page.evaluate(CONTRAST, [sel])
    assert ratio >= 4.5, (path, sel, theme, round(ratio, 2))


def test_reduced_motion_is_still(site_url, page_factory):
    page = page_factory(reduced_motion=True)
    page.goto(f"{site_url}/")
    page.wait_for_timeout(300)
    running = page.evaluate("document.getAnimations().filter(a => a.playState === 'running').length")
    assert running == 0


def test_only_facet_dist_is_published(public_dir):
    # ignored_static's "[!d]*" glob lets any new top-level facet entry starting with "d" through.
    assert sorted(p.name for p in (public_dir / "vendor/facet").iterdir()) == ["dist"]


def test_site_icons_are_linked_and_published(public_dir):
    head = (public_dir / "index.html").read_text()
    for name in ("favicon.ico", "favicon.svg", "apple-touch-icon.png"):
        assert f"/{name}" in head and (public_dir / name).is_file(), name


@pytest.mark.parametrize("width", [390, 360])
@pytest.mark.parametrize("path", ["/", "/blog/shell-upgrade/", "/projects/"])
def test_nav_fits_on_phones(site_url, page_factory, width, path):
    """The fixed nav pill holds every item, theme toggle included, without scrolling sideways."""
    page = page_factory(width=width, theme="light")  # "Light" is the toggle's widest label
    page.goto(f"{site_url}{path}")
    page.evaluate("document.fonts.ready.then(() => 1)")
    sw, cw = page.evaluate("(n => [n.scrollWidth, n.clientWidth])(document.querySelector('nav.f-nav'))")
    assert sw <= cw, (path, width, sw, cw)
    box = page.locator("[data-f-theme-toggle]").bounding_box()
    assert box["x"] >= 0 and box["x"] + box["width"] <= width, (path, width, box)
    btn = page.locator(".site-search-open")
    assert btn.get_attribute("aria-label") == "Search"
    btn.click()  # the magnifier still opens search
    page.wait_for_selector("#site-search[open]")
