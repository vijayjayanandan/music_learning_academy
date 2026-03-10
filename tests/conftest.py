import pytest
from apps.accounts.models import User, Membership
from apps.academies.models import Academy


@pytest.fixture
def academy(db):
    return Academy.objects.create(
        name="Test Music Academy",
        slug="test-academy",
        description="A test academy",
        email="test@academy.com",
        timezone="UTC",
        primary_instruments=["Piano", "Guitar"],
        genres=["Classical", "Jazz"],
    )


@pytest.fixture
def owner_user(db, academy):
    user = User.objects.create_user(
        username="owner",
        email="owner@test.com",
        password="testpass123",
        first_name="Test",
        last_name="Owner",
    )
    user.current_academy = academy
    user.save()
    Membership.objects.create(user=user, academy=academy, role="owner")
    return user


@pytest.fixture
def instructor_user(db, academy):
    user = User.objects.create_user(
        username="instructor",
        email="instructor@test.com",
        password="testpass123",
        first_name="Test",
        last_name="Instructor",
    )
    user.current_academy = academy
    user.save()
    Membership.objects.create(
        user=user, academy=academy, role="instructor",
        instruments=["Piano"],
    )
    return user


@pytest.fixture
def student_user(db, academy):
    user = User.objects.create_user(
        username="student",
        email="student@test.com",
        password="testpass123",
        first_name="Test",
        last_name="Student",
    )
    user.current_academy = academy
    user.save()
    Membership.objects.create(
        user=user, academy=academy, role="student",
        instruments=["Piano"], skill_level="beginner",
    )
    return user


@pytest.fixture
def auth_client(client, owner_user):
    client.force_login(owner_user)
    return client
