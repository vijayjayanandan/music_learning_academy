from django.urls import path
from . import views

urlpatterns = [
    path("", views.MyEnrollmentsView.as_view(), name="enrollment-list"),
    path("<int:pk>/", views.EnrollmentDetailView.as_view(), name="enrollment-detail"),
    path("<int:pk>/lesson/<int:lesson_pk>/complete/", views.MarkLessonCompleteView.as_view(), name="mark-lesson-complete"),
    path("<int:pk>/submit/<int:assignment_pk>/", views.SubmitAssignmentView.as_view(), name="submit-assignment"),
    # Enroll/unenroll via course slug
    path("enroll/<slug:slug>/", views.EnrollView.as_view(), name="enroll"),
    path("unenroll/<slug:slug>/", views.UnenrollView.as_view(), name="unenroll"),
]
