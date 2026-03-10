from datetime import timedelta

from django import forms
from django.db.models import Sum
from django.shortcuts import redirect
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from apps.academies.mixins import TenantMixin
from .models import PracticeLog, PracticeGoal


class PracticeLogForm(forms.ModelForm):
    class Meta:
        model = PracticeLog
        fields = ["date", "duration_minutes", "instrument", "pieces_worked_on", "notes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs["class"] = "textarea textarea-bordered w-full"
                field.widget.attrs["rows"] = 2
            else:
                field.widget.attrs["class"] = "input input-bordered w-full"
        self.fields["date"].widget = forms.DateInput(
            attrs={"type": "date", "class": "input input-bordered w-full"}
        )


class PracticeLogListView(TenantMixin, ListView):
    model = PracticeLog
    template_name = "practice/log_list.html"
    context_object_name = "logs"
    paginate_by = 20

    def get_queryset(self):
        return PracticeLog.objects.filter(
            student=self.request.user,
            academy=self.get_academy(),
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = PracticeLogForm()
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        ctx["weekly_minutes"] = (
            PracticeLog.objects.filter(
                student=self.request.user,
                academy=self.get_academy(),
                date__gte=week_start,
            ).aggregate(total=Sum("duration_minutes"))["total"]
            or 0
        )

        # Calculate streak
        streak = 0
        check_date = today
        while PracticeLog.objects.filter(
            student=self.request.user, academy=self.get_academy(), date=check_date
        ).exists():
            streak += 1
            check_date -= timedelta(days=1)
        ctx["streak"] = streak

        goal = PracticeGoal.objects.filter(
            student=self.request.user, academy=self.get_academy(), is_active=True
        ).first()
        ctx["goal"] = goal
        return ctx


class PracticeLogCreateView(TenantMixin, View):
    def post(self, request):
        form = PracticeLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.student = request.user
            log.academy = self.get_academy()
            log.save()
        return redirect("practice-log-list")


class SetGoalView(TenantMixin, View):
    def post(self, request):
        target = int(request.POST.get("weekly_minutes_target", 120))
        PracticeGoal.objects.update_or_create(
            student=request.user,
            academy=self.get_academy(),
            is_active=True,
            defaults={"weekly_minutes_target": target},
        )
        return redirect("practice-log-list")
