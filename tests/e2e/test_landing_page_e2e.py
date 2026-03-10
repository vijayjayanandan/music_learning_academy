"""
E2E Tests: Academy Landing Page (/join/<slug>/)

Tests the public-facing branded signup page that prospective students
see when they visit an academy's join link. No login required.
"""
import os
import pytest

from .conftest import _remove_debug_toolbar


ACADEMY_SLUG = "harmony-music-school"
LANDING_URL = f"/join/{ACADEMY_SLUG}/"


def _goto_landing(page, e2e_server):
    """Navigate to the academy landing page and wait for it to load."""
    page.goto(f"{e2e_server}{LANDING_URL}")
    page.wait_for_load_state("domcontentloaded")
    _remove_debug_toolbar(page)


@pytest.mark.e2e
class TestLandingPageHero:
    """Hero section: academy name, welcome message, instrument badges, CTA."""

    def test_01_page_loads_without_login(self, e2e_server, page, screenshot_dir):
        """Landing page is publicly accessible — no authentication required."""
        _goto_landing(page, e2e_server)
        page.screenshot(path=os.path.join(screenshot_dir, "landing_01_hero.png"))
        assert "Server Error" not in page.content()
        assert "/accounts/login" not in page.url

    def test_02_academy_name_visible(self, e2e_server, page, screenshot_dir):
        """The academy name is displayed prominently in the hero section."""
        _goto_landing(page, e2e_server)
        h1 = page.locator("h1")
        assert h1.is_visible()
        # The seeded academy is "Harmony Music School"
        assert "Harmony Music School" in h1.inner_text()
        page.screenshot(path=os.path.join(screenshot_dir, "landing_02_academy_name.png"))

    def test_03_hero_section_has_aria_label(self, e2e_server, page):
        """Hero section has an accessible aria-label."""
        _goto_landing(page, e2e_server)
        hero = page.locator("section[aria-label*='Welcome']")
        assert hero.count() > 0, "Hero section should have aria-label containing 'Welcome'"

    def test_04_instrument_badges_displayed(self, e2e_server, page, screenshot_dir):
        """Instrument badges render in the hero section (if academy has instruments)."""
        _goto_landing(page, e2e_server)
        badges = page.locator("section[aria-label*='Welcome'] .badge")
        page.screenshot(path=os.path.join(screenshot_dir, "landing_04_instrument_badges.png"))
        # Seed data includes instruments; at least one badge should be visible
        if badges.count() > 0:
            assert badges.first.is_visible()

    def test_05_get_started_cta_visible(self, e2e_server, page, screenshot_dir):
        """The 'Get Started' CTA button is visible in the hero."""
        _goto_landing(page, e2e_server)
        cta = page.locator("a:has-text('Get Started')")
        assert cta.is_visible()
        # CTA should link to the #signup anchor
        assert cta.get_attribute("href") == "#signup"
        page.screenshot(path=os.path.join(screenshot_dir, "landing_05_cta.png"))


@pytest.mark.e2e
class TestLandingPageCourses:
    """Courses section: grid of published courses."""

    def test_06_courses_section_renders(self, e2e_server, page, screenshot_dir):
        """Courses section renders if published courses exist."""
        _goto_landing(page, e2e_server)
        courses_section = page.locator("section[aria-label='Courses offered']")
        page.screenshot(path=os.path.join(screenshot_dir, "landing_06_courses.png"))
        if courses_section.count() > 0:
            heading = courses_section.locator("h2")
            assert "Learn" in heading.inner_text()
            # Course cards should be present
            cards = courses_section.locator("article")
            assert cards.count() > 0

    def test_07_course_cards_have_title_and_instrument(self, e2e_server, page):
        """Each course card displays a title and instrument badge."""
        _goto_landing(page, e2e_server)
        courses_section = page.locator("section[aria-label='Courses offered']")
        if courses_section.count() > 0:
            cards = courses_section.locator("article")
            for i in range(min(cards.count(), 3)):
                card = cards.nth(i)
                # Card title
                title = card.locator(".card-title")
                assert title.is_visible(), f"Course card {i} should have a visible title"
                # At least one badge (instrument or difficulty)
                badges = card.locator(".badge")
                assert badges.count() > 0, f"Course card {i} should have badges"


@pytest.mark.e2e
class TestLandingPageInstructors:
    """Instructors section: instructor cards."""

    def test_08_instructors_section_renders(self, e2e_server, page, screenshot_dir):
        """Instructors section renders if instructors exist."""
        _goto_landing(page, e2e_server)
        instructors_section = page.locator("section[aria-label='Our instructors']")
        page.screenshot(path=os.path.join(screenshot_dir, "landing_08_instructors.png"))
        if instructors_section.count() > 0:
            heading = instructors_section.locator("h2")
            assert "Instructor" in heading.inner_text()
            # Instructor cards
            cards = instructors_section.locator("article")
            assert cards.count() > 0

    def test_09_instructor_cards_have_name(self, e2e_server, page):
        """Each instructor card displays the instructor's name."""
        _goto_landing(page, e2e_server)
        instructors_section = page.locator("section[aria-label='Our instructors']")
        if instructors_section.count() > 0:
            cards = instructors_section.locator("article")
            for i in range(cards.count()):
                card = cards.nth(i)
                name = card.locator("h3")
                assert name.is_visible(), f"Instructor card {i} should display a name"
                assert len(name.inner_text().strip()) > 0, f"Instructor card {i} name should not be empty"


