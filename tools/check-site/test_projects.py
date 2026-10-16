from conftest import BASE_URL, serve_from_public


def test_projects_render_as_cards_with_a_sheet(site_url, page_factory):
    page = page_factory()
    page.goto(f"{site_url}/projects/")
    cards = page.locator(".site-pj-card")
    assert cards.count() >= 5
    page.locator(".site-pj-card[data-has-detail] h2").first.click()
    page.wait_for_selector("dialog.f-sheet[open]")
    page.keyboard.press("Escape")
    assert page.locator("dialog.f-sheet[open]").count() == 0


def test_filter_chips_filter(site_url, page_factory):
    page = page_factory()
    page.goto(f"{site_url}/projects/")
    page.locator(".site-pj-filter button").nth(1).click()
    visible = page.locator(".site-pj-card:visible").count()
    assert 0 < visible < page.locator(".site-pj-card").count()


def test_home_anchors_reach_their_cards(site_url, page_factory):
    """The home page links featured projects as /projects/#<id>; the hash opens that card's sheet."""
    page = page_factory()
    page.goto(f"{site_url}/projects/")
    for pid in ("rllvm", "grammar-mutator", "chromatron"):
        assert page.locator(f".site-pj-card#{pid}").count() == 1, pid
    page.goto(f"{site_url}/projects/#grammar-mutator")
    page.wait_for_selector("dialog.site-pj-sheet[open]")
    assert "Grammar-Mutator" in page.locator(".site-pj-sheet-body h2").inner_text()
    page.mouse.click(5, 5)  # the backdrop
    assert page.locator("dialog.f-sheet[open]").count() == 0
    assert page.evaluate("location.hash") == ""


def test_sheet_fits_a_phone(site_url, page_factory):
    page = page_factory(width=390)
    page.goto(f"{site_url}/projects/#rllvm")
    page.wait_for_selector("dialog.site-pj-sheet[open]")
    box = page.locator("dialog.site-pj-sheet").bounding_box()
    assert box["x"] >= 0 and box["x"] + box["width"] <= 390
    sw, cw = page.evaluate("(d => [d.scrollWidth, d.clientWidth])(document.querySelector('dialog.site-pj-sheet'))")
    assert sw <= cw


def test_hover_animations_are_still_under_reduced_motion(site_url, page_factory):
    page = page_factory(reduced_motion=True)
    page.goto(f"{site_url}/projects/")
    for pid in ("rllvm", "chromatron", "my-resume", "grammar-mutator"):
        page.locator(f"#{pid}").hover()
        page.wait_for_timeout(200)
        running = page.evaluate("document.getAnimations().filter(a => a.playState === 'running').length")
        assert running == 0, pid
        if pid == "rllvm":  # the typed command is shown whole, not left at zero width
            assert page.locator("#rllvm .site-pj-cmd").bounding_box()["width"] > 50


def test_touch_screens_see_the_details_hint(browser, site_url):
    """Hover is decoration: on a touch screen the Details control shows at rest."""
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)
    ctx.route(f"{BASE_URL}/**", serve_from_public)
    ctx.route("**googletagmanager.com/**", lambda r: r.fulfill(body="", content_type="text/javascript"))
    page = ctx.new_page()
    page.goto(f"{site_url}/projects/")
    hint = page.locator("#cairn .site-pj-hint")
    assert hint.evaluate("e => getComputedStyle(e).opacity") == "1"
    hint.tap()
    page.wait_for_selector("dialog.site-pj-sheet[open]")
    ctx.close()
