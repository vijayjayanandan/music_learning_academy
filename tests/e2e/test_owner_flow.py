"""
E2E Persona Agent: Academy Owner (admin@harmonymusic.com)
"""

import os
import pytest

from .conftest import _remove_debug_toolbar, click_sidebar


def _goto_home(page, e2e_server):
    page.goto(f"{e2e_server}/")
    page.wait_for_load_state("networkidle")
    _remove_debug_toolbar(page)


@pytest.mark.e2e
class TestOwnerFlow:
    def test_01_admin_dashboard(self, e2e_server, owner_page, screenshot_dir):
        _goto_home(owner_page, e2e_server)
        owner_page.screenshot(
            path=os.path.join(screenshot_dir, "owner_01_dashboard.png")
        )
        assert "/accounts/login" not in owner_page.url

    def test_02_academy_settings(self, e2e_server, owner_page, screenshot_dir):
        _goto_home(owner_page, e2e_server)
        click_sidebar(owner_page, "Settings")
        owner_page.screenshot(
            path=os.path.join(screenshot_dir, "owner_02_settings.png")
        )
        assert "Server Error" not in owner_page.content()

    def test_03_academy_members(self, e2e_server, owner_page, screenshot_dir):
        _goto_home(owner_page, e2e_server)
        click_sidebar(owner_page, "Members")
        owner_page.screenshot(path=os.path.join(screenshot_dir, "owner_03_members.png"))
        assert "members" in owner_page.url.lower()

    def test_04_course_list(self, e2e_server, owner_page, screenshot_dir):
        _goto_home(owner_page, e2e_server)
        click_sidebar(owner_page, "Courses")
        owner_page.screenshot(path=os.path.join(screenshot_dir, "owner_04_courses.png"))
        assert "courses" in owner_page.url

    def test_05_create_course_form(self, e2e_server, owner_page, screenshot_dir):
        _goto_home(owner_page, e2e_server)
        click_sidebar(owner_page, "+ New Course")
        owner_page.screenshot(
            path=os.path.join(screenshot_dir, "owner_05_create_course.png")
        )
        assert "Server Error" not in owner_page.content()

    def test_06_live_sessions(self, e2e_server, owner_page, screenshot_dir):
        _goto_home(owner_page, e2e_server)
        click_sidebar(owner_page, "Live Sessions")
        owner_page.screenshot(
            path=os.path.join(screenshot_dir, "owner_06_sessions.png")
        )
        assert "schedule" in owner_page.url

    def test_07_schedule_session_form(self, e2e_server, owner_page, screenshot_dir):
        _goto_home(owner_page, e2e_server)
        click_sidebar(owner_page, "+ Schedule Session")
        owner_page.screenshot(
            path=os.path.join(screenshot_dir, "owner_07_create_session.png")
        )
        assert "Server Error" not in owner_page.content()

    def test_08_pricing_page(self, e2e_server, owner_page, screenshot_dir):
        owner_page.goto(f"{e2e_server}/payments/pricing/")
        owner_page.wait_for_load_state("networkidle")
        _remove_debug_toolbar(owner_page)
        owner_page.screenshot(path=os.path.join(screenshot_dir, "owner_08_pricing.png"))
        assert "Server Error" not in owner_page.content()

    def test_09_coupons(self, e2e_server, owner_page, screenshot_dir):
        _goto_home(owner_page, e2e_server)
        click_sidebar(owner_page, "Coupons")
        owner_page.screenshot(path=os.path.join(screenshot_dir, "owner_09_coupons.png"))
        assert "Server Error" not in owner_page.content()

    def test_10_announcements(self, e2e_server, owner_page, screenshot_dir):
        _goto_home(owner_page, e2e_server)
        click_sidebar(owner_page, "Announcements")
        owner_page.screenshot(
            path=os.path.join(screenshot_dir, "owner_10_announcements.png")
        )
        assert "Server Error" not in owner_page.content()

    def test_11_sidebar_completeness(self, e2e_server, owner_page, screenshot_dir):
        _goto_home(owner_page, e2e_server)
        owner_page.screenshot(path=os.path.join(screenshot_dir, "owner_11_sidebar.png"))
        sidebar = owner_page.locator("aside")
        sidebar_text = sidebar.text_content()
        for item in [
            "Dashboard",
            "Courses",
            "Live Sessions",
            "Members",
            "Settings",
            "Coupons",
        ]:
            assert item in sidebar_text, f"Missing sidebar item: {item}"

    def test_12_mobile_viewport(
        self, e2e_server, browser, owner_storage, screenshot_dir
    ):
        ctx = browser.new_context(
            storage_state=owner_storage, viewport={"width": 375, "height": 812}
        )
        p = ctx.new_page()
        p.goto(f"{e2e_server}/")
        p.wait_for_load_state("networkidle")
        _remove_debug_toolbar(p)
        p.screenshot(path=os.path.join(screenshot_dir, "owner_12_mobile.png"))
        assert "/accounts/login" not in p.url, "Not authenticated in mobile context"
        hamburger = p.locator("label[for='sidebar-drawer']").first
        hamburger.wait_for(state="visible", timeout=5000)
        assert hamburger.is_visible()
        p.close()
        ctx.close()
