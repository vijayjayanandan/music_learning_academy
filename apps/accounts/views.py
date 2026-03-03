from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, TemplateView, UpdateView

from apps.academies.models import Academy
from .forms import RegisterForm, ProfileForm
from .models import User


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("login")


class RegisterView(CreateView):
    model = User
    form_class = RegisterForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["memberships"] = self.request.user.memberships.select_related("academy").all()
        return ctx


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = "accounts/profile_edit.html"
    success_url = reverse_lazy("profile")

    def get_object(self):
        return self.request.user


class SwitchAcademyView(LoginRequiredMixin, View):
    def post(self, request, slug):
        academy = get_object_or_404(Academy, slug=slug)
        if request.user.memberships.filter(academy=academy).exists():
            request.user.current_academy = academy
            request.user.save(update_fields=["current_academy"])
        return redirect("dashboard")
