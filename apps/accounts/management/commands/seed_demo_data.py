from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import User, Membership
from apps.academies.models import Academy
from apps.courses.models import Course, Lesson, PracticeAssignment
from apps.enrollments.models import Enrollment
from apps.scheduling.models import LiveSession
from apps.scheduling.jitsi import generate_jitsi_room_name


class Command(BaseCommand):
    help = "Seed the database with demo data for the Music Learning Academy PoC"

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")

        # Create Academy
        academy, _ = Academy.objects.get_or_create(
            slug="harmony-music-school",
            defaults={
                "name": "Harmony Music School",
                "description": "A premier music school offering courses in piano, guitar, violin, and vocals.",
                "email": "info@harmonymusic.com",
                "timezone": "UTC",
                "primary_instruments": ["Piano", "Guitar", "Violin", "Vocals", "Drums"],
                "genres": ["Classical", "Jazz", "Rock", "Pop", "Indian Classical"],
            },
        )
        self.stdout.write(f"  Academy: {academy.name}")

        # Create Users
        admin_user = self._create_user("admin@harmonymusic.com", "Admin", "User", "admin123")
        instructor1 = self._create_user("sarah@harmonymusic.com", "Sarah", "Johnson", "instructor123")
        instructor2 = self._create_user("david@harmonymusic.com", "David", "Chen", "instructor123")
        student1 = self._create_user("alice@example.com", "Alice", "Smith", "student123")
        student2 = self._create_user("bob@example.com", "Bob", "Wilson", "student123")
        student3 = self._create_user("carol@example.com", "Carol", "Davis", "student123")

        # Set current academy for all users
        for user in [admin_user, instructor1, instructor2, student1, student2, student3]:
            user.current_academy = academy
            user.save(update_fields=["current_academy"])

        # Create Memberships
        self._create_membership(admin_user, academy, "owner")
        self._create_membership(instructor1, academy, "instructor", ["Piano", "Music Theory"])
        self._create_membership(instructor2, academy, "instructor", ["Guitar", "Bass Guitar"])
        self._create_membership(student1, academy, "student", ["Piano"], "beginner")
        self._create_membership(student2, academy, "student", ["Guitar"], "intermediate")
        self._create_membership(student3, academy, "student", ["Piano", "Vocals"], "beginner")

        # Create Courses
        piano_course = self._create_course(
            academy, instructor1,
            "Piano Fundamentals",
            "Learn piano from scratch. Master hand position, reading notes, and playing your first songs.",
            "Piano", "Classical", "beginner",
            ["Read treble and bass clef", "Play major scales", "Perform simple pieces"],
        )

        guitar_course = self._create_course(
            academy, instructor2,
            "Guitar for Beginners",
            "Start your guitar journey. Learn chords, strumming patterns, and popular songs.",
            "Guitar", "Rock", "beginner",
            ["Play open chords", "Strumming patterns", "Play 5 complete songs"],
        )

        jazz_course = self._create_course(
            academy, instructor1,
            "Jazz Piano Improvisation",
            "Explore jazz harmony, chord voicings, and improvisation techniques.",
            "Piano", "Jazz", "intermediate",
            ["Jazz chord voicings", "ii-V-I progressions", "Basic improvisation"],
        )

        # Create Lessons for Piano Fundamentals
        lessons_data = [
            ("Introduction to the Piano", "Learn about the piano keyboard layout, posture, and hand position.", 30),
            ("Reading Music - Treble Clef", "Introduction to music notation and reading notes on the treble clef.", 45),
            ("Reading Music - Bass Clef", "Reading notes on the bass clef and combining both hands.", 45),
            ("Major Scales - C, G, D", "Learn and practice the C, G, and D major scales.", 40),
            ("Your First Song - Twinkle Twinkle", "Learn to play Twinkle Twinkle Little Star with both hands.", 30),
            ("Rhythm and Time Signatures", "Understanding 4/4, 3/4, and 2/4 time signatures.", 35),
            ("Chords - Major Triads", "Learn C, F, and G major chords and chord progressions.", 45),
            ("Playing with Expression", "Dynamics, tempo, and musical expression techniques.", 40),
        ]
        for i, (title, desc, duration) in enumerate(lessons_data, 1):
            self._create_lesson(academy, piano_course, title, desc, i, duration)

        # Create Lessons for Guitar course
        guitar_lessons = [
            ("Getting Started - Parts of the Guitar", "Learn guitar anatomy, holding position, and tuning.", 25),
            ("Open Chords - E, A, D", "Master your first three open chords.", 40),
            ("Open Chords - C, G, Em, Am", "Expand your chord vocabulary.", 40),
            ("Strumming Patterns", "Learn basic strumming patterns and rhythm.", 35),
            ("Your First Song", "Put chords and strumming together to play a complete song.", 30),
        ]
        for i, (title, desc, duration) in enumerate(guitar_lessons, 1):
            self._create_lesson(academy, guitar_course, title, desc, i, duration)

        # Create Practice Assignments
        piano_lesson1 = piano_course.lessons.first()
        if piano_lesson1:
            PracticeAssignment.objects.get_or_create(
                academy=academy,
                lesson=piano_lesson1,
                title="Hand Position Practice",
                defaults={
                    "description": "Practice correct hand position at the piano for 15 minutes daily.",
                    "assignment_type": "technique",
                    "practice_minutes_target": 15,
                    "instructions": "Sit at the piano with relaxed shoulders. Curve your fingers naturally. Practice placing each finger on C-D-E-F-G.",
                    "due_date": timezone.now() + timedelta(days=7),
                },
            )

        # Create Enrollments
        Enrollment.objects.get_or_create(
            student=student1, course=piano_course, academy=academy
        )
        Enrollment.objects.get_or_create(
            student=student2, course=guitar_course, academy=academy
        )
        Enrollment.objects.get_or_create(
            student=student3, course=piano_course, academy=academy
        )

        # Create Live Sessions
        now = timezone.now()
        self._create_session(
            academy, instructor1,
            "Piano Group Lesson - Scales Practice",
            piano_course,
            now + timedelta(days=1, hours=2),
            60, "group", 10,
        )
        self._create_session(
            academy, instructor2,
            "Guitar One-on-One with Bob",
            guitar_course,
            now + timedelta(days=2, hours=3),
            45, "one_on_one", 1,
        )
        self._create_session(
            academy, instructor1,
            "Jazz Masterclass - Chord Voicings",
            jazz_course,
            now + timedelta(days=3, hours=4),
            90, "masterclass", 20,
        )

        self.stdout.write(self.style.SUCCESS("\nDemo data seeded successfully!"))
        self.stdout.write(self.style.SUCCESS("\nLogin credentials:"))
        self.stdout.write(f"  Admin:      admin@harmonymusic.com / admin123")
        self.stdout.write(f"  Instructor: sarah@harmonymusic.com / instructor123")
        self.stdout.write(f"  Instructor: david@harmonymusic.com / instructor123")
        self.stdout.write(f"  Student:    alice@example.com / student123")
        self.stdout.write(f"  Student:    bob@example.com / student123")
        self.stdout.write(f"  Student:    carol@example.com / student123")

    def _create_user(self, email, first_name, last_name, password):
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email.split("@")[0],
                "first_name": first_name,
                "last_name": last_name,
            },
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(f"  User: {email}")
        return user

    def _create_membership(self, user, academy, role, instruments=None, skill_level="professional"):
        Membership.objects.get_or_create(
            user=user,
            academy=academy,
            defaults={
                "role": role,
                "instruments": instruments or [],
                "skill_level": skill_level,
            },
        )

    def _create_course(self, academy, instructor, title, description, instrument, genre, difficulty, outcomes):
        from django.utils.text import slugify
        course, created = Course.objects.get_or_create(
            academy=academy,
            slug=slugify(title),
            defaults={
                "title": title,
                "description": description,
                "instructor": instructor,
                "instrument": instrument,
                "genre": genre,
                "difficulty_level": difficulty,
                "learning_outcomes": outcomes,
                "is_published": True,
                "published_at": timezone.now(),
            },
        )
        if created:
            self.stdout.write(f"  Course: {title}")
        return course

    def _create_lesson(self, academy, course, title, description, order, duration):
        Lesson.objects.get_or_create(
            academy=academy,
            course=course,
            order=order,
            defaults={
                "title": title,
                "description": description,
                "estimated_duration_minutes": duration,
                "is_published": True,
                "content": f"## {title}\n\n{description}\n\nDetailed lesson content goes here.",
            },
        )

    def _create_session(self, academy, instructor, title, course, start_time, duration, session_type, max_participants):
        room_name = generate_jitsi_room_name(academy.slug, f"{title[:10]}-{start_time.timestamp()}")
        LiveSession.objects.get_or_create(
            academy=academy,
            jitsi_room_name=room_name,
            defaults={
                "title": title,
                "instructor": instructor,
                "course": course,
                "scheduled_start": start_time,
                "scheduled_end": start_time + timedelta(minutes=duration),
                "duration_minutes": duration,
                "session_type": session_type,
                "max_participants": max_participants,
            },
        )
        self.stdout.write(f"  Session: {title}")
