"""
UX Audit: Student Journey Screenshot Walker
Captures screenshots at every step of the student experience.
Run: python scripts/ux_audit_student.py
"""
import os
import sys
import time

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8001"
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "..", "screenshots", "ux_audit")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

STUDENT_EMAIL = "alice@example.com"
STUDENT_PASSWORD = "student123"


def shot(page, name, mobile=False):
    """Take a screenshot with a numbered name."""
    prefix = "mobile_" if mobile else ""
    path = os.path.join(SCREENSHOT_DIR, f"{prefix}{name}.png")
    page.screenshot(path=path, full_page=True)
    print(f"  -> {prefix}{name}.png")


def remove_debug_toolbar(page):
    page.evaluate("document.getElementById('djDebug')?.remove()")


def wait_ready(page):
    """Wait for page to be ready - use domcontentloaded + short sleep to avoid networkidle timeout from CDN."""
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(1000)
    remove_debug_toolbar(page)


def login(page, email, password):
    page.goto(f"{BASE_URL}/accounts/login/")
    wait_ready(page)
    page.fill('input[name="username"]', email)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    wait_ready(page)


def nav_click(page, text):
    """Click sidebar nav link."""
    page.locator(f"aside a:has-text('{text}')").click()
    wait_ready(page)


def run_audit():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # ============================================================
        # STAGE 1: DISCOVERY & ENTRY (Unauthenticated)
        # ============================================================
        print("\n=== STAGE 1: Discovery & Entry ===")
        ctx = browser.new_context(viewport={"width": 1280, "height": 720})
        page = ctx.new_page()

        # 1a. Academy landing page (branded)
        page.goto(f"{BASE_URL}/join/harmony-music-academy/")
        wait_ready(page)
        shot(page, "01a_academy_landing")

        # 1b. Login page
        page.goto(f"{BASE_URL}/accounts/login/")
        wait_ready(page)
        shot(page, "01b_login_page")

        # 1c. Register page
        page.goto(f"{BASE_URL}/accounts/register/")
        wait_ready(page)
        shot(page, "01c_register_page")

        # 1d. Register page with validation errors (submit empty)
        page.click('button[type="submit"]')
        wait_ready(page)
        shot(page, "01d_register_validation_errors")

        page.close()
        ctx.close()

        # ============================================================
        # STAGE 2-12: AUTHENTICATED STUDENT JOURNEY
        # ============================================================
        print("\n=== STAGE 2: Login & Dashboard ===")
        ctx = browser.new_context(viewport={"width": 1280, "height": 720})
        page = ctx.new_page()
        login(page, STUDENT_EMAIL, STUDENT_PASSWORD)

        # 2a. Student dashboard (first thing after login)
        shot(page, "02a_student_dashboard")

        # ============================================================
        # STAGE 3: Course Discovery
        # ============================================================
        print("\n=== STAGE 3: Course Discovery ===")

        # 3a. Course list via sidebar
        nav_click(page, "Courses")
        shot(page, "03a_course_list")

        # 3b. Course detail (click first course)
        course_links = page.locator(".drawer-content a[href*='/courses/']")
        if course_links.count() > 0:
            course_links.first.click()
            wait_ready(page)
            shot(page, "03b_course_detail")

            # 3c. Lesson detail (click first lesson if available)
            lesson_links = page.locator("a[href*='/lessons/']")
            if lesson_links.count() > 0:
                lesson_links.first.click()
                wait_ready(page)
                shot(page, "03c_lesson_detail")
                page.go_back()
                wait_ready(page)
        else:
            print("  (no courses found)")

        # ============================================================
        # STAGE 4: Enrollment & Progress
        # ============================================================
        print("\n=== STAGE 4: Enrollment & Progress ===")

        # 4a. My Progress (enrollments list)
        nav_click(page, "My Progress")
        shot(page, "04a_my_progress")

        # 4b. Enrollment detail (click first enrollment if available)
        enrollment_links = page.locator("a[href*='/enrollments/']")
        if enrollment_links.count() > 0:
            enrollment_links.first.click()
            wait_ready(page)
            shot(page, "04b_enrollment_detail")
            page.go_back()
            wait_ready(page)
        else:
            print("  (no enrollments found)")

        # ============================================================
        # STAGE 5: Schedule & Live Sessions
        # ============================================================
        print("\n=== STAGE 5: Schedule & Live Sessions ===")

        page.goto(f"{BASE_URL}/schedule/")
        wait_ready(page)
        shot(page, "05a_schedule")

        # 5b. Session detail (click first session if available)
        session_links = page.locator("a[href*='/schedule/']")
        if session_links.count() > 0:
            session_links.first.click()
            wait_ready(page)
            shot(page, "05b_session_detail")

        # ============================================================
        # STAGE 6: Practice
        # ============================================================
        print("\n=== STAGE 6: Practice ===")

        page.goto(f"{BASE_URL}/practice/")
        wait_ready(page)
        shot(page, "06a_practice_journal")

        # ============================================================
        # STAGE 7: Music Tools
        # ============================================================
        print("\n=== STAGE 7: Music Tools ===")

        page.goto(f"{BASE_URL}/tools/metronome/")
        wait_ready(page)
        shot(page, "07a_metronome")

        page.goto(f"{BASE_URL}/tools/tuner/")
        wait_ready(page)
        shot(page, "07b_tuner")

        # ============================================================
        # STAGE 8: Library
        # ============================================================
        print("\n=== STAGE 8: Library ===")

        page.goto(f"{BASE_URL}/library/")
        wait_ready(page)
        shot(page, "08a_library")

        # ============================================================
        # STAGE 9: Notifications
        # ============================================================
        print("\n=== STAGE 9: Notifications ===")

        page.goto(f"{BASE_URL}/notifications/")
        wait_ready(page)
        shot(page, "09a_notifications")

        # ============================================================
        # STAGE 10: Profile & Account
        # ============================================================
        print("\n=== STAGE 10: Profile & Account ===")

        page.goto(f"{BASE_URL}/accounts/profile/")
        wait_ready(page)
        shot(page, "10a_profile")

        edit_link = page.locator("a[href*='profile/edit']")
        if edit_link.count() > 0:
            edit_link.first.click()
            wait_ready(page)
            shot(page, "10b_profile_edit")

        # ============================================================
        # STAGE 11: Payments
        # ============================================================
        print("\n=== STAGE 11: Payments ===")

        page.goto(f"{BASE_URL}/payments/pricing/")
        wait_ready(page)
        shot(page, "11a_pricing")

        page.goto(f"{BASE_URL}/payments/my-subscriptions/")
        wait_ready(page)
        shot(page, "11b_my_subscriptions")

        page.goto(f"{BASE_URL}/payments/my-packages/")
        wait_ready(page)
        shot(page, "11c_my_packages")

        # ============================================================
        # STAGE 12: Legal Pages
        # ============================================================
        print("\n=== STAGE 12: Legal & Footer ===")

        page.goto(f"{BASE_URL}/legal/terms/")
        wait_ready(page)
        shot(page, "12a_terms")

        page.goto(f"{BASE_URL}/legal/privacy/")
        wait_ready(page)
        shot(page, "12b_privacy")

        page.close()
        ctx.close()

        # ============================================================
        # MOBILE VIEWPORT (key pages)
        # ============================================================
        print("\n=== MOBILE VIEWPORT (375px) ===")
        ctx = browser.new_context(viewport={"width": 375, "height": 812})
        page = ctx.new_page()
        login(page, STUDENT_EMAIL, STUDENT_PASSWORD)

        # Mobile dashboard
        shot(page, "02a_student_dashboard", mobile=True)

        # Mobile - open sidebar
        hamburger = page.locator("label[for='sidebar-drawer']").first
        if hamburger.is_visible():
            hamburger.click()
            page.wait_for_timeout(500)
            shot(page, "02b_sidebar_open", mobile=True)

            # Navigate to courses
            page.locator("aside a:has-text('Courses')").click()
            wait_ready(page)
            shot(page, "03a_course_list", mobile=True)

        # Mobile course detail
        course_links = page.locator(".drawer-content a[href*='/courses/']")
        if course_links.count() > 0:
            course_links.first.click()
            wait_ready(page)
            shot(page, "03b_course_detail", mobile=True)

        # Mobile schedule
        page.goto(f"{BASE_URL}/schedule/")
        wait_ready(page)
        shot(page, "05a_schedule", mobile=True)

        # Mobile profile
        page.goto(f"{BASE_URL}/accounts/profile/")
        wait_ready(page)
        shot(page, "10a_profile", mobile=True)

        page.close()
        ctx.close()
        browser.close()

    print(f"\nDone! {len(os.listdir(SCREENSHOT_DIR))} screenshots saved to {SCREENSHOT_DIR}")


if __name__ == "__main__":
    run_audit()
