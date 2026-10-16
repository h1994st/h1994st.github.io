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
  const rgb = (c) => { const x = document.createElement('canvas').getContext('2d');
    x.fillStyle = getComputedStyle(document.body).backgroundColor; x.fillRect(0, 0, 1, 1);
    x.fillStyle = c; x.fillRect(0, 0, 1, 1); return [...x.getImageData(0, 0, 1, 1).data].slice(0, 3); };
  const lum = (c) => { const [r, g, b] = c.map(v => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
  const fg = lum(rgb(getComputedStyle(document.querySelector(sel)).color));
  const bg = lum(rgb(getComputedStyle(document.body).backgroundColor));
  return (Math.max(fg, bg) + 0.05) / (Math.min(fg, bg) + 0.05);
}"""


@pytest.mark.parametrize("theme", ["dark", "light"])
@pytest.mark.parametrize("path, sel", [("/", ".site-lead"), ("/blog/shell-upgrade/", ".f-meta"),
                                       ("/blog/shell-upgrade/", "article p")])
def test_text_contrast(site_url, page_factory, theme, path, sel):
    page = page_factory(theme=theme)
    page.goto(f"{site_url}{path}")
    if page.locator(sel).count():
        assert page.evaluate(CONTRAST, [sel]) >= 4.5, (path, sel, theme)


def test_reduced_motion_is_still(site_url, page_factory):
    page = page_factory(reduced_motion=True)
    page.goto(f"{site_url}/")
    page.wait_for_timeout(300)
    running = page.evaluate("document.getAnimations().filter(a => a.playState === 'running').length")
    assert running == 0
