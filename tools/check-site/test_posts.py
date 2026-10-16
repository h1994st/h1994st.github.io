from conftest import BASE_URL, serve_from_public, site_paths

POST_WITH_TOC = "/blog/shell-upgrade/"
POST_PLAIN = "/misc/"


def test_toc_posts_use_the_docs_layout(site_url, page_factory):
    page = page_factory()
    page.goto(f"{site_url}{POST_WITH_TOC}")
    assert page.locator(".f-docs .f-toc a").count() >= 2
    assert page.locator(".f-docs article h1").inner_text()


def test_toc_false_uses_the_reading_layout(site_url, page_factory):
    page = page_factory()
    page.goto(f"{site_url}{POST_PLAIN}")
    assert page.locator("main.f-reading").count() == 1


def test_chromatron_gets_the_default_toc(site_url, page_factory):
    page = page_factory()
    page.goto(f"{site_url}/blog/chromatron-remake/")
    assert page.locator(".f-docs .f-toc a").count() >= 2


def test_post_header_has_date_reading_time_and_tags(site_url, page_factory):
    page = page_factory()
    page.goto(f"{site_url}{POST_WITH_TOC}")
    meta = page.locator(".site-post-meta").inner_text()
    assert "min read" in meta and "2025" in meta


def test_code_blocks_have_copy_buttons(public_dir, site_url, page_factory):
    page = page_factory()
    for path in [p for p in site_paths() if p.startswith(("/blog/", "/notebook/")) and p.count("/") >= 3]:
        page.goto(f"{site_url}{path}")
        blocks = page.locator("pre").count()
        assert page.locator("pre .f-code-copy").count() == blocks, path


def test_copy_button_copies(browser, site_url):
    ctx = browser.new_context(permissions=["clipboard-read", "clipboard-write"])
    ctx.route(f"{BASE_URL}/**", serve_from_public)  # get_url() assets are absolute
    page = ctx.new_page()
    page.goto(f"{site_url}{POST_WITH_TOC}")
    page.locator("pre .f-code-copy").first.click()
    copied = page.evaluate("navigator.clipboard.readText()")
    assert copied.strip() and copied.strip() in page.locator("pre").first.inner_text()
    ctx.close()


def test_share_falls_back_to_copying_the_link(browser, site_url):
    ctx = browser.new_context(permissions=["clipboard-read", "clipboard-write"])
    ctx.route(f"{BASE_URL}/**", serve_from_public)  # get_url() assets are absolute
    page = ctx.new_page()
    page.add_init_script("delete navigator.share")
    page.goto(f"{site_url}{POST_WITH_TOC}")
    page.click(".site-share")
    assert page.evaluate("navigator.clipboard.readText()").endswith(POST_WITH_TOC)
    ctx.close()


def test_backlinks_list_pages_linking_here(public_dir):
    # whole-program-bitcode links to the rllvm posts; at least one post shows a backlinks list.
    pages = [public_dir / p.lstrip("/") / "index.html" for p in site_paths() if not p.endswith(".html")]
    hits = [f for f in pages if f.is_file() and "site-backlinks" in f.read_text()]
    assert hits


def test_copy_omits_line_numbers(browser, site_url):
    ctx = browser.new_context(permissions=["clipboard-read", "clipboard-write"])
    ctx.route(f"{BASE_URL}/**", serve_from_public)
    page = ctx.new_page()
    page.goto(f"{site_url}/notebook/binary/memory-registers/")
    page.locator("pre .f-code-copy").first.click()
    lines = page.evaluate("navigator.clipboard.readText()").splitlines()
    assert lines[0] == "pwndbg> info proc mappings"
    assert lines[1] == "process 67443"
    ctx.close()
