"""Browser tests: the real page in headless Chromium (Playwright), driven through the panel's shadow DOM.

Skipped, not failed, when Playwright or its Chromium is not installed:
    .venv/Scripts/pip install -r requirements-dev.txt && .venv/Scripts/python -m playwright install chromium
"""
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if os.environ.get("CI"):
    import playwright.sync_api as playwright   # in CI a missing Playwright is a failure, never a silent skip
else:
    playwright = pytest.importorskip("playwright.sync_api")


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def app_url():
    """One Streamlit server for the whole session, on a free port, killed at the end."""
    port = _free_port()
    proc = subprocess.Popen([sys.executable, "-m", "streamlit", "run", str(ROOT / "app.py"), "--server.port", str(port),
                             "--server.headless", "true", "--browser.gatherUsageStats", "false"],
                            cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen(url, timeout=2).read(1)
                break
            except Exception:
                time.sleep(1)
        else:
            raise RuntimeError("streamlit did not start")
        yield url
    finally:
        proc.terminate()
        proc.wait(timeout=10)


@pytest.fixture(scope="session")
def browser():
    with playwright.sync_playwright() as p:
        try:
            b = p.chromium.launch()   # Playwright's Chromium allows autoplay without a gesture, so play() resolves headless
        except Exception as e:
            # Locally, a missing browser download is a skip (install once with `playwright install chromium`).
            # Any other launch failure, and any failure in CI, is a failure: the browser layer must not vanish silently.
            if "Executable doesn't exist" in str(e) and not os.environ.get("CI"):
                pytest.skip("Chromium not installed for Playwright; run: python -m playwright install chromium")
            raise
        yield b
        b.close()


@pytest.fixture
def page(browser, app_url):
    """A fresh page on the app with the first curated item mounted."""
    pg = browser.new_page(viewport={"width": 1280, "height": 900})
    pg.goto(app_url)
    pg.locator(".s2s-play").wait_for(timeout=30000)   # CSS locators pierce the component's open shadow root
    yield pg
    pg.close()


PANEL_STATE = """() => {
  const root = [...document.querySelectorAll('*')].map(e => e.shadowRoot).find(r => r && r.querySelector('.s2s'));
  const vis = [...root.querySelectorAll('.s2s-video')].find(v => !v.hidden);
  return {
    status: root.querySelector('.s2s-status').textContent,
    button: root.querySelector('.s2s-play').textContent,
    gloss: root.querySelector('.s2s-gloss').textContent,
    badge: root.querySelector('.s2s-badge').textContent,
    note: root.querySelector('.s2s-note').textContent,
    card: root.querySelector('.s2s-textsign').hidden ? null : root.querySelector('.s2s-textsign').textContent,
    visible: vis ? {src: vis.src.split('/').pop(), t: vis.currentTime, paused: vis.paused, ready: vis.readyState} : null,
    allPaused: [...root.querySelectorAll('.s2s-video')].every(v => v.paused) && root.querySelector('.s2s-audio').paused,
    captions: [...root.querySelectorAll('.s2s-captions span')].map(s => ({text: s.firstChild ? s.firstChild.textContent.trim() : '', cls: s.className, missing: s.querySelector('s') ? s.querySelector('s').textContent.trim() : null})),
  };
}"""


@pytest.fixture
def state(page):
    return lambda: page.evaluate(PANEL_STATE)
