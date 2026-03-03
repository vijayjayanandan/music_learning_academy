from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import AssignmentSubmission, Enrollment


@receiver(post_save, sender=Enrollment)
def notify_enrollment_created(sender, instance, created, **kwargs):
    if not created:
        return
    instructor = instance.course.instructor
    if not instructor.wants_email("enrollment_created"):
        return
    send_mail(
        subject=f"New enrollment: {instance.student.get_full_name()} in {instance.course.title}",
        message=f"{instance.student.get_full_name() or instance.student.email} has enrolled in "
                f"your course '{instance.course.title}'.",
        from_email=None,
        recipient_list=[instructor.email],
        fail_silently=True,
    )


@receiver(post_save, sender=AssignmentSubmission)
def notify_submission(sender, instance, created, **kwargs):
    if created:
        # Notify instructor of new submission
        instructor = instance.assignment.lesson.course.instructor
        if instructor.wants_email("assignment_submitted"):
            send_mail(
                subject=f"New submission: {instance.student.get_full_name()} - {instance.assignment.title}",
                message=f"{instance.student.get_full_name() or instance.student.email} submitted "
                        f"'{instance.assignment.title}'.",
                from_email=None,
                recipient_list=[instructor.email],
                fail_silently=True,
            )
    elif instance.status in ("reviewed", "approved") and instance.reviewed_by:
        # Notify student of graded assignment
        student = instance.student
        if student.wants_email("assignment_graded"):
            send_mail(
                subject=f"Assignment graded: {instance.assignment.title}",
                message=f"Your submission for '{instance.assignment.title}' has been reviewed. "
                        f"Grade: {instance.grade or 'See feedback'}.",
                from_email=None,
                recipient_list=[student.email],
                fail_silently=True,
            )
