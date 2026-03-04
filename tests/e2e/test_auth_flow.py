import pytest
import os

from .conftest import _do_login, _remove_debug_toolbar, click_sidebar


@pytest.mark.e2e
class TestLoginFlow:
    def test_login_page_renders(self, e2e_server, page, screenshot_dir):
        page.goto(f"{e2e_server}/accounts/login/")
        page.wait_for_load_state("domcontentloaded")
        _remove_debug_toolbar(page)
        page.screenshot(path=os.path.join(screenshot_dir, "01_login_page.png"))
        assert page.is_visible("button:has-text('Sign In')")

    def test_login_success(self, e2e_server, owner_page, screenshot_dir):
        owner_page.goto(f"{e2e_server}/")
        owner_page.wait_for_load_state("networkidle")
        _remove_debug_toolbar(owner_page)
        owner_page.screenshot(path=os.path.join(screenshot_dir, "02_dashboard_after_login.png"))
        assert "/accounts/login" not in owner_page.url

    def test_login_failure_shows_error(self, e2e_server, page, screenshot_dir):
        page.goto(f"{e2e_server}/accounts/login/")
        page.wait_for_load_state("domcontentloaded")
        _remove_debug_toolbar(page)
        page.fill('input[name="username"]', 'admin@harmonymusic.com')
        page.fill('input[name="password"]', 'wrongpassword')
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        _remove_debug_toolbar(page)
        page.screenshot(path=os.path.join(screenshot_dir, "03_login_error.png"))
        assert page.is_visible(".alert-error") or page.is_visible(".alert")


@pytest.mark.e2e
class TestDashboardFlow:
    def test_admin_dashboard(self, e2e_server, owner_page, screenshot_dir):
        owner_page.goto(f"{e2e_server}/")
        owner_page.wait_for_load_state("networkidle")
        _remove_debug_toolbar(owner_page)
        owner_page.screenshot(path=os.path.join(screenshot_dir, "04_admin_dashboard.png"))
        assert "/accounts/login" not in owner_page.url

    def test_sidebar_navigation(self, e2e_server, owner_page, screenshot_dir):
        owner_page.goto(f"{e2e_server}/")
        owner_page.wait_for_load_state("networkidle")
        _remove_debug_toolbar(owner_page)
        owner_page.screenshot(path=os.path.join(screenshot_dir, "05_sidebar.png"))
        sidebar = owner_page.locator("aside")
        assert "Courses" in sidebar.inner_text()

    def test_navigate_to_courses(self, e2e_server, owner_page, screenshot_dir):
        owner_page.goto(f"{e2e_server}/")
        owner_page.wait_for_load_state("networkidle")
        _remove_debug_toolbar(owner_page)
        click_sidebar(owner_page, "Courses")
        owner_page.screenshot(path=os.path.join(screenshot_dir, "06_course_list.png"))
        assert "courses" in owner_page.url

    def test_navigate_to_sessions(self, e2e_server, owner_page, screenshot_dir):
        owner_page.goto(f"{e2e_server}/")
        owner_page.wait_for_load_state("networkidle")
        _remove_debug_toolbar(owner_page)
        click_sidebar(owner_page, "Live Sessions")
        owner_page.screenshot(path=os.path.join(screenshot_dir, "07_sessions_list.png"))
        assert "schedule" in owner_page.url

    def test_student_dashboard(self, e2e_server, student_page, screenshot_dir):
        student_page.goto(f"{e2e_server}/")
        student_page.wait_for_load_state("networkidle")
        _remove_debug_toolbar(student_page)
        student_page.screenshot(path=os.path.join(screenshot_dir, "08_student_dashboard.png"))
        assert "/accounts/login" not in student_page.url

    def test_mobile_view(self, e2e_server, browser, owner_storage, screenshot_dir):
        ctx = browser.new_context(storage_state=owner_storage, viewport={"width": 375, "height": 812})
        p = ctx.new_page()
        p.goto(f"{e2e_server}/")
        p.wait_for_load_state("networkidle")
        _remove_debug_toolbar(p)
        p.screenshot(path=os.path.join(screenshot_dir, "09_mobile_dashboard.png"))
        p.close()
        ctx.close()
