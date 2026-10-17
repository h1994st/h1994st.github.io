from conftest import BASE_URL, PUBLIC, serve_from_public, stub_third_party, third_party

CHROMATRON = "/blog/chromatron-remake/"


def test_notebook_contents_are_numbered_and_titles_clear_the_nav(site_url, page_factory):
    page = page_factory()
    for path in ["/notebook/", "/notebook/binary/"]:
        page.set_viewport_size({"width": 1280, "height": 900})
        page.goto(f"{site_url}{path}")
        if path == "/notebook/":
            links = page.locator(".site-notebook-toc a").all_inner_texts()
            assert links[0].startswith("1.") and any(t.startswith("1.1.") for t in links)
        for width in (1280, 390):
            page.set_viewport_size({"width": width, "height": 900})
            nav = page.locator("nav.f-nav").bounding_box()
            h1 = page.locator("main h1").bounding_box()
            assert h1["y"] >= nav["y"] + nav["height"], (path, width)


def test_404_draws_a_cat_and_its_search_button_opens_search(site_url, page_factory):
    """GitHub Pages serves /404.html at whatever path was asked for, so it must work from deep paths."""
    page = page_factory()
    deep = f"{site_url}/no/such/deep/page/"
    page.route(deep, lambda r: r.fulfill(status=404, path=str(PUBLIC / "404.html")))
    page.goto(deep)
    page.wait_for_selector(".f-empty__cat .cat")
    assert page.locator(".f-empty a.f-btn--primary").inner_text() == "Back to home"
    btn = page.locator(".f-empty .site-search-open")
    assert btn.is_visible()
    btn.click()
    page.wait_for_selector("#site-search[open]")
    page.fill("#site-search input", "bitcode")
    page.wait_for_selector(".site-search-results li")
    # The browser logs the document's own 404 status; nothing else may fail.
    assert [e for e in page.errors if "status of 404" not in e] == []


def test_chromatron_switches_looks(site_url, page_factory):
    page = page_factory()
    page.goto(f"{site_url}{CHROMATRON}")
    assert page.locator(".f-docs .f-toc a").count() >= 2  # posts get a TOC by default
    loaded = page.locator(".f-figure img, .f-gallery img").evaluate_all(
        "els => els.filter(e => e.checkVisibility()).map(e => e.complete && e.naturalWidth > 0)"
    )
    assert loaded and all(loaded)
    modern = page.locator('[data-f-variant="look:modern"]').first
    classic = page.locator('[data-f-variant="look:classic"]').first
    assert modern.is_visible() and not classic.is_visible()
    page.click('[data-f-variants="look"] label:has-text("Classic")')
    assert classic.is_visible() and not modern.is_visible()


def test_chromatron_switches_without_js(site_url, browser):
    ctx = browser.new_context(java_script_enabled=False, viewport={"width": 1280, "height": 900})
    ctx.route(third_party, stub_third_party)
    ctx.route(f"{BASE_URL}/**", serve_from_public)
    try:
        page = ctx.new_page()
        page.goto(f"{site_url}{CHROMATRON}")
        # facet's radio form switches in CSS alone: modern by default, classic after a click.
        assert page.locator('[data-f-variant="look:modern"]:visible').count() == 4
        assert page.locator('[data-f-variant="look:classic"]:visible').count() == 0
        page.click('[data-f-variants="look"] label:has-text("Classic")')
        assert page.locator('[data-f-variant="look:classic"]:visible').count() == 4
        assert page.locator('[data-f-variant="look:modern"]:visible').count() == 0
    finally:
        ctx.close()
