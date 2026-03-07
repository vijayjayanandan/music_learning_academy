"""Management command to load pre-built course packs into an academy."""

import markdown
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from apps.academies.models import Academy
from apps.courses.models import Course, Lesson, PracticeAssignment

# Markdown converter with extensions for tables, fenced code, etc.
_md = markdown.Markdown(extensions=["tables", "fenced_code", "nl2br"])


class Command(BaseCommand):
    help = "Load pre-built course packs into an academy (creates template courses with full lesson content)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--academy",
            default="harmony-music-school",
            help="Academy slug to load courses into (default: harmony-music-school)",
        )
        parser.add_argument(
            "--packs",
            nargs="*",
            default=["hindustani_vocal"],
            help="Course packs to load (default: all). Options: hindustani_vocal, piano, guitar, carnatic_vocal, music_theory",
        )

    def handle(self, *args, **options):
        # Get the academy
        try:
            academy = Academy.objects.get(slug=options["academy"])
        except Academy.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                f"Academy '{options['academy']}' not found. Run seed_demo_data first."
            ))
            return

        # Get an instructor to assign courses to
        from apps.accounts.models import Membership
        instructor_membership = Membership.objects.filter(
            academy=academy, role="instructor"
        ).first()
        if not instructor_membership:
            # Fall back to owner
            instructor_membership = Membership.objects.filter(
                academy=academy, role="owner"
            ).first()
        if not instructor_membership:
            self.stderr.write(self.style.ERROR("No instructor or owner found in this academy."))
            return

        instructor = instructor_membership.user

        # Load requested packs
        pack_loaders = {
            "hindustani_vocal": self._load_hindustani_vocal,
        }

        packs_to_load = options["packs"]
        for pack_name in packs_to_load:
            if pack_name in pack_loaders:
                pack_loaders[pack_name](academy, instructor)
            else:
                self.stderr.write(self.style.WARNING(f"Unknown pack: {pack_name}"))

        self.stdout.write(self.style.SUCCESS("\nCourse packs loaded successfully!"))

    @staticmethod
    def _md_to_html(text):
        """Convert Markdown to HTML for storage (TinyMCE editor produces HTML)."""
        if not text:
            return ""
        _md.reset()
        return _md.convert(text)

    def _load_course_pack(self, academy, instructor, course_data, lessons_data):
        """Generic loader for any course pack."""
        slug = slugify(course_data["title"])
        course, created = Course.objects.get_or_create(
            academy=academy,
            slug=slug,
            defaults={
                "title": course_data["title"],
                "description": course_data["description"],
                "instructor": instructor,
                "instrument": course_data["instrument"],
                "genre": course_data.get("genre", ""),
                "difficulty_level": course_data["difficulty_level"],
                "prerequisites": course_data.get("prerequisites", ""),
                "learning_outcomes": course_data.get("learning_outcomes", []),
                "estimated_duration_weeks": course_data.get("estimated_duration_weeks", 12),
                "max_students": course_data.get("max_students", 30),
                "is_published": True,
                "published_at": timezone.now(),
                "is_template": True,
            },
        )

        if not created:
            self.stdout.write(f"  Course '{course.title}' already exists, skipping.")
            return course

        self.stdout.write(f"  Course: {course.title} ({len(lessons_data)} lessons)")

        for lesson_data in lessons_data:
            lesson = Lesson.objects.create(
                academy=academy,
                course=course,
                title=lesson_data["title"],
                description=lesson_data.get("description", ""),
                order=lesson_data["order"],
                content=self._md_to_html(lesson_data.get("content", "")),
                topics=lesson_data.get("topics", []),
                estimated_duration_minutes=lesson_data.get("estimated_duration_minutes", 30),
                is_published=True,
            )
            self.stdout.write(f"    Lesson {lesson.order}: {lesson.title}")

            for assignment_data in lesson_data.get("assignments", []):
                PracticeAssignment.objects.create(
                    academy=academy,
                    lesson=lesson,
                    title=assignment_data["title"],
                    description=assignment_data["description"],
                    assignment_type=assignment_data.get("type", "practice"),
                    practice_minutes_target=assignment_data.get("practice_minutes_target", 30),
                    tempo_bpm=assignment_data.get("tempo_bpm"),
                    instructions=assignment_data.get("instructions", ""),
                )
                self.stdout.write(f"      Assignment: {assignment_data['title']}")

        return course

    def _load_hindustani_vocal(self, academy, instructor):
        self.stdout.write("\nLoading: Hindustani Vocal Foundations...")
        from apps.courses.course_packs.hindustani_vocal import COURSE, LESSONS
        self._load_course_pack(academy, instructor, COURSE, LESSONS)
