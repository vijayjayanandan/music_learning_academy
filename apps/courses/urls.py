from django.urls import path
from . import views

urlpatterns = [
    path("", views.CourseListView.as_view(), name="course-list"),
    path("create/", views.CourseCreateView.as_view(), name="course-create"),
    path("<slug:slug>/", views.CourseDetailView.as_view(), name="course-detail"),
    path("<slug:slug>/edit/", views.CourseEditView.as_view(), name="course-edit"),
    path("<slug:slug>/delete/", views.CourseDeleteView.as_view(), name="course-delete"),
    # Lessons
    path("<slug:slug>/lessons/create/", views.LessonCreateView.as_view(), name="lesson-create"),
    path("<slug:slug>/lessons/<int:pk>/", views.LessonDetailView.as_view(), name="lesson-detail"),
    path("<slug:slug>/lessons/<int:pk>/edit/", views.LessonEditView.as_view(), name="lesson-edit"),
    path("<slug:slug>/lessons/<int:pk>/delete/", views.LessonDeleteView.as_view(), name="lesson-delete"),
]
