"""Site search: the facet sheet, its keyboard shortcuts, and escaped results."""


def open_search(page, site_url):
    page.goto(f"{site_url}/")
    page.keyboard.press("/")
    page.wait_for_selector("#site-search[open]")


def test_slash_opens_and_escape_closes(site_url, page_factory):
    page = page_factory()
    open_search(page, site_url)
    page.keyboard.press("Escape")
    assert page.locator("#site-search[open]").count() == 0


def test_title_matches_rank_first(site_url, page_factory):
    page = page_factory()
    open_search(page, site_url)
    page.fill("#site-search input", "bitcode")
    page.wait_for_selector(".site-search-results li")
    assert "itcode" in page.locator(".site-search-results li a").first.inner_text()


def test_search_escapes_and_matches_bodies(site_url, page_factory):
    page = page_factory()
    open_search(page, site_url)
    page.fill("#site-search input", "<script>")
    page.wait_for_timeout(200)
    assert page.locator(".site-search-results script").count() == 0
    page.fill("#site-search input", "zzzzqqq")
    page.wait_for_timeout(200)
    assert "No results" in page.locator(".site-search-status").inner_text()
    assert page.errors == []


def test_arrows_move_through_results(site_url, page_factory):
    page = page_factory()
    open_search(page, site_url)
    page.fill("#site-search input", "rllvm")
    page.wait_for_selector(".site-search-results li")
    page.keyboard.press("ArrowDown")
    assert page.evaluate("document.activeElement === document.querySelector('.site-search-results a')")
    page.keyboard.press("ArrowUp")
    assert page.evaluate("document.activeElement === document.querySelector('#site-search input')")


def test_slash_ignored_while_typing_or_with_modifier(site_url, page_factory):
    page = page_factory()
    page.goto(f"{site_url}/")
    page.evaluate("document.body.insertAdjacentHTML('beforeend', '<div id=ce contenteditable>x</div>')")
    page.focus("#ce")
    page.keyboard.press("/")
    assert page.locator("#site-search[open]").count() == 0
    page.evaluate("document.activeElement.blur()")
    page.keyboard.press("Control+/")
    assert page.locator("#site-search[open]").count() == 0


def test_open_sheet_fits_and_scrolls_inside(site_url, page_factory):
    for width in (390, 1280):
        page = page_factory(width=width, reduced_motion=True)
        open_search(page, site_url)
        page.fill("#site-search input", "e")
        page.wait_for_selector(".site-search-results li")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        box = page.locator("#site-search").bounding_box()
        assert box["y"] >= 0 and box["y"] + box["height"] <= page.viewport_size["height"]
        res = page.locator(".site-search-results")
        assert res.evaluate("el => getComputedStyle(el).overflowY") in ("auto", "scroll")
