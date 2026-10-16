import json

from conftest import BASE_URL, serve_from_public


def test_hero_has_name_banner_and_typed_intro(site_url, page_factory):
    page = page_factory()
    page.goto(f"{site_url}/")
    assert page.locator(".site-hero h1").inner_text() == "Shengtuo Hu"
    assert page.locator(".site-hero .site-crt pre").count() == 1
    phrases = json.loads(page.locator(".site-intro [data-f-type]").get_attribute("data-f-type"))
    assert len(phrases) >= 2
    assert page.locator(".site-intro [aria-hidden='true'] [data-f-type]").count() == 1


def test_intro_order_is_shuffled(browser, site_url):
    orders = set()
    for _ in range(8):
        ctx = browser.new_context()
        ctx.route(f"{BASE_URL}/**", serve_from_public)
        page = ctx.new_page()
        page.goto(f"{site_url}/")
        orders.add(page.locator(".site-intro [data-f-type]").get_attribute("data-f-type"))
        ctx.close()
    assert len(orders) > 1


def test_writing_and_projects(site_url, page_factory):
    page = page_factory()
    page.goto(f"{site_url}/")
    assert page.locator(".site-writing .f-list__row").count() == 5
    assert page.locator(".site-projects li").count() == 3
    assert "Who am I" in page.locator(".site-about").inner_text()


def test_hero_still_without_motion(site_url, page_factory):
    page = page_factory(reduced_motion=True)
    page.goto(f"{site_url}/")
    text = page.locator(".site-intro [data-f-type]").inner_text()
    page.wait_for_timeout(3000)
    assert page.locator(".site-intro [data-f-type]").inner_text() == text
