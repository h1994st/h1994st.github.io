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
