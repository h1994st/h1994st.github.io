import json
import tomllib

from conftest import ROOT


def test_home_renders_its_sections_with_a_shuffled_intro(site_url, page_factory):
    page = page_factory()
    # Math.random() == 0 makes the inline Fisher-Yates shuffle a fixed, non-identity permutation.
    page.add_init_script("Math.random = () => 0")
    page.goto(f"{site_url}/")
    assert page.locator(".site-hero h1").inner_text() == "Shengtuo Hu"
    assert page.locator(".site-hero .site-crt pre").count() == 1
    built = tomllib.loads((ROOT / "content/_index.md").read_text().split("+++")[1])["extra"]["intro"]
    shown = json.loads(page.locator(".site-intro [data-f-type]").get_attribute("data-f-type"))
    assert len(built) >= 2 and sorted(shown) == sorted(built) and shown != built
    assert page.locator(".site-intro [aria-hidden='true'] [data-f-type]").count() == 1
    assert page.locator(".site-writing .f-list__row").count() == 5
    assert page.locator(".site-projects li").count() == 3
    assert "Who am I" in page.locator(".site-about").inner_text()


def test_home_has_no_motion_under_reduced_motion(site_url, page_factory):
    page = page_factory(reduced_motion=True)
    page.clock.install()
    page.goto(f"{site_url}/")
    page.wait_for_timeout(300)
    running = page.evaluate("document.getAnimations().filter(a => a.playState === 'running').length")
    assert running == 0
    typed = page.locator(".site-intro [data-f-type]")
    phrases, text = json.loads(typed.get_attribute("data-f-type")), typed.inner_text()
    page.clock.run_for(3000)  # past the typewriter's 2.5 s hold: the next phrase, whole, not typed
    assert typed.inner_text() != text and typed.inner_text() in phrases


def test_crt_art_fits_without_scrolling(site_url, page_factory):
    page = page_factory()
    page.goto(f"{site_url}/")
    for width in (1280, 390):
        page.set_viewport_size({"width": width, "height": 900})
        sw, cw = page.evaluate(
            "(() => { const e = document.querySelector('.site-hero .site-crt pre'); return [e.scrollWidth, e.clientWidth]; })()"
        )
        assert sw <= cw + 1, (width, sw, cw)
    # Every glyph, the block art included, comes from facet's Geist Mono: a system fallback
    # (Consolas on Windows) has other widths and heights and breaks the art apart.
    page.evaluate("document.fonts.ready")
    cdp = page.context.new_cdp_session(page)
    root = cdp.send("DOM.getDocument")["root"]["nodeId"]
    pre = cdp.send("DOM.querySelector", {"nodeId": root, "selector": ".site-hero .site-crt pre"})["nodeId"]
    cdp.send("CSS.enable")
    fonts = {f["familyName"] for f in cdp.send("CSS.getPlatformFontsForNode", {"nodeId": pre})["fonts"]}
    assert fonts == {"Geist Mono"}, fonts
