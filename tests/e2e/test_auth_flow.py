import pytest
import os


@pytest.mark.e2e
class TestLoginFlow:
    def test_login_page_renders(self, live_server, page, screenshot_dir):
        page.goto(f"{live_server}/accounts/login/")
        page.screenshot(path=os.path.join(screenshot_dir, "01_login_page.png"))

        assert page.title() == "Login - Music Academy"
        assert page.is_visible("text=Music Academy")
        assert page.is_visible("text=Sign in to your account")
        assert page.is_visible("button:has-text('Sign In')")

    def test_login_success(self, live_server, page, screenshot_dir):
        page.goto(f"{live_server}/accounts/login/")
        page.fill('input[name="username"]', 'admin@harmonymusic.com')
        page.fill('input[name="password"]', 'admin123')
        page.click('button[type="submit"]')
        page.wait_for_url("**/dashboard/**", timeout=5000)
        page.screenshot(path=os.path.join(screenshot_dir, "02_dashboard_after_login.png"))

        assert "dashboard" in page.url
        assert page.is_visible("text=Harmony Music School")

    def test_login_failure_shows_error(self, live_server, page, screenshot_dir):
        page.goto(f"{live_server}/accounts/login/")
        page.fill('input[name="username"]', 'admin@harmonymusic.com')
        page.fill('input[name="password"]', 'wrongpassword')
        page.click('button[type="submit"]')
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(screenshot_dir, "03_login_error.png"))

        assert page.is_visible(".alert-error")


@pytest.mark.e2e
class TestDashboardFlow:
    def _login(self, page, live_server, email="admin@harmonymusic.com", password="admin123"):
        page.goto(f"{live_server}/accounts/login/")
        page.fill('input[name="username"]', email)
        page.fill('input[name="password"]', password)
        page.click('button[type="submit"]')
        page.wait_for_url("**/dashboard/**", timeout=5000)

    def test_admin_dashboard(self, live_server, page, screenshot_dir):
        self._login(page, live_server)
        page.screenshot(path=os.path.join(screenshot_dir, "04_admin_dashboard.png"))

        assert page.is_visible("text=Dashboard")

    def test_sidebar_navigation(self, live_server, page, screenshot_dir):
        self._login(page, live_server)
        page.screenshot(path=os.path.join(screenshot_dir, "05_sidebar.png"))

        assert page.is_visible("text=Courses")
        assert page.is_visible("text=Live Sessions")
        assert page.is_visible("text=Members")
        assert page.is_visible("text=Settings")

    def test_navigate_to_courses(self, live_server, page, screenshot_dir):
        self._login(page, live_server)
        page.click("a:has-text('Courses')")
        page.wait_for_url("**/courses/**", timeout=5000)
        page.screenshot(path=os.path.join(screenshot_dir, "06_course_list.png"))

        assert "courses" in page.url

    def test_navigate_to_sessions(self, live_server, page, screenshot_dir):
        self._login(page, live_server)
        page.click("a:has-text('Live Sessions')")
        page.wait_for_url("**/schedule/**", timeout=5000)
        page.screenshot(path=os.path.join(screenshot_dir, "07_sessions_list.png"))

        assert "schedule" in page.url

    def test_student_dashboard(self, live_server, page, screenshot_dir):
        self._login(page, live_server, "alice@example.com", "student123")
        page.screenshot(path=os.path.join(screenshot_dir, "08_student_dashboard.png"))

        assert page.is_visible("text=My Progress") or "student" in page.url

    def test_mobile_view(self, live_server, page, screenshot_dir):
        page.set_viewport_size({"width": 375, "height": 812})
        self._login(page, live_server)
        page.screenshot(path=os.path.join(screenshot_dir, "09_mobile_dashboard.png"))
