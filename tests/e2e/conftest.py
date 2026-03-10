import asyncio
import os
import sys
import pytest
import subprocess
import time
import socket

# Windows requires ProactorEventLoop for Playwright subprocess spawning
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Allow Django ORM calls from ProactorEventLoop context (E2E tests don't use test DB)
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


@pytest.fixture(scope="session")
def e2e_server():
    """Start Django dev server for E2E tests.

    Named e2e_server to override pytest-django's built-in (which tries
    to create a test database). Our E2E tests hit an externally-running
    dev server and don't need a test DB.
    """
    port = int(os.environ.get("E2E_PORT", "8001"))
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


def _remove_debug_toolbar(page):
    """Remove Django Debug Toolbar from DOM entirely."""
    page.evaluate("document.getElementById('djDebug')?.remove()")


def _do_login(page, server, email, password):
    """Perform login on a page."""
    page.goto(f"{server}/accounts/login/")
    page.wait_for_load_state("domcontentloaded")
    _remove_debug_toolbar(page)
    page.fill('input[name="username"]', email)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    _remove_debug_toolbar(page)


def click_sidebar(page, text):
    """Click a sidebar link, scoped to <aside> to avoid debug toolbar matches."""
    page.locator(f"aside a:has-text('{text}')").click()
    page.wait_for_load_state("networkidle")
    _remove_debug_toolbar(page)


# --- Session-scoped authenticated contexts (login once per persona) ---


def _create_auth_context(browser, server, email, password):
    """Login once, save auth state, return a reusable context factory."""
    context = browser.new_context(viewport={"width": 1280, "height": 720})
    page = context.new_page()
    _do_login(page, server, email, password)
    storage = context.storage_state()
    page.close()
    context.close()
    return storage


@pytest.fixture(scope="session")
def owner_storage(browser, e2e_server):
    return _create_auth_context(
        browser, e2e_server, "admin@harmonymusic.com", "admin123"
    )


@pytest.fixture(scope="session")
def instructor_storage(browser, e2e_server):
    return _create_auth_context(
        browser, e2e_server, "sarah@harmonymusic.com", "instructor123"
    )


@pytest.fixture(scope="session")
def student_storage(browser, e2e_server):
    return _create_auth_context(browser, e2e_server, "alice@example.com", "student123")


@pytest.fixture
def page(browser):
    """Create a new browser page for each test (unauthenticated)."""
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    yield page
    page.close()


@pytest.fixture
def owner_page(browser, owner_storage):
    """Page pre-authenticated as owner."""
    ctx = browser.new_context(
        storage_state=owner_storage, viewport={"width": 1280, "height": 720}
    )
    page = ctx.new_page()
    yield page
    page.close()
    ctx.close()


@pytest.fixture
def instructor_page(browser, instructor_storage):
    """Page pre-authenticated as instructor."""
    ctx = browser.new_context(
        storage_state=instructor_storage, viewport={"width": 1280, "height": 720}
    )
    page = ctx.new_page()
    yield page
    page.close()
    ctx.close()


@pytest.fixture
def student_page(browser, student_storage):
    """Page pre-authenticated as student."""
    ctx = browser.new_context(
        storage_state=student_storage, viewport={"width": 1280, "height": 720}
    )
    page = ctx.new_page()
    yield page
    page.close()
    ctx.close()


@pytest.fixture
def screenshot_dir():
    """Return screenshot directory path."""
    import os

    d = os.path.join(os.path.dirname(__file__), "..", "..", "screenshots")
    os.makedirs(d, exist_ok=True)
    return d
