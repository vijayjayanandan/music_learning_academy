from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.AcademyCreateView.as_view(), name="academy-create"),
    path("<slug:slug>/", views.AcademyDetailView.as_view(), name="academy-detail"),
    path("<slug:slug>/settings/", views.AcademySettingsView.as_view(), name="academy-settings"),
    path("<slug:slug>/members/", views.MemberListView.as_view(), name="academy-members"),
    path("<slug:slug>/members/invite/", views.InviteMemberView.as_view(), name="academy-invite"),
    path("<slug:slug>/members/<int:pk>/remove/", views.RemoveMemberView.as_view(), name="academy-remove-member"),
    path("<slug:slug>/announcements/", views.AnnouncementListView.as_view(), name="academy-announcements"),
]
