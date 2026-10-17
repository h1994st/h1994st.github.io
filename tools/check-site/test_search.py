"""Site search: the facet sheet, its keyboard shortcuts, and escaped results."""

import json


def open_search(page, site_url):
    page.goto(f"{site_url}/")
    page.keyboard.press("/")
    page.wait_for_selector("#site-search[open]")


def test_search_by_keyboard(site_url, page_factory):
    """/ opens search unless typing or with a modifier, Escape closes it; title matches rank first;
    arrows move between the input and the results; no match says so."""
    page = page_factory()
    page.goto(f"{site_url}/")
    page.evaluate("document.body.insertAdjacentHTML('beforeend', '<div id=ce contenteditable>x</div>')")
    page.focus("#ce")
    page.keyboard.press("/")
    assert page.locator("#site-search[open]").count() == 0
    page.evaluate("document.getElementById('ce').remove()")
    page.keyboard.press("Control+/")
    assert page.locator("#site-search[open]").count() == 0
    page.keyboard.press("/")
    page.wait_for_selector("#site-search[open]")
    page.keyboard.press("Escape")
    # Closed, and focus has left the input, so "/" is no longer typed into it.
    page.wait_for_function("(d => !d.open && !d.contains(document.activeElement))(document.getElementById('site-search'))")
    page.keyboard.press("/")
    page.wait_for_selector("#site-search[open]")
    page.fill("#site-search input", "bitcode")
    page.wait_for_selector(".site-search-results li")
    assert "itcode" in page.locator(".site-search-results li a").first.inner_text()
    page.keyboard.press("ArrowDown")
    assert page.evaluate("document.activeElement === document.querySelector('.site-search-results a')")
    page.keyboard.press("ArrowUp")
    assert page.evaluate("document.activeElement === document.querySelector('#site-search input')")
    page.fill("#site-search input", "zzzzqqq")
    page.wait_for_function("document.querySelector('.site-search-status').textContent.includes('No results')")
    assert page.errors == []


def test_open_sheet_fits_and_scrolls_inside(site_url, page_factory):
    page = page_factory(width=390, reduced_motion=True)
    open_search(page, site_url)
    for width in (390, 1280):
        page.set_viewport_size({"width": width, "height": 900})
        page.fill("#site-search input", "e")
        page.wait_for_selector(".site-search-results li")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), width
        box = page.locator("#site-search").bounding_box()
        assert box["y"] >= 0 and box["y"] + box["height"] <= page.viewport_size["height"], width
        res = page.locator(".site-search-results")
        assert res.evaluate("el => getComputedStyle(el).overflowY") in ("auto", "scroll")
        page.fill("#site-search input", "editor")
        page.wait_for_selector(".site-search-results li")
        assert res.evaluate("el => el.scrollWidth <= el.clientWidth"), width


STUB_URL = "**/search_index.en.json"


def test_index_failure_reports_and_retries(site_url, page_factory):
    page = page_factory()
    page.route(STUB_URL, lambda r: r.fulfill(status=500, body="nope"))
    open_search(page, site_url)
    page.fill("#site-search input", "bitcode")
    page.wait_for_function("document.querySelector('.site-search-status').textContent.includes('unavailable')")
    assert "Search unavailable" in page.locator(".site-search-status").inner_text()
    page.unroute(STUB_URL)
    page.fill("#site-search input", "bitcod")
    page.wait_for_selector(".site-search-results li")
    # The browser itself logs the 500 as a console error; anything else (an uncaught rejection) fails.
    assert [e for e in page.errors if "status of 500" not in e] == []


def test_results_are_escaped(site_url, page_factory):
    doc = {
        "url": "https://shengtuo.me/",
        "title": 'Zork <img src=x onerror="window.__x=1"> &amp;',
        "description": "",
        "body": 'a zork body <img src=x onerror="window.__x=1"> &amp; end',
    }
    page = page_factory()
    page.route(STUB_URL, lambda r: r.fulfill(body=json.dumps([doc]), content_type="application/json"))
    open_search(page, site_url)
    page.fill("#site-search input", "zork")
    page.wait_for_selector(".site-search-results li")
    page.wait_for_timeout(200)
    assert page.locator(".site-search-results img").count() == 0
    assert page.evaluate("window.__x") is None
    assert "<img" in page.locator(".site-search-results a").first.inner_text()
    assert "&amp;" in page.locator(".site-search-results p").first.inner_text()
