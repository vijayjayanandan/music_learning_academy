from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string

from apps.notifications.models import Notification

from .models import AssignmentSubmission, Enrollment


@receiver(post_save, sender=Enrollment)
def notify_enrollment_created(sender, instance, created, **kwargs):
    if not created:
        return

    # Notify instructor
    instructor = instance.course.instructor
    student_name = instance.student.get_full_name() or instance.student.email

    # Always create in-app notification for the instructor
    Notification.objects.create(
        recipient=instructor,
        academy=instance.academy,
        notification_type="enrollment",
        title=f"New enrollment in {instance.course.title}",
        message=f"{student_name} enrolled in your course.",
        link=f"/courses/{instance.course.slug}/",
    )

    # Send HTML email if instructor has email preference enabled
    if instructor.wants_email("enrollment_created"):
        enrolled_count = Enrollment.objects.filter(
            course=instance.course,
            status__in=["active", "completed"],
        ).count()

        html_message = render_to_string(
            "emails/enrollment_notification_instructor_email.html",
            {
                "instructor_first_name": instructor.first_name,
                "student_name": student_name,
                "student_email": instance.student.email,
                "course": instance.course,
                "course_url": f"/courses/{instance.course.slug}/",
                "enrolled_count": enrolled_count,
            },
        )
        send_mail(
            subject=f"New enrollment: {student_name} in {instance.course.title}",
            message=f"{student_name} has enrolled in your course '{instance.course.title}'.",
            from_email=None,
            recipient_list=[instructor.email],
            html_message=html_message,
            fail_silently=True,
        )

    # Send enrollment confirmation to student
    student = instance.student
    if student.wants_email("enrollment_confirmation"):
        html_message = render_to_string(
            "emails/enrollment_confirmation_email.html",
            {
                "user": student,
                "course": instance.course,
                "course_url": f"/courses/{instance.course.slug}/",
            },
        )
        send_mail(
            subject=f"Welcome to {instance.course.title}!",
            message=f"You've been enrolled in {instance.course.title}.",
            from_email=None,
            recipient_list=[student.email],
            html_message=html_message,
            fail_silently=True,
        )


@receiver(post_save, sender=AssignmentSubmission)
def notify_submission(sender, instance, created, **kwargs):
    if created:
        # Notify instructor of new submission
        instructor = instance.assignment.lesson.course.instructor
        if instructor.wants_email("assignment_submitted"):
            course = instance.assignment.lesson.course
            html_message = render_to_string(
                "emails/assignment_submitted_email.html",
                {
                    "instructor": instructor,
                    "student": instance.student,
                    "assignment": instance.assignment,
                    "course": course,
                    "lesson_url": f"/courses/{course.slug}/lessons/{instance.assignment.lesson.pk}/",
                },
            )
            send_mail(
                subject=f"New submission: {instance.student.get_full_name()} - {instance.assignment.title}",
                message=f"{instance.student.get_full_name() or instance.student.email} submitted "
                f"'{instance.assignment.title}'.",
                from_email=None,
                recipient_list=[instructor.email],
                html_message=html_message,
                fail_silently=True,
            )
    elif instance.status in ("reviewed", "approved") and instance.reviewed_by:
        # Notify student of graded assignment
        student = instance.student
        if student.wants_email("assignment_graded"):
            course = instance.assignment.lesson.course
            html_message = render_to_string(
                "emails/assignment_graded_email.html",
                {
                    "student": student,
                    "assignment": instance.assignment,
                    "grade": instance.grade,
                    "course": course,
                    "feedback_url": f"/courses/{course.slug}/",
                },
            )
            send_mail(
                subject=f"Assignment graded: {instance.assignment.title}",
                message=f"Your submission for '{instance.assignment.title}' has been reviewed. "
                f"Grade: {instance.grade or 'See feedback'}.",
                from_email=None,
                recipient_list=[student.email],
                html_message=html_message,
                fail_silently=True,
            )
