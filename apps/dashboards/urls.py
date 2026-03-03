from django.urls import path
from . import views

urlpatterns = [
    path("", views.DashboardRedirectView.as_view(), name="dashboard"),
    path("dashboard/admin/", views.AdminDashboardView.as_view(), name="admin-dashboard"),
    path("dashboard/instructor/", views.InstructorDashboardView.as_view(), name="instructor-dashboard"),
    path("dashboard/student/", views.StudentDashboardView.as_view(), name="student-dashboard"),
    path("dashboard/partials/stats/", views.DashboardStatsPartialView.as_view(), name="dashboard-stats-partial"),
]
