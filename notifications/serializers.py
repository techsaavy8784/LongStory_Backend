from rest_framework import serializers

from notifications.models import (
    Notification,
)

from orders.models import (
    OrderDetail,
)

from products.models import (
    Product
)

from users.models import (
    User,
)

from orders.serializers import (
    OrderDetailSerializer
)

from users.serializers import (
    UserMainInfoSerializer,
    AddressSerializer,
    PaymentSerializer,
    UserMainInfoSerializer
)

class NotificationSerializer(serializers.ModelSerializer):
    user = UserMainInfoSerializer()
    inactive_user = UserMainInfoSerializer()
    order_detail = OrderDetailSerializer()

    
    class Meta:
        model = Notification
        fields = ["id", "user", "read", "notification_type", "inactive_user", "order_detail", "created_at", "modified_at"]

