def test_lists(site_url, page_factory):
    """The blog groups by year under a featured post; the HTB section and its tag list every writeup."""
    page = page_factory()
    page.goto(f"{site_url}/blog/")
    assert page.locator(".site-featured").count() == 1
    years = page.locator(".f-list__year > h2").all_inner_texts()
    assert years == sorted(years, reverse=True) and "2026" in years
    assert page.locator(".f-list__row").count() >= 10
    page.goto(f"{site_url}/blog/htb/")
    assert page.locator(".site-featured").count() == 1
    assert page.locator(".f-list__row").count() == 7  # plus the featured one: all eight
    page.goto(f"{site_url}/tags/hackthebox/")
    assert page.locator(".f-list__row").count() == 8
