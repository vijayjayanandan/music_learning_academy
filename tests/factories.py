"""Factory Boy factories for test data generation."""

import factory
from django.utils import timezone


class AcademyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "academies.Academy"

    name = factory.Sequence(lambda n: f"Test Academy {n}")
    slug = factory.Sequence(lambda n: f"test-academy-{n}")
    description = "A test academy"
    email = factory.LazyAttribute(lambda o: f"{o.slug}@example.com")
    timezone = "UTC"
    primary_instruments = ["Piano", "Guitar"]
    genres = ["Classical", "Jazz"]


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "accounts.User"

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@test.com")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")
    first_name = "Test"
    last_name = "User"


class MembershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "accounts.Membership"

    user = factory.SubFactory(UserFactory)
    academy = factory.SubFactory(AcademyFactory)
    role = "student"
    is_active = True


class CourseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "courses.Course"

    academy = factory.SubFactory(AcademyFactory)
    title = factory.Sequence(lambda n: f"Test Course {n}")
    slug = factory.Sequence(lambda n: f"test-course-{n}")
    description = "A test course"
    instructor = factory.SubFactory(UserFactory)
    instrument = "Piano"
    difficulty_level = "beginner"
    is_published = True


class LessonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "courses.Lesson"

    academy = factory.LazyAttribute(lambda o: o.course.academy)
    course = factory.SubFactory(CourseFactory)
    title = factory.Sequence(lambda n: f"Lesson {n}")
    order = factory.Sequence(lambda n: n)


class PracticeAssignmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "courses.PracticeAssignment"

    academy = factory.LazyAttribute(lambda o: o.lesson.academy)
    lesson = factory.SubFactory(LessonFactory)
    title = factory.Sequence(lambda n: f"Assignment {n}")
    description = "Test assignment"
    assignment_type = "practice"
    due_date = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=7))


class EnrollmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "enrollments.Enrollment"

    academy = factory.LazyAttribute(lambda o: o.course.academy)
    student = factory.SubFactory(UserFactory)
    course = factory.SubFactory(CourseFactory)
    status = "active"


class SubscriptionPlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "payments.SubscriptionPlan"

    academy = factory.SubFactory(AcademyFactory)
    name = factory.Sequence(lambda n: f"Plan {n}")
    price_cents = 2999
    billing_cycle = "monthly"
    is_active = True


class SubscriptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "payments.Subscription"

    academy = factory.LazyAttribute(lambda o: o.plan.academy)
    student = factory.SubFactory(UserFactory)
    plan = factory.SubFactory(SubscriptionPlanFactory)
    status = "active"
    stripe_subscription_id = factory.Sequence(lambda n: f"sub_test_{n}")


class PaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "payments.Payment"

    academy = factory.SubFactory(AcademyFactory)
    student = factory.SubFactory(UserFactory)
    amount_cents = 2999
    payment_type = "subscription"
    status = "completed"
    paid_at = factory.LazyFunction(timezone.now)


class CouponFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "payments.Coupon"

    academy = factory.SubFactory(AcademyFactory)
    code = factory.Sequence(lambda n: f"TEST{n}")
    discount_type = "percentage"
    discount_value = 20
    is_active = True


class PackageDealFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "payments.PackageDeal"

    academy = factory.SubFactory(AcademyFactory)
    name = factory.Sequence(lambda n: f"Package {n}")
    price_cents = 9999
    total_credits = 10
    is_active = True


class PracticeLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "practice.PracticeLog"

    academy = factory.SubFactory(AcademyFactory)
    student = factory.SubFactory(UserFactory)
    date = factory.LazyFunction(lambda: timezone.now().date())
    duration_minutes = 30
    instrument = "Piano"


class LiveSessionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "scheduling.LiveSession"

    academy = factory.SubFactory(AcademyFactory)
    title = factory.Sequence(lambda n: f"Session {n}")
    instructor = factory.SubFactory(UserFactory)
    scheduled_start = factory.LazyFunction(
        lambda: timezone.now() + timezone.timedelta(hours=1)
    )
    scheduled_end = factory.LazyFunction(
        lambda: timezone.now() + timezone.timedelta(hours=2)
    )
    session_type = "one_on_one"
    room_name = factory.Sequence(lambda n: f"room-{n}")
