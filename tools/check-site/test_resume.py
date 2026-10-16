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


def test_resume_prints_link_targets(site_url, page_factory):
    """On paper, body links are underlined and publication and project links spell out their URL."""
    page = page_factory()
    page.goto(f"{site_url}/resume/")
    page.emulate_media(media="print")
    for sel in (".f-pubs a.f-chip", "#projects a.f-chip"):
        href, after, line = page.eval_on_selector(
            sel, "a => [a.href, getComputedStyle(a, '::after').content, getComputedStyle(a).textDecorationLine]")
        assert after == f'" ({href})"' and line == "underline", (sel, after, line)
    assert page.eval_on_selector(".f-resume__contact a", "a => getComputedStyle(a, '::after').content") == "none"


def test_publications_alias_still_redirects(public_dir):
    assert 'http-equiv="refresh"' in (public_dir / "publications" / "index.html").read_text()


HREFS = "el => [...el.querySelectorAll('a')].map(a => a.getAttribute('href'))"


def entries(page, selector, items):
    """Each generated item next to the text and link hrefs of its own rendered entry, so a field
    can only be satisfied by its own entry, not by the same words elsewhere on the page."""
    rows = page.locator(selector)
    assert rows.count() == len(items), selector
    return [(item, rows.nth(i).inner_text(), rows.nth(i).evaluate(HREFS)) for i, item in enumerate(items)]


def test_resume_renders_every_generated_field(site_url, page_factory):
    """Every field of the generated [extra] reaches the page, in the entry it belongs to."""
    r = resume_extra()
    page = page_factory()
    page.goto(f"{site_url}/resume/")
    head = page.locator(".f-resume__head")
    assert r["headline"] in head.inner_text()
    assert head.locator(".f-resume__contact").evaluate(HREFS) == [c["url"] for c in r["contact"]]
    assert head.locator(".f-resume__contact").inner_text().split("\n")[: len(r["contact"])] == [
        c["label"] for c in r["contact"]
    ]
    summary = page.locator("#summary").inner_text()
    assert r["summary"] in summary
    assert page.locator(".f-resume__skills dt").all_inner_texts() == [s["label"] for s in r["skills"]]
    assert page.locator(".f-resume__skills dd").all_inner_texts() == [s["value"] for s in r["skills"]]

    def check(selector, items, fields):
        for item, text, hrefs in entries(page, selector, items):
            for f in fields:
                if f in item:
                    assert item[f] in text, (selector, f, item[f])
            if "award" in item:
                assert item["award"] in text, (selector, item["award"])
            expected = ([item["org_url"]] if "org_url" in item else []) + [l["url"] for l in item.get("links", [])]
            assert hrefs == expected, (selector, hrefs)
            for l in item.get("links", []):
                assert l["label"] in text, (selector, l["label"])

    check("#experience .f-timeline > li", r["experience"], ("title", "org", "location", "start", "end", "summary"))
    check("#projects .f-timeline > li", r["projects"], ("name", "org", "start", "end", "summary"))
    check("#education .f-timeline > li", r["education"],
          ("degree", "org", "location", "start", "end", "dissertation"))
    check(".f-pubs > li", r["publications"], ("title", "authors", "venue"))
    check("#service .f-lines > li", r["service"], ("text", "years"))
    check("#honors .f-lines > li", r["honors"], ("text", "years"))
    # The site owner's name is bold in every author list that has it, the way facet styles it.
    name = page.locator(".f-resume__head h1").inner_text()
    for item, li in zip(r["publications"], page.locator(".f-pubs > li").all()):
        if name in item["authors"]:
            assert li.locator(".f-pubs__authors b").inner_text() == name, item["title"]


def test_resume_roles_have_no_duty_bullets(site_url, page_factory):
    """Roles carry metadata and one summary line only."""
    page = page_factory()
    page.goto(f"{site_url}/resume/")
    assert page.locator(".f-resume__bullets, #experience li ul").count() == 0
    assert page.locator("#experience .f-timeline > li p").count() <= len(resume_extra()["experience"])


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
