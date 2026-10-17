import json
import re

from conftest import BASE_URL, PROJECT_SITES, ROOT, site_paths

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


def og_image(html):
    return re.search(r'property="og:image" content="([^"]+)"', html)[1]


def test_posts_are_blog_postings_with_a_real_share_image(public_dir):
    """Every post is a BlogPosting by the home page's Person. With generated cards (as CI builds),
    every post points at its own card and that card is published; without them, posts fall back
    to their own card, else the site card."""
    posts = {}
    for path in site_paths():
        html = read(public_dir, path)
        post = next((b for b in ld_blocks(html) if b["@type"] == "BlogPosting"), None)
        if post and not is_redirect(html):
            assert post["author"]["@id"].endswith("/#person"), path
            posts[path] = og_image(html)
    assert {"/blog/shell-upgrade/", "/blog/chromatron-remake/", "/blog/htb/editor/"} <= posts.keys()
    for path, url in posts.items():
        assert url.startswith(f"{BASE_URL}/"), (path, url)
        rel = url.removeprefix(f"{BASE_URL}/")
        assert rel.split("/")[0] in PROJECT_SITES or (public_dir / rel).is_file(), (path, url)
    if any((ROOT / "static" / "cards").rglob("*.png")):
        for path, url in posts.items():
            assert url == f"{BASE_URL}/cards{path.rstrip('/')}.png", (path, url)
    else:
        assert not any("/cards/" in url for url in posts.values())
        assert posts["/blog/chromatron-remake/"] == f"{BASE_URL}/blog/chromatron-remake/card.png"
        assert posts["/blog/from-capture-to-query/"] == f"{BASE_URL}/rllvm/assets/images/social-card.png"
        assert posts["/blog/shell-upgrade/"] == posts["/blog/htb/editor/"] == f"{BASE_URL}/card.png"
