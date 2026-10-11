from django.urls import path

from .views import CronOverdueView, HealthView

urlpatterns = [path("health", HealthView.as_view()), path("cron/overdue", CronOverdueView.as_view())]
