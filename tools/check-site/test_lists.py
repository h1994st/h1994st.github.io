def test_blog_list_groups_by_year_with_a_featured_post(site_url, page_factory):
    page = page_factory()
    page.goto(f"{site_url}/blog/")
    assert page.locator(".site-featured").count() == 1
    years = page.locator(".f-list__year > h2").all_inner_texts()
    assert years == sorted(years, reverse=True) and "2026" in years
    assert page.locator(".f-list__row").count() >= 10


def test_htb_list_shows_all_eight_posts(site_url, page_factory):
    page = page_factory()
    page.goto(f"{site_url}/blog/htb/")
    assert page.locator(".site-featured").count() == 1
    assert page.locator(".f-list__row").count() == 7


def test_old_page_urls_redirect(public_dir):
    for old in ("blog/page/2", "blog/page/3", "blog/htb/page/2"):
        html = (public_dir / old / "index.html").read_text()
        assert 'http-equiv="refresh"' in html, old
    sitemap = (public_dir / "sitemap.xml").read_text()
    assert "/blog/page/2/" not in sitemap


def test_tag_pages_list_posts(site_url, page_factory):
    page = page_factory()
    page.goto(f"{site_url}/tags/hackthebox/")
    assert page.locator(".f-list__row").count() == 8
