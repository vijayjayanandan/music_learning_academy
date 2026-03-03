from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404


class TenantMixin(LoginRequiredMixin):
    def get_academy(self):
        academy = self.request.academy
        if not academy:
            raise Http404("No academy selected")
        return academy

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(qs.model, "academy"):
            return qs.filter(academy=self.get_academy())
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_academy"] = self.get_academy()
        ctx["user_role"] = self.request.user.get_role_in(self.get_academy())
        return ctx
