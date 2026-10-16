"""Smoke tests for the built site. Run: uv run --with pytest --with playwright pytest tools/check-site -q"""

import base64
import functools
import http.server
import re
import subprocess
import threading
import tomllib
import urllib.parse
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "public"
BASE_URL = tomllib.loads((ROOT / "config.toml").read_text())["base_url"].rstrip("/")
# The GitHub Pages project sites served under this domain (/rllvm/, ...), from the one list
# templates/robots.txt keeps. Their files are not in this build, so tests stub them.
PROJECT_SITES = set(
    re.findall(r'"([^"]+)"', re.search(r"for project in \[(.*?)\]", (ROOT / "templates/robots.txt").read_text())[1])
)
PIXEL = base64.b64decode("R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==")


def serve_from_public(route):
    """Answer a live-site URL from public/, or 404. Never the network: a file only the live
    site still has must not pass. Project-site URLs get a 1x1 GIF instead."""
    rel = urllib.parse.unquote(urllib.parse.urlsplit(route.request.url).path).lstrip("/")
    if rel.split("/")[0] in PROJECT_SITES:
        route.fulfill(body=PIXEL, content_type="image/gif")
        return
    target = PUBLIC / rel
    if target.is_dir():
        target = target / "index.html"
    if target.is_file() and PUBLIC in target.resolve().parents:
        route.fulfill(path=str(target))
    else:
        route.fulfill(status=404, body="")


def site_paths():
    return sorted(
        "/" + p.relative_to(PUBLIC).as_posix().removesuffix("index.html")
        for p in PUBLIC.rglob("*.html")
        if "vendor" not in p.relative_to(PUBLIC).parts
    )


@pytest.fixture(scope="session")
def public_dir():
    subprocess.run(["zola", "build"], cwd=ROOT, check=True, capture_output=True)
    return PUBLIC


@pytest.fixture(scope="session")
def site_url(public_dir):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    handler = functools.partial(Quiet, directory=str(public_dir))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.fixture
def page_factory(browser):
    contexts = []

    def make(width=1280, theme="dark", reduced_motion=False):
        ctx = browser.new_context(
            viewport={"width": width, "height": 900},
            reduced_motion="reduce" if reduced_motion else "no-preference",
        )
        ctx.add_init_script(f"try{{localStorage.setItem('facet-theme','{theme}')}}catch{{}}")
        # Never reach Google from tests.
        ctx.route("**googletagmanager.com/**", lambda r: r.fulfill(body="", content_type="text/javascript"))
        # YouTube embeds log their own errors into the page's console; stub the iframe.
        ctx.route("**youtube-nocookie.com/**", lambda r: r.fulfill(body="", content_type="text/html"))
        # get_url() makes absolute links to the live site; serve those from this build.
        ctx.route(f"{BASE_URL}/**", serve_from_public)
        page = ctx.new_page()
        page.errors = []
        page.on("pageerror", lambda e: page.errors.append(str(e)))
        page.on("console", lambda m: m.type == "error" and page.errors.append(m.text))
        contexts.append(ctx)
        return page

    yield make
    for c in contexts:
        c.close()
