from django.db import models

# Create your models here.

from users.models import (
    User,
)

from orders.models import (
    OrderDetail
)

class Notification(models.Model):
    user = models.ForeignKey(User, related_name="user_notifications", on_delete=models.CASCADE,)
    read = models.BooleanField(default=False)
    notification_type = models.IntegerField(default=0)
    inactive_user = models.ForeignKey(User, related_name="inactive_user_notifications", on_delete=models.CASCADE, blank=True, null=True)
    order_detail = models.ForeignKey(OrderDetail, related_name="order_detail_notifications", on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now=True)
    modified_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)    

    def __str__(self) -> str:
        return f"notification to {self.user.username} - {self.notification_type}"
