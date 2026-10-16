import re
from pathlib import Path

from conftest import BASE_URL, serve_from_public

ROOT = Path(__file__).resolve().parents[2]
CSS = ROOT / "static" / "css"
DUCKQUILL = r"var\(--(accent-color|contrast-color|fg-color|bg-color|fg-muted-\d|font-size-(x-)?small|font-monospace-code|font-system-ui|font-transitional|container-width)\)"
CHROMATRON = "/blog/chromatron-remake/"
DIAGRAM_POSTS = ["whole-program-bitcode", "beyond-single-bitcode-file", "from-capture-to-query"]
# The Chromatron screenshots' alt texts, which the facet rewrite must keep word for word.
CHROMATRON_ALTS = [
    f"Chromatron{n}, level {lvl} solved, in the {look} look"
    for n, lvl in [("", 46), (" 2", 22), (" 3", 41), (" 4", 21)]
    for look in ("modern", "classic")
]


def test_notebook_is_a_docs_page_with_numbered_contents(site_url, page_factory):
    page = page_factory()
    page.goto(f"{site_url}/notebook/")
    links = page.locator(".site-notebook-toc a").all_inner_texts()
    assert links[0].startswith("1.") and any(t.startswith("1.1.") for t in links)


def test_notebook_contents_are_a_plain_nested_list(site_url, page_factory):
    page = page_factory()
    page.goto(f"{site_url}/notebook/")
    outer, inner = page.evaluate(
        """() => ['.site-notebook-toc > ul', '.site-notebook-toc ul ul'].map(s => {
             const cs = getComputedStyle(document.querySelector(s));
             return [cs.listStyleType, parseFloat(cs.paddingLeft)];
           })"""
    )
    assert outer == ["none", 0] and inner[0] == "none" and inner[1] > 0


def test_notebook_title_clears_the_nav(site_url, page_factory):
    for width in (390, 1280):
        page = page_factory(width=width)
        for path in ["/notebook/", "/notebook/binary/"]:
            page.goto(f"{site_url}{path}")
            nav = page.locator("nav.f-nav").bounding_box()
            h1 = page.locator("main h1").bounding_box()
            assert h1["y"] >= nav["y"] + nav["height"], (path, width)


def test_404_is_the_empty_layout(public_dir):
    html = (public_dir / "404.html").read_text()
    assert "f-empty" in html and "f-empty__cat" in html


def test_404_draws_a_cat_and_its_search_button_opens_search(site_url, page_factory):
    page = page_factory()
    page.goto(f"{site_url}/404.html")
    page.wait_for_selector(".f-empty__cat .cat")
    home = page.locator(".f-empty a.f-btn--primary")
    assert home.inner_text() == "Back to home"
    btn = page.locator(".f-empty .site-search-open")
    assert btn.is_visible()
    btn.click()
    page.wait_for_selector("#site-search[open]")
    assert page.errors == []


def test_no_duckquill_variables_left():
    for f in CSS.glob("*.css"):
        assert not re.search(DUCKQUILL, f.read_text()), f.name


def test_post_stylesheets_are_folded_into_facet():
    assert not (CSS / "notebook.css").exists()
    assert not (CSS / "chromatron-post.css").exists()
    assert "styles" not in (ROOT / "content/blog/chromatron-remake/index.md").read_text()
    for f in ["_index.md", "binary/_index.md", "ddia/_index.md"]:
        assert "styles" not in (ROOT / "content/notebook" / f).read_text(), f


def test_chromatron_switches_looks(site_url, page_factory):
    page = page_factory()
    page.goto(f"{site_url}{CHROMATRON}")
    modern = page.locator('[data-f-variant="look:modern"]').first
    classic = page.locator('[data-f-variant="look:classic"]').first
    assert modern.is_visible() and not classic.is_visible()
    page.click('[data-f-variants="look"] [data-variant="classic"]')
    assert classic.is_visible() and not modern.is_visible()


def test_chromatron_without_js_shows_modern_and_no_dead_control(site_url, browser):
    ctx = browser.new_context(java_script_enabled=False, viewport={"width": 1280, "height": 900})
    ctx.route(f"{BASE_URL}/**", serve_from_public)
    try:
        page = ctx.new_page()
        page.goto(f"{site_url}{CHROMATRON}")
        assert page.locator('[data-f-variants="look"]').is_hidden()
        assert page.locator('[data-f-variant="look:modern"]:visible').count() == 4
        assert page.locator('[data-f-variant="look:classic"]:visible').count() == 0
    finally:
        ctx.close()


def test_chromatron_keeps_its_images_and_alt_texts(site_url, page_factory):
    page = page_factory()
    page.goto(f"{site_url}{CHROMATRON}")
    alts = page.locator(".f-gallery img").evaluate_all("els => els.map(e => e.alt)")
    assert alts == CHROMATRON_ALTS
    labels = page.locator(".f-gallery__label").all_inner_texts()
    assert labels == ["Chromatron", "Chromatron 2", "Chromatron 3", "Chromatron 4"]
    assert page.locator("figure.f-figure.f-figure--bare").count() == 2
    assert page.locator("figure.f-figure picture source").count() == 1
    assert page.locator(".site-video + p.f-meta, .site-video ~ p.f-meta").count() >= 1
    loaded = page.locator(".f-figure img, .f-gallery img").evaluate_all(
        "els => els.filter(e => !e.hidden).map(e => e.complete && e.naturalWidth > 0)"
    )
    assert loaded and all(loaded)


def test_diagram_figures_use_facet_figures(public_dir):
    for slug in DIAGRAM_POSTS:
        html = (public_dir / "blog" / slug / "index.html").read_text()
        figs = re.findall(r'<figure class="([^"]*)"', html)
        assert figs and all("f-figure" in c.split() for c in figs), (slug, figs)
        assert not re.search(r'class="(ffi|substrate)-kicker"', html), slug


def test_diagram_figures_keep_their_structure(site_url, page_factory):
    page = page_factory()
    checks = {
        "whole-program-bitcode": [(".bc-ledger li", 5), (".bc-graph .node", 4)],
        "beyond-single-bitcode-file": [(".substrate-card", 2), (".substrate-outputs span", 3)],
        "from-capture-to-query": [(".ffi-crossings li", 3), (".ffi-life .ffi-step", 4), (".ffi-funnel .ffi-rung", 4)],
    }
    for slug, sels in checks.items():
        page.goto(f"{site_url}/blog/{slug}/")
        for sel, n in sels:
            assert page.locator(sel).count() == n, (slug, sel)
            assert page.locator(sel).first.bounding_box()["height"] > 0, (slug, sel)
