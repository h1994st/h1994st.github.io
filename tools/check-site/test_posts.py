from conftest import site_paths

CLIPBOARD = ["clipboard-read", "clipboard-write"]


def test_post_layouts_and_share(site_url, page_factory):
    """A post with a TOC gets the docs layout and the dated header, and Share falls back to copying
    the link; the TOC follows the scroll; toc = false gets the reading layout."""
    page = page_factory()
    page.context.grant_permissions(CLIPBOARD)
    page.add_init_script("delete navigator.share")
    page.goto(f"{site_url}/blog/shell-upgrade/")
    assert page.locator(".f-docs .f-toc a").count() >= 2
    assert page.locator(".f-docs article h1").inner_text()
    # The scroll spy marks the section in view (it only follows same-page "#id" links).
    last = page.locator(".f-docs .f-toc a").last.get_attribute("href")
    page.evaluate("id => document.getElementById(id).scrollIntoView()", last.removeprefix("#"))
    page.wait_for_function("h => document.querySelector('.f-toc a[aria-current]')?.getAttribute('href') === h", arg=last)
    meta = page.locator(".site-post-meta").inner_text()
    assert "min read" in meta and "2025" in meta
    page.click(".site-share")
    assert page.evaluate("navigator.clipboard.readText()").endswith("/blog/shell-upgrade/")
    page.goto(f"{site_url}/misc/")
    assert page.locator("main.f-reading").count() == 1


def test_copy_button_copies_without_line_numbers(site_url, page_factory):
    page = page_factory()
    page.context.grant_permissions(CLIPBOARD)
    page.goto(f"{site_url}/notebook/binary/memory-registers/")
    page.locator("pre .f-code-copy").first.click()
    lines = page.evaluate("navigator.clipboard.readText()").splitlines()
    assert lines[0] == "pwndbg> info proc mappings"
    assert lines[1] == "process 67443"


def test_backlinks_list_pages_linking_here(public_dir):
    # whole-program-bitcode links to the rllvm posts; at least one post shows a backlinks list.
    pages = [public_dir / p.lstrip("/") / "index.html" for p in site_paths() if not p.endswith(".html")]
    hits = [f for f in pages if f.is_file() and "site-backlinks" in f.read_text()]
    assert hits
