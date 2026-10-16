import tomllib

from conftest import ROOT


def resume_extra():
    text = (ROOT / "content/resume/index.md").read_text()
    return tomllib.loads(text.split("+++")[1])["extra"]


def test_resume_uses_the_facet_layout(site_url, page_factory):
    page = page_factory()
    page.goto(f"{site_url}/resume/")
    assert page.locator("main.f-resume .f-resume__head h1").inner_text() == "Shengtuo Hu"
    sections = page.locator(".f-resume__body nav.f-toc a").all_inner_texts()
    assert sections[:2] == ["Summary", "Experience"]
    assert page.locator("#experience .f-resume__entry").count() >= 3


def test_resume_prints_one_column_without_the_nav(site_url, page_factory):
    page = page_factory()
    page.goto(f"{site_url}/resume/")
    page.emulate_media(media="print")
    assert page.evaluate("getComputedStyle(document.querySelector('.f-resume__body nav.f-toc')).display") == "none"


def test_publications_alias_still_redirects(public_dir):
    assert 'http-equiv="refresh"' in (public_dir / "publications" / "index.html").read_text()


def test_resume_shows_every_entry_and_no_duty_bullets(site_url, page_factory):
    """Every generated entry is on the page; roles carry metadata and one summary line only."""
    r = resume_extra()
    page = page_factory()
    page.goto(f"{site_url}/resume/")
    text = page.locator("main").inner_text()
    for e in r["experience"]:
        for field in ("title", "org", "location", "start", "end", "summary"):
            assert e[field] in text, (field, e[field])
    for p in r["projects"]:
        assert p["name"] in text and p["summary"] in text, p["name"]
    for e in r["education"]:
        assert e["degree"] in text, e["degree"]
    for p in r["publications"]:
        assert p["title"] in text and p["venue"] in text, p["title"]
    for s in r["service"] + r["honors"]:
        assert s["text"] in text and s["years"] in text, s["text"]
    for s in r["skills"]:
        assert s["value"] in text, s["label"]
    assert page.locator("#experience .f-timeline > li").count() == len(r["experience"])
    assert page.locator(".f-resume__bullets, #experience li ul").count() == 0
    assert page.locator(".f-pubs > li").count() == len(r["publications"])


def test_resume_marks_the_section_in_view(site_url, page_factory):
    page = page_factory()
    page.goto(f"{site_url}/resume/")
    page.evaluate("document.getElementById('publications').scrollIntoView()")
    page.wait_for_function(
        "document.querySelector('.f-resume__body nav.f-toc a[aria-current]')?.hash === '#publications'"
    )


def test_resume_has_one_sticky_bar_on_phones(site_url, page_factory):
    """At 390px only the site nav and the section pill bar stick; no old .rs-* bar or sidebar."""
    page = page_factory(width=390)
    page.goto(f"{site_url}/resume/")
    page.evaluate("window.scrollTo(0, 1500)")
    sticky = page.evaluate(
        """[...document.querySelectorAll('body *')].filter(e => {
             const s = getComputedStyle(e);
             return (s.position === 'sticky' || s.position === 'fixed') && s.display !== 'none'
               && e.getBoundingClientRect().height > 0 && !e.closest('dialog');
           }).map(e => e.className)"""
    )
    assert len(sticky) <= 2, sticky
    assert page.locator(".rs-nav, .rs-side, script[src*='resume-nav']").count() == 0
