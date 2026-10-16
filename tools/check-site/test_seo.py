import json
import re

from conftest import site_paths

SAME_AS = [
    "https://github.com/h1994st",
    "https://scholar.google.com/citations?user=VOefXMMAAAAJ",
    "https://dblp.org/pid/203/0829.html",
    "https://www.linkedin.com/in/shengtuo/",
    "https://x.com/ShengtuoHu",
    "https://www.instagram.com/hst_nullderef/",
]


def read(public_dir, path):
    return (public_dir / path.lstrip("/") / ("index.html" if path.endswith("/") else "")).read_text()


def ld_blocks(html):
    return [json.loads(m) for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)]


def is_redirect(html):
    return 'http-equiv="refresh"' in html


def test_every_page_has_its_head(public_dir):
    for path in site_paths():
        html = read(public_dir, path)
        if is_redirect(html):
            continue
        for needle in ('<link rel="canonical"', 'property="og:title"', 'property="og:image"',
                       'name="description"', 'name="twitter:card"', "data-accent=\"moss\"",
                       'data-f-ga4="G-ZMH6NLL7C7"', "/vendor/facet/dist/facet.css"):
            assert needle in html, (path, needle)
        assert re.search(r"<title>[^<]+</title>", html), path


def test_home_person_keeps_every_profile(public_dir):
    person = next(b for b in ld_blocks(read(public_dir, "/")) if b["@type"] == "ProfilePage")["mainEntity"]
    assert person["name"] == "Shengtuo Hu"
    assert person["alternateName"] == "nu1lptr"
    assert sorted(person["sameAs"]) == sorted(SAME_AS)


def test_dated_pages_are_blog_postings(public_dir):
    html = read(public_dir, "/blog/shell-upgrade/")
    post = next(b for b in ld_blocks(html) if b["@type"] == "BlogPosting")
    assert post["author"]["@id"].endswith("/#person")
