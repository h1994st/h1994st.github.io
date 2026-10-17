from pathlib import Path

URLS = (Path(__file__).parent / "urls.txt").read_text().split()


def test_every_old_url_still_answers(public_dir):
    missing = []
    for url in URLS:
        rel = url.lstrip("/")
        target = public_dir / rel
        if url.endswith("/"):
            target = target / "index.html"
        if not target.is_file():
            missing.append(url)
    assert missing == [], missing


def test_moved_urls_redirect_and_stay_out_of_the_sitemap(public_dir):
    for old in ("blog/page/2", "blog/page/3", "blog/htb/page/2", "publications"):
        html = (public_dir / old / "index.html").read_text()
        assert 'http-equiv="refresh"' in html, old
    sitemap = (public_dir / "sitemap.xml").read_text()
    assert "/page/" not in sitemap and "/publications/" not in sitemap
