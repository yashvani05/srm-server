from django.contrib import admin

from .models import ServiceRequest, SystemState


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "priority", "status", "overdue", "created_by", "created_at")
    list_filter = ("status", "priority", "category", "overdue")
    search_fields = ("title", "description")


admin.site.register(SystemState)
