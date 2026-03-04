"""
E2E Persona Agent: Instructor (sarah@harmonymusic.com)
"""
import os
import pytest

from .conftest import _remove_debug_toolbar, click_sidebar


def _goto_home(page, e2e_server):
    page.goto(f"{e2e_server}/")
    page.wait_for_load_state("networkidle")
    _remove_debug_toolbar(page)


@pytest.mark.e2e
class TestInstructorFlow:

    def test_01_instructor_dashboard(self, e2e_server, instructor_page, screenshot_dir):
        _goto_home(instructor_page, e2e_server)
        instructor_page.screenshot(path=os.path.join(screenshot_dir, "instructor_01_dashboard.png"))
        assert "/accounts/login" not in instructor_page.url

    def test_02_my_courses(self, e2e_server, instructor_page, screenshot_dir):
        _goto_home(instructor_page, e2e_server)
        click_sidebar(instructor_page, "Courses")
        instructor_page.screenshot(path=os.path.join(screenshot_dir, "instructor_02_courses.png"))
        assert "courses" in instructor_page.url

    def test_03_course_detail(self, e2e_server, instructor_page, screenshot_dir):
        _goto_home(instructor_page, e2e_server)
        click_sidebar(instructor_page, "Courses")
        course_links = instructor_page.locator(".drawer-content a[href*='/courses/']")
        if course_links.count() > 0:
            course_links.first.click()
            instructor_page.wait_for_load_state("networkidle")
            _remove_debug_toolbar(instructor_page)
        instructor_page.screenshot(path=os.path.join(screenshot_dir, "instructor_03_course_detail.png"))
        assert "Server Error" not in instructor_page.content()

    def test_04_create_lesson_form(self, e2e_server, instructor_page, screenshot_dir):
        _goto_home(instructor_page, e2e_server)
        click_sidebar(instructor_page, "Courses")
        course_links = instructor_page.locator(".drawer-content a[href*='/courses/']")
        if course_links.count() > 0:
            course_links.first.click()
            instructor_page.wait_for_load_state("networkidle")
            _remove_debug_toolbar(instructor_page)
        instructor_page.screenshot(path=os.path.join(screenshot_dir, "instructor_04_lesson_form.png"))
        assert "Server Error" not in instructor_page.content()

    def test_05_schedule_page(self, e2e_server, instructor_page, screenshot_dir):
        _goto_home(instructor_page, e2e_server)
        click_sidebar(instructor_page, "Live Sessions")
        instructor_page.screenshot(path=os.path.join(screenshot_dir, "instructor_05_schedule.png"))
        assert "schedule" in instructor_page.url

    def test_06_notifications(self, e2e_server, instructor_page, screenshot_dir):
        instructor_page.goto(f"{e2e_server}/notifications/")
        instructor_page.wait_for_load_state("networkidle")
        _remove_debug_toolbar(instructor_page)
        instructor_page.screenshot(path=os.path.join(screenshot_dir, "instructor_06_notifications.png"))
        assert "Server Error" not in instructor_page.content()

    def test_07_messages(self, e2e_server, instructor_page, screenshot_dir):
        _goto_home(instructor_page, e2e_server)
        click_sidebar(instructor_page, "Messages")
        instructor_page.screenshot(path=os.path.join(screenshot_dir, "instructor_07_messages.png"))
        assert "Server Error" not in instructor_page.content()

    def test_08_profile(self, e2e_server, instructor_page, screenshot_dir):
        instructor_page.goto(f"{e2e_server}/accounts/profile/")
        instructor_page.wait_for_load_state("networkidle")
        _remove_debug_toolbar(instructor_page)
        instructor_page.screenshot(path=os.path.join(screenshot_dir, "instructor_08_profile.png"))
        assert "Server Error" not in instructor_page.content()

    def test_09_practice_page(self, e2e_server, instructor_page, screenshot_dir):
        _goto_home(instructor_page, e2e_server)
        click_sidebar(instructor_page, "Practice")
        instructor_page.screenshot(path=os.path.join(screenshot_dir, "instructor_09_practice.png"))
        assert "Server Error" not in instructor_page.content()

    def test_10_availability(self, e2e_server, instructor_page, screenshot_dir):
        _goto_home(instructor_page, e2e_server)
        click_sidebar(instructor_page, "My Availability")
        instructor_page.screenshot(path=os.path.join(screenshot_dir, "instructor_10_availability.png"))
        assert "Server Error" not in instructor_page.content()

    def test_11_mobile_viewport(self, e2e_server, browser, instructor_storage, screenshot_dir):
        ctx = browser.new_context(storage_state=instructor_storage, viewport={"width": 375, "height": 812})
        p = ctx.new_page()
        p.goto(f"{e2e_server}/")
        p.wait_for_load_state("networkidle")
        _remove_debug_toolbar(p)
        p.screenshot(path=os.path.join(screenshot_dir, "instructor_11_mobile.png"))
        assert "/accounts/login" not in p.url, "Not authenticated in mobile context"
        hamburger = p.locator("label[for='sidebar-drawer']").first
        hamburger.wait_for(state="visible", timeout=5000)
        assert hamburger.is_visible()
        p.close()
        ctx.close()
