import pytest
from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.courses.models import Course, Lesson


@pytest.mark.unit
class TestUserModel:
    def test_create_user(self, db):
        user = User.objects.create_user(
            username="test", email="test@test.com", password="pass123"
        )
        assert user.email == "test@test.com"
        assert user.check_password("pass123")
        assert user.USERNAME_FIELD == "email"

    def test_get_role_in_academy(self, owner_user, academy):
        assert owner_user.get_role_in(academy) == "owner"

    def test_get_academies(self, owner_user, academy):
        academies = owner_user.get_academies()
        assert academy in academies


@pytest.mark.unit
class TestAcademyModel:
    def test_create_academy(self, academy):
        assert academy.name == "Test Music Academy"
        assert academy.slug == "test-academy"
        assert academy.is_active is True

    def test_str(self, academy):
        assert str(academy) == "Test Music Academy"


@pytest.mark.unit
class TestMembershipModel:
    def test_membership_role(self, owner_user, academy):
        membership = Membership.objects.get(user=owner_user, academy=academy)
        assert membership.role == "owner"

    def test_unique_user_academy(self, owner_user, academy):
        with pytest.raises(Exception):
            Membership.objects.create(
                user=owner_user, academy=academy, role="student"
            )


@pytest.mark.unit
class TestCourseModel:
    def test_create_course(self, db, academy, instructor_user):
        course = Course.objects.create(
            academy=academy,
            title="Piano 101",
            slug="piano-101",
            instructor=instructor_user,
            instrument="Piano",
            difficulty_level="beginner",
            is_published=True,
        )
        assert course.title == "Piano 101"
        assert course.lesson_count == 0
        assert course.enrolled_count == 0

    def test_lesson_ordering(self, db, academy, instructor_user):
        course = Course.objects.create(
            academy=academy, title="Test Course", slug="test-course",
            instructor=instructor_user, instrument="Piano",
            difficulty_level="beginner", is_published=True,
        )
        lesson2 = Lesson.objects.create(
            academy=academy, course=course, title="Lesson 2", order=2,
        )
        lesson1 = Lesson.objects.create(
            academy=academy, course=course, title="Lesson 1", order=1,
        )
        lessons = list(course.lessons.all())
        assert lessons[0] == lesson1
        assert lessons[1] == lesson2
