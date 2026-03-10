"""
File cleanup signals — delete R2/storage objects when models are deleted.

Registered in apps/common/apps.py via ready().
"""

import logging

from django.db import models
from django.db.models.signals import post_delete, pre_save

logger = logging.getLogger(__name__)

# Models with file fields that need cleanup on deletion
_FILE_FIELD_MODELS = []


def _register_file_cleanup(*model_classes):
    """Register post_delete handlers for models with file fields."""
    for model_class in model_classes:
        _FILE_FIELD_MODELS.append(model_class)


def _delete_file_fields(sender, instance, **kwargs):
    """Delete storage files when a model instance is deleted."""
    for field in instance._meta.get_fields():
        if isinstance(field, (models.FileField, models.ImageField)):
            file_obj = getattr(instance, field.name, None)
            if file_obj and file_obj.name:
                try:
                    file_obj.delete(save=False)
                    logger.info(
                        "Deleted file %s for %s pk=%s",
                        file_obj.name,
                        sender.__name__,
                        instance.pk,
                    )
                except Exception:
                    logger.exception(
                        "Failed to delete file %s for %s pk=%s",
                        file_obj.name,
                        sender.__name__,
                        instance.pk,
                    )


def _delete_old_file_on_update(sender, instance, **kwargs):
    """Delete the old file from storage when a file field is updated."""
    if not instance.pk:
        return
    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    for field in instance._meta.get_fields():
        if isinstance(field, (models.FileField, models.ImageField)):
            old_file = getattr(old_instance, field.name, None)
            new_file = getattr(instance, field.name, None)
            if old_file and old_file.name and old_file != new_file:
                try:
                    old_file.delete(save=False)
                    logger.info(
                        "Deleted old file %s on update for %s pk=%s",
                        old_file.name,
                        sender.__name__,
                        instance.pk,
                    )
                except Exception:
                    logger.exception(
                        "Failed to delete old file %s for %s pk=%s",
                        old_file.name,
                        sender.__name__,
                        instance.pk,
                    )


def connect_file_cleanup_signals():
    """Connect cleanup signals for all models with file fields.

    Called from CommonConfig.ready().
    """
    from apps.accounts.models import User
    from apps.academies.models import Academy
    from apps.courses.models import Course, LessonAttachment
    from apps.enrollments.models import AssignmentSubmission
    from apps.library.models import LibraryResource
    from apps.music_tools.models import PracticeAnalysis, RecordingArchive

    file_models = [
        User,
        Academy,
        Course,
        LessonAttachment,
        AssignmentSubmission,
        LibraryResource,
        PracticeAnalysis,
        RecordingArchive,
    ]
    for model in file_models:
        post_delete.connect(_delete_file_fields, sender=model)
        pre_save.connect(_delete_old_file_on_update, sender=model)
