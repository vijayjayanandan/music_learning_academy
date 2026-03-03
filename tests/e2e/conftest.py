import pytest
import subprocess
import time
import socket


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


@pytest.fixture(scope="session")
def live_server():
    """Start Django dev server for E2E tests."""
    port = 8002  # Use different port to avoid conflicts
    if is_port_in_use(port):
        # Server already running, reuse it
        yield f"http://localhost:{port}"
        return

    proc = subprocess.Popen(
        ["python", "manage.py", "runserver", str(port), "--noreload"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Wait for server to start
    for _ in range(30):
        if is_port_in_use(port):
            break
        time.sleep(0.5)
    else:
        proc.kill()
        raise RuntimeError("Django server failed to start")

    yield f"http://localhost:{port}"
    proc.terminate()
    proc.wait()


@pytest.fixture(scope="session")
def browser():
    """Launch Playwright browser."""
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    yield browser
    browser.close()
    pw.stop()


@pytest.fixture
def page(browser):
    """Create a new browser page for each test."""
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    yield page
    page.close()


@pytest.fixture
def screenshot_dir():
    """Return screenshot directory path."""
    import os
    d = os.path.join(os.path.dirname(__file__), "..", "..", "screenshots")
    os.makedirs(d, exist_ok=True)
    return d
