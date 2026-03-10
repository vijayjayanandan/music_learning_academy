"""
E2E Persona Agent: Student (alice@example.com)
"""

import os
import pytest

from .conftest import _remove_debug_toolbar, click_sidebar


def _goto_home(page, e2e_server):
    page.goto(f"{e2e_server}/")
    page.wait_for_load_state("networkidle")
    _remove_debug_toolbar(page)


@pytest.mark.e2e
class TestStudentFlow:
    def test_01_student_dashboard(self, e2e_server, student_page, screenshot_dir):
        _goto_home(student_page, e2e_server)
        student_page.screenshot(
            path=os.path.join(screenshot_dir, "student_01_dashboard.png")
        )
        assert "/accounts/login" not in student_page.url

    def test_02_enrollments(self, e2e_server, student_page, screenshot_dir):
        _goto_home(student_page, e2e_server)
        click_sidebar(student_page, "My Progress")
        student_page.screenshot(
            path=os.path.join(screenshot_dir, "student_02_enrollments.png")
        )
        assert "Server Error" not in student_page.content()

    def test_03_course_list(self, e2e_server, student_page, screenshot_dir):
        _goto_home(student_page, e2e_server)
        click_sidebar(student_page, "Courses")
        student_page.screenshot(
            path=os.path.join(screenshot_dir, "student_03_courses.png")
        )
        assert "courses" in student_page.url

    def test_04_course_detail(self, e2e_server, student_page, screenshot_dir):
        _goto_home(student_page, e2e_server)
        click_sidebar(student_page, "Courses")
        course_links = student_page.locator(".drawer-content a[href*='/courses/']")
        if course_links.count() > 0:
            course_links.first.click()
            student_page.wait_for_load_state("networkidle")
            _remove_debug_toolbar(student_page)
        student_page.screenshot(
            path=os.path.join(screenshot_dir, "student_04_course_detail.png")
        )
        assert "Server Error" not in student_page.content()

    def test_05_practice_journal(self, e2e_server, student_page, screenshot_dir):
        _goto_home(student_page, e2e_server)
        click_sidebar(student_page, "Practice")
        student_page.screenshot(
            path=os.path.join(screenshot_dir, "student_05_practice.png")
        )
        assert "Server Error" not in student_page.content()

    def test_06_practice_form_on_list(self, e2e_server, student_page, screenshot_dir):
        student_page.goto(f"{e2e_server}/practice/")
        student_page.wait_for_load_state("networkidle")
        _remove_debug_toolbar(student_page)
        student_page.screenshot(
            path=os.path.join(screenshot_dir, "student_06_practice_form.png")
        )
        # Verify inline practice form is present on the list page
        assert student_page.locator("form").count() > 0
        assert "Server Error" not in student_page.content()

    def test_07_music_tools_metronome(self, e2e_server, student_page, screenshot_dir):
        student_page.goto(f"{e2e_server}/tools/metronome/")
        student_page.wait_for_load_state("networkidle")
        _remove_debug_toolbar(student_page)
        student_page.screenshot(
            path=os.path.join(screenshot_dir, "student_07_metronome.png")
        )
        assert "Server Error" not in student_page.content()

    def test_08_music_tools_tuner(self, e2e_server, student_page, screenshot_dir):
        student_page.goto(f"{e2e_server}/tools/tuner/")
        student_page.wait_for_load_state("networkidle")
        _remove_debug_toolbar(student_page)
        student_page.screenshot(
            path=os.path.join(screenshot_dir, "student_08_tuner.png")
        )
        assert "Server Error" not in student_page.content()

    def test_09_library(self, e2e_server, student_page, screenshot_dir):
        student_page.goto(f"{e2e_server}/library/")
        student_page.wait_for_load_state("networkidle")
        _remove_debug_toolbar(student_page)
        student_page.screenshot(
            path=os.path.join(screenshot_dir, "student_09_library.png")
        )
        assert "Server Error" not in student_page.content()

    def test_10_notifications(self, e2e_server, student_page, screenshot_dir):
        student_page.goto(f"{e2e_server}/notifications/")
        student_page.wait_for_load_state("networkidle")
        _remove_debug_toolbar(student_page)
        student_page.screenshot(
            path=os.path.join(screenshot_dir, "student_10_notifications.png")
        )
        assert "Server Error" not in student_page.content()

    def test_11_profile(self, e2e_server, student_page, screenshot_dir):
        student_page.goto(f"{e2e_server}/accounts/profile/")
        student_page.wait_for_load_state("networkidle")
        _remove_debug_toolbar(student_page)
        student_page.screenshot(
            path=os.path.join(screenshot_dir, "student_11_profile.png")
        )
        assert "Server Error" not in student_page.content()

    def test_12_mobile_viewport(
        self, e2e_server, browser, student_storage, screenshot_dir
    ):
        ctx = browser.new_context(
            storage_state=student_storage, viewport={"width": 375, "height": 812}
        )
        p = ctx.new_page()
        p.goto(f"{e2e_server}/")
        p.wait_for_load_state("networkidle")
        _remove_debug_toolbar(p)
        p.screenshot(path=os.path.join(screenshot_dir, "student_12_mobile.png"))
        assert "/accounts/login" not in p.url, "Not authenticated in mobile context"
        hamburger = p.locator("label[for='sidebar-drawer']").first
        hamburger.wait_for(state="visible", timeout=5000)
        assert hamburger.is_visible()
        p.close()
        ctx.close()
