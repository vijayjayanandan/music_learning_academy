"""Tests for the 3-step Book Session wizard (HTMX-powered).

Covers:
- Instructor card grid display
- Slot partial loading via HTMX
- Confirmation partial rendering
- Session + attendance creation on booking
- Custom/default title handling
- Validation: past dates, wrong day-of-week, double-booking
- Permission: login required, cross-tenant instructor/slot rejection
- Empty states: no instructors, no slots
- Partial responses: no <!DOCTYPE in HTMX partials
"""

import datetime

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.academies.models import Academy
from apps.accounts.models import User, Membership
from apps.scheduling.models import LiveSession, SessionAttendance, InstructorAvailability
from apps.scheduling.jitsi import generate_room_name


def _next_weekday(day_of_week):
    """Return the next date matching the given Python weekday (Mon=0 ... Sun=6)."""
    today = datetime.date.today()
    days_ahead = day_of_week - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + datetime.timedelta(days=days_ahead)


@pytest.mark.integration
class TestBookSessionWizard(TestCase):
    """Integration tests for the Book Session 3-step wizard."""

    @classmethod
    def setUpTestData(cls):
        # --- Academy 1 (main) ---
        cls.academy = Academy.objects.create(
            name="Book Session Academy",
            slug="booksess-acad",
            description="Test academy for booking",
            email="booksess@academy.com",
            timezone="UTC",
            primary_instruments=["Piano", "Guitar"],
            genres=["Classical"],
        )
        cls.owner_user = User.objects.create_user(
            username="booksess-owner",
            email="booksess-owner@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Owner",
        )
        cls.owner_user.current_academy = cls.academy
        cls.owner_user.save()
        Membership.objects.create(
            user=cls.owner_user, academy=cls.academy, role="owner",
        )

        cls.instructor_user = User.objects.create_user(
            username="booksess-instructor",
            email="booksess-instructor@test.com",
            password="testpass123",
            first_name="Sarah",
            last_name="Music",
        )
        cls.instructor_user.current_academy = cls.academy
        cls.instructor_user.save()
        Membership.objects.create(
            user=cls.instructor_user, academy=cls.academy, role="instructor",
            instruments=["Piano", "Vocals"],
            bio="Professional piano instructor with 10 years of experience.",
        )

        cls.student_user = User.objects.create_user(
            username="booksess-student",
            email="booksess-student@test.com",
            password="testpass123",
            first_name="Alice",
            last_name="Learner",
        )
        cls.student_user.current_academy = cls.academy
        cls.student_user.save()
        Membership.objects.create(
            user=cls.student_user, academy=cls.academy, role="student",
            instruments=["Piano"], skill_level="beginner",
        )

        # Instructor availability: Monday 10:00-11:00
        cls.slot = InstructorAvailability.objects.create(
            instructor=cls.instructor_user,
            academy=cls.academy,
            day_of_week=0,  # Monday
            start_time=datetime.time(10, 0),
            end_time=datetime.time(11, 0),
            is_active=True,
        )

        # --- Academy 2 (cross-tenant) ---
        cls.academy2 = Academy.objects.create(
            name="Other Academy",
            slug="booksess-other",
            description="Second academy for cross-tenant tests",
            email="booksess-other@academy.com",
            timezone="UTC",
            primary_instruments=["Violin"],
            genres=["Jazz"],
        )
        cls.instructor2 = User.objects.create_user(
            username="booksess-instructor2",
            email="booksess-instructor2@test.com",
            password="testpass123",
            first_name="David",
            last_name="Violin",
        )
        cls.instructor2.current_academy = cls.academy2
        cls.instructor2.save()
        Membership.objects.create(
            user=cls.instructor2, academy=cls.academy2, role="instructor",
            instruments=["Violin"],
        )
        cls.slot2 = InstructorAvailability.objects.create(
            instructor=cls.instructor2,
            academy=cls.academy2,
            day_of_week=2,  # Wednesday
            start_time=datetime.time(14, 0),
            end_time=datetime.time(15, 0),
            is_active=True,
        )

    def setUp(self):
        self.client = Client()

    def _login_student(self):
        self.client.login(
            username="booksess-student@test.com", password="testpass123",
        )

    def _next_monday(self):
        return _next_weekday(0)

    def _valid_post_data(self, **overrides):
        data = {
            "instructor": self.instructor_user.pk,
            "slot": self.slot.pk,
            "session_date": self._next_monday().strftime("%Y-%m-%d"),
        }
        data.update(overrides)
        return data

    # --- 1. Page shows instructor cards ---
    def test_page_shows_instructor_cards(self):
        """GET /schedule/book/ shows instructor name and instrument badges."""
        self._login_student()
        response = self.client.get(reverse("book-session"))
        content = response.content.decode()
        assert response.status_code == 200
        assert "Sarah" in content
        assert "Music" in content
        assert "Piano" in content

    # --- 2. Slots partial loads ---
    def test_slots_partial_loads(self):
        """GET /schedule/book/slots/?instructor=ID returns slot day+time."""
        self._login_student()
        url = reverse("book-session-slots") + f"?instructor={self.instructor_user.pk}"
        response = self.client.get(url)
        content = response.content.decode()
        assert response.status_code == 200
        assert "Monday" in content
        assert "10:00" in content

    # --- 3. Confirm partial shows summary ---
    def test_confirm_partial_shows_summary(self):
        """POST /schedule/book/confirm/ with valid data shows instructor name + date."""
        self._login_student()
        next_monday = self._next_monday()
        data = {
            "instructor": self.instructor_user.pk,
            "slot": self.slot.pk,
            "session_date": next_monday.strftime("%Y-%m-%d"),
        }
        response = self.client.post(reverse("book-session-confirm"), data)
        content = response.content.decode()
        assert response.status_code == 200
        assert "Sarah" in content
        assert next_monday.strftime("%Y") in content

    # --- 4. Booking creates session and attendance ---
    def test_booking_creates_session_and_attendance(self):
        """POST /schedule/book/ creates LiveSession + SessionAttendance, redirects to detail."""
        self._login_student()
        data = self._valid_post_data()
        response = self.client.post(reverse("book-session"), data)

        assert response.status_code == 302
        session = LiveSession.objects.filter(
            academy=self.academy,
            instructor=self.instructor_user,
        ).last()
        assert session is not None
        assert session.session_type == "one_on_one"
        assert SessionAttendance.objects.filter(
            session=session, student=self.student_user,
        ).exists()
        assert response.url == reverse("session-detail", args=[session.pk])

    # --- 5. Custom title ---
    def test_custom_title(self):
        """POST with session_title='My Guitar Lesson' uses the custom title."""
        self._login_student()
        data = self._valid_post_data(session_title="My Guitar Lesson")
        self.client.post(reverse("book-session"), data)

        session = LiveSession.objects.filter(academy=self.academy).last()
        assert session.title == "My Guitar Lesson"

    # --- 6. Default title when blank ---
    def test_default_title_when_blank(self):
        """POST without session_title uses 'Lesson with <instructor name>'."""
        self._login_student()
        data = self._valid_post_data()
        # No session_title key at all
        self.client.post(reverse("book-session"), data)

        session = LiveSession.objects.filter(academy=self.academy).last()
        assert session.title.startswith("Lesson with")

    # --- 7. Success message ---
    def test_success_message(self):
        """POST valid booking, follow redirect, check 'Session booked' in messages."""
        self._login_student()
        data = self._valid_post_data()
        response = self.client.post(reverse("book-session"), data, follow=True)
        content = response.content.decode()
        assert "Session booked" in content

    # --- 8. Rejects past date ---
    def test_rejects_past_date(self):
        """POST with yesterday's date returns error."""
        self._login_student()
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        # Find a past date that also matches Monday so we specifically test past-date logic
        # Use any past Monday
        days_since_monday = (yesterday.weekday() - 0) % 7
        past_monday = yesterday - datetime.timedelta(days=days_since_monday)
        if past_monday >= datetime.date.today():
            past_monday -= datetime.timedelta(days=7)
        data = self._valid_post_data(session_date=past_monday.strftime("%Y-%m-%d"))
        response = self.client.post(reverse("book-session"), data)
        content = response.content.decode()
        assert response.status_code == 200
        assert "past" in content.lower()

    # --- 9. Rejects wrong day of week ---
    def test_rejects_wrong_day_of_week(self):
        """POST with a date that is not the slot's day returns error."""
        self._login_student()
        # Slot is Monday (0), pick the next Tuesday (1)
        next_tuesday = _next_weekday(1)
        data = self._valid_post_data(session_date=next_tuesday.strftime("%Y-%m-%d"))
        response = self.client.post(reverse("book-session"), data)
        content = response.content.decode()
        assert response.status_code == 200
        assert "does not match" in content

    # --- 10. Rejects double booking ---
    def test_rejects_double_booking(self):
        """POST with same instructor/time as an existing session returns error."""
        self._login_student()
        next_monday = self._next_monday()
        # Create an existing session at the same slot
        start_dt = timezone.make_aware(
            datetime.datetime.combine(next_monday, datetime.time(10, 0))
        )
        end_dt = timezone.make_aware(
            datetime.datetime.combine(next_monday, datetime.time(11, 0))
        )
        LiveSession.objects.create(
            title="Existing Booking",
            instructor=self.instructor_user,
            academy=self.academy,
            scheduled_start=start_dt,
            scheduled_end=end_dt,
            session_type="one_on_one",
            room_name=generate_room_name(self.academy.slug, 9999),
            status="scheduled",
        )
        data = self._valid_post_data()
        response = self.client.post(reverse("book-session"), data)
        content = response.content.decode()
        assert response.status_code == 200
        assert "already booked" in content.lower()

    # --- 11. Requires login ---
    def test_requires_login(self):
        """GET as anonymous user redirects to login."""
        response = self.client.get(reverse("book-session"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    # --- 12. Rejects instructor from other academy ---
    def test_rejects_instructor_from_other_academy(self):
        """POST with instructor from academy2 returns 403."""
        self._login_student()
        data = self._valid_post_data(instructor=self.instructor2.pk)
        response = self.client.post(reverse("book-session"), data)
        assert response.status_code == 403

    # --- 13. Rejects slot from other academy ---
    def test_rejects_slot_from_other_academy(self):
        """POST with slot from academy2 returns 404."""
        self._login_student()
        data = self._valid_post_data(slot=self.slot2.pk)
        response = self.client.post(reverse("book-session"), data)
        assert response.status_code == 404

    # --- 14. Empty state: no instructors ---
    def test_empty_state_no_instructors(self):
        """GET page with no instructors shows 'No Instructors' message."""
        # Create a student in academy2 (which has no instructors in student's view)
        empty_academy = Academy.objects.create(
            name="Empty Academy",
            slug="booksess-empty",
            description="No instructors",
            email="booksess-empty@academy.com",
            timezone="UTC",
            primary_instruments=["Piano"],
            genres=["Classical"],
        )
        lonely_student = User.objects.create_user(
            username="booksess-lonely",
            email="booksess-lonely@test.com",
            password="testpass123",
        )
        lonely_student.current_academy = empty_academy
        lonely_student.save()
        Membership.objects.create(
            user=lonely_student, academy=empty_academy, role="student",
        )
        self.client.login(
            username="booksess-lonely@test.com", password="testpass123",
        )
        response = self.client.get(reverse("book-session"))
        content = response.content.decode()
        assert response.status_code == 200
        assert "No Instructors" in content

    # --- 15. Slots empty state ---
    def test_slots_empty_state(self):
        """GET slots partial for instructor with no slots shows empty message."""
        self._login_student()
        # Create instructor with no availability
        no_slots_instructor = User.objects.create_user(
            username="booksess-noslots",
            email="booksess-noslots@test.com",
            password="testpass123",
            first_name="NoSlots",
            last_name="Instructor",
        )
        no_slots_instructor.current_academy = self.academy
        no_slots_instructor.save()
        Membership.objects.create(
            user=no_slots_instructor, academy=self.academy, role="instructor",
        )
        url = reverse("book-session-slots") + f"?instructor={no_slots_instructor.pk}"
        response = self.client.get(url)
        content = response.content.decode()
        assert response.status_code == 200
        assert "No Available Slots" in content

    # --- 16. Slots is partial (no <!DOCTYPE) ---
    def test_slots_is_partial(self):
        """GET slots response does NOT contain <!DOCTYPE (it's a partial)."""
        self._login_student()
        url = reverse("book-session-slots") + f"?instructor={self.instructor_user.pk}"
        response = self.client.get(url)
        content = response.content.decode()
        assert "<!DOCTYPE" not in content

    # --- 17. Confirm is partial (no <!DOCTYPE) ---
    def test_confirm_is_partial(self):
        """POST confirm response does NOT contain <!DOCTYPE (it's a partial)."""
        self._login_student()
        next_monday = self._next_monday()
        data = {
            "instructor": self.instructor_user.pk,
            "slot": self.slot.pk,
            "session_date": next_monday.strftime("%Y-%m-%d"),
        }
        response = self.client.post(reverse("book-session-confirm"), data)
        content = response.content.decode()
        assert "<!DOCTYPE" not in content
