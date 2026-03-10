from django.urls import path
from . import views

urlpatterns = [
    path("", views.CourseListView.as_view(), name="course-list"),
    path("create/", views.CourseCreateView.as_view(), name="course-create"),
    path("<slug:slug>/", views.CourseDetailView.as_view(), name="course-detail"),
    path("<slug:slug>/edit/", views.CourseEditView.as_view(), name="course-edit"),
    path("<slug:slug>/delete/", views.CourseDeleteView.as_view(), name="course-delete"),
    # Lessons
    path(
        "<slug:slug>/lessons/create/",
        views.LessonCreateView.as_view(),
        name="lesson-create",
    ),
    path(
        "<slug:slug>/lessons/<int:pk>/",
        views.LessonDetailView.as_view(),
        name="lesson-detail",
    ),
    path(
        "<slug:slug>/lessons/<int:pk>/edit/",
        views.LessonEditView.as_view(),
        name="lesson-edit",
    ),
    path(
        "<slug:slug>/lessons/<int:pk>/delete/",
        views.LessonDeleteView.as_view(),
        name="lesson-delete",
    ),
    # Assignments
    path(
        "<slug:slug>/lessons/<int:lesson_pk>/assignments/<int:pk>/edit/",
        views.AssignmentEditView.as_view(),
        name="assignment-edit",
    ),
    path(
        "<slug:slug>/lessons/<int:lesson_pk>/assignments/<int:pk>/delete/",
        views.AssignmentDeleteView.as_view(),
        name="assignment-delete",
    ),
    # Attachments
    path(
        "<slug:slug>/lessons/<int:pk>/attachments/upload/",
        views.AttachmentUploadView.as_view(),
        name="attachment-upload",
    ),
    path(
        "<slug:slug>/lessons/<int:pk>/attachments/<int:attachment_pk>/delete/",
        views.AttachmentDeleteView.as_view(),
        name="attachment-delete",
    ),
]