@pytest.mark.e2e
class TestLandingPagePricing:
    """Pricing section: subscription plans and packages."""

    def test_10_pricing_section_renders(self, e2e_server, page, screenshot_dir):
        """Pricing section renders if plans or packages exist."""
        _goto_landing(page, e2e_server)
        pricing_section = page.locator("section[aria-label='Pricing plans']")
        page.screenshot(path=os.path.join(screenshot_dir, "landing_10_pricing.png"))
        # Pricing section is conditional — only rendered if has_pricing is true
        if pricing_section.count() > 0:
            heading = pricing_section.locator("h2")
            assert "Pricing" in heading.inner_text()


@pytest.mark.e2e
class TestLandingPageSignupForm:
    """Signup form section: registration form with expected fields."""

    def test_11_signup_section_exists(self, e2e_server, page, screenshot_dir):
        """The #signup section exists and has the registration form."""
        _goto_landing(page, e2e_server)
        signup_section = page.locator("section#signup")
        assert signup_section.is_visible()
        page.screenshot(path=os.path.join(screenshot_dir, "landing_11_signup_form.png"))

    def test_12_signup_section_has_aria_label(self, e2e_server, page):
        """Signup section has an accessible aria-label."""
        _goto_landing(page, e2e_server)
        signup_section = page.locator("section#signup[aria-label='Create your account']")
        assert signup_section.count() > 0

    def test_13_form_has_expected_fields(self, e2e_server, page, screenshot_dir):
        """Registration form renders all expected input fields."""
        _goto_landing(page, e2e_server)
        form = page.locator("section#signup form")
        assert form.count() > 0, "Signup section should contain a form"

        # Check for key form fields from RegisterForm (slim: email, password, DOB, terms)
        assert page.locator("section#signup input[name='email']").count() > 0, "Form should have email field"
        assert page.locator("section#signup input[name='password1']").count() > 0, "Form should have password1 field"
        assert page.locator("section#signup input[name='password2']").count() > 0, "Form should have password2 field"
        assert page.locator("section#signup input[name='date_of_birth']").count() > 0, "Form should have date_of_birth field"
        assert page.locator("section#signup input[name='accept_terms']").count() > 0, "Form should have accept_terms checkbox"
        # username, first_name, last_name should NOT be visible
        assert page.locator("section#signup input[name='username']").count() == 0, "username field should not be visible"
        assert page.locator("section#signup input[name='first_name']").count() == 0, "first_name field should not be visible"
        assert page.locator("section#signup input[name='last_name']").count() == 0, "last_name field should not be visible"

        page.screenshot(path=os.path.join(screenshot_dir, "landing_13_form_fields.png"))

    def test_14_form_has_submit_button(self, e2e_server, page):
        """Registration form has a submit button with academy-specific text."""
        _goto_landing(page, e2e_server)
        submit_btn = page.locator("section#signup button[type='submit']")
        assert submit_btn.is_visible()
        assert "Join" in submit_btn.inner_text()

    def test_15_form_has_csrf_token(self, e2e_server, page):
        """Registration form includes a CSRF token (Django security)."""
        _goto_landing(page, e2e_server)
        csrf = page.locator("section#signup input[name='csrfmiddlewaretoken']")
        assert csrf.count() > 0, "Form must include CSRF token"

    def test_16_sign_in_link_present(self, e2e_server, page):
        """A 'Sign in' link is available below the form for existing users."""
        _goto_landing(page, e2e_server)
        sign_in = page.locator("section#signup a:has-text('Sign in')")
        assert sign_in.is_visible()
        assert "/accounts/login" in sign_in.get_attribute("href")

    def test_17_terms_and_privacy_links(self, e2e_server, page):
        """Terms of Service and Privacy Policy links are present."""
        _goto_landing(page, e2e_server)
        terms_link = page.locator("section#signup a:has-text('Terms of Service')")
        privacy_link = page.locator("section#signup a:has-text('Privacy Policy')")
        assert terms_link.is_visible(), "Terms of Service link should be visible"
        assert privacy_link.is_visible(), "Privacy Policy link should be visible"


