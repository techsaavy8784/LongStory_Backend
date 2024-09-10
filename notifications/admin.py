from django.contrib import admin

# Register your models here.
from notifications.models import (
    Notification
)

class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "read", "notification_type", "inactive_user_id", "order_detail_id", "created_at", "modified_at")

admin.site.register(Notification, NotificationAdmin)