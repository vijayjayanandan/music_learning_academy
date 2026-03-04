from django.urls import path
from . import views

urlpatterns = [
    path("", views.PracticeLogListView.as_view(), name="practice-log-list"),
    path("add/", views.PracticeLogCreateView.as_view(), name="practice-log-create"),
    path("goal/", views.SetGoalView.as_view(), name="practice-set-goal"),
]