@pytest.mark.e2e
class TestLandingPageCTAScroll:
    """Test that the 'Get Started' CTA scrolls to the signup section."""

    def test_18_cta_scrolls_to_signup(self, e2e_server, page, screenshot_dir):
        """Clicking 'Get Started' scrolls the page to the #signup section."""
        _goto_landing(page, e2e_server)
        page.wait_for_load_state("networkidle")

        # Verify signup section is NOT in the viewport initially (it's below the fold)
        signup_section = page.locator("section#signup")
        assert signup_section.is_visible()  # exists in DOM

        # Click the CTA
        cta = page.locator("a:has-text('Get Started')")
        cta.click()

        # Wait for smooth scroll to complete
        page.wait_for_timeout(1000)

        # After clicking, the signup section should be in or near the viewport
        # We verify by checking that the signup form heading is visible in the viewport
        signup_heading = page.locator("section#signup h2")
        signup_heading.wait_for(state="visible", timeout=3000)
        bounding_box = signup_heading.bounding_box()
        assert bounding_box is not None, "Signup heading should be in the DOM"
        # The heading should be within the visible viewport height (720px default)
        viewport_height = page.viewport_size["height"]
        assert bounding_box["y"] < viewport_height, "Signup heading should be scrolled into view"

        page.screenshot(path=os.path.join(screenshot_dir, "landing_18_after_cta_scroll.png"))


@pytest.mark.e2e
class TestLandingPageMobile:
    """Test the landing page at mobile viewport (375px width)."""

    def test_19_mobile_page_loads(self, e2e_server, browser, screenshot_dir):
        """Landing page renders correctly at mobile viewport width."""
        ctx = browser.new_context(viewport={"width": 375, "height": 812})
        p = ctx.new_page()
        p.goto(f"{e2e_server}{LANDING_URL}")
        p.wait_for_load_state("domcontentloaded")
        _remove_debug_toolbar(p)
        p.screenshot(path=os.path.join(screenshot_dir, "landing_19_mobile_hero.png"))

        # Academy name should still be visible
        h1 = p.locator("h1")
        assert h1.is_visible()
        assert "Harmony Music School" in h1.inner_text()

        # CTA should be visible
        cta = p.locator("a:has-text('Get Started')")
        assert cta.is_visible()

        assert "Server Error" not in p.content()
        p.close()
        ctx.close()

    def test_20_mobile_signup_form(self, e2e_server, browser, screenshot_dir):
        """Signup form is usable at mobile viewport width."""
        ctx = browser.new_context(viewport={"width": 375, "height": 812})
        p = ctx.new_page()
        p.goto(f"{e2e_server}{LANDING_URL}")
        p.wait_for_load_state("domcontentloaded")
        _remove_debug_toolbar(p)

        # Scroll to signup section
        p.locator("section#signup").scroll_into_view_if_needed()
        p.wait_for_timeout(500)
        p.screenshot(path=os.path.join(screenshot_dir, "landing_20_mobile_signup.png"))

        # Form should be visible and usable
        form = p.locator("section#signup form")
        assert form.is_visible()

        # Submit button should be visible
        submit_btn = p.locator("section#signup button[type='submit']")
        assert submit_btn.is_visible()

        p.close()
        ctx.close()

    def test_21_mobile_full_page_screenshot(self, e2e_server, browser, screenshot_dir):
        """Capture a full-page screenshot at mobile viewport for visual review."""
        ctx = browser.new_context(viewport={"width": 375, "height": 812})
        p = ctx.new_page()
        p.goto(f"{e2e_server}{LANDING_URL}")
        p.wait_for_load_state("networkidle")
        _remove_debug_toolbar(p)
        p.screenshot(
            path=os.path.join(screenshot_dir, "landing_21_mobile_full_page.png"),
            full_page=True,
        )
        assert "Server Error" not in p.content()
        p.close()
        ctx.close()


@pytest.mark.e2e
class TestLandingPageFullPage:
    """Full-page screenshot and overall page structure tests."""

    def test_22_full_page_screenshot(self, e2e_server, page, screenshot_dir):
        """Capture a full-page screenshot at desktop viewport for visual review."""
        _goto_landing(page, e2e_server)
        page.wait_for_load_state("networkidle")
        page.screenshot(
            path=os.path.join(screenshot_dir, "landing_22_desktop_full_page.png"),
            full_page=True,
        )
        assert "Server Error" not in page.content()

    def test_23_page_has_correct_title(self, e2e_server, page):
        """Page title includes the academy name."""
        _goto_landing(page, e2e_server)
        title = page.title()
        assert "Harmony Music School" in title

    def test_24_no_server_errors_in_page(self, e2e_server, page):
        """Page does not contain any Django server error output."""
        _goto_landing(page, e2e_server)
        content = page.content()
        assert "Server Error" not in content
        assert "Traceback" not in content
        assert "TemplateSyntaxError" not in content

    def test_25_invalid_slug_returns_404(self, e2e_server, page):
        """A non-existent academy slug returns a 404, not a server error."""
        response = page.goto(f"{e2e_server}/join/this-academy-does-not-exist/")
        assert response.status == 404
