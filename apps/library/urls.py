from django.urls import path
from . import views

urlpatterns = [
    path("", views.LibraryListView.as_view(), name="library-list"),
    path("upload/", views.LibraryUploadView.as_view(), name="library-upload"),
    path("<int:pk>/", views.LibraryDetailView.as_view(), name="library-detail"),
    path("<int:pk>/delete/", views.LibraryDeleteView.as_view(), name="library-delete"),
]
