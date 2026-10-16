"""Smoke tests for the built site. Run: uv run --with pytest --with playwright pytest tools/check-site -q"""

import functools
import http.server
import subprocess
import threading
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "public"


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
        page = ctx.new_page()
        page.errors = []
        page.on("pageerror", lambda e: page.errors.append(str(e)))
        page.on("console", lambda m: m.type == "error" and page.errors.append(m.text))
        contexts.append(ctx)
        return page

    yield make
    for c in contexts:
        c.close()
