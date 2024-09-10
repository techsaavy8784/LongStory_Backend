from rest_framework import serializers

from orders.models import (
    OrderDetail,
    OrderItem
)

from products.models import (
    Product
)

from users.models import (
    User,
    Address,
    Payment
)

from products.serializers import (
    ProductSerializer,
    ProductOrderItemSerializer
)

from users.serializers import (
    UserMainInfoSerializer,
    AddressSerializer,
    PaymentSerializer
)


        
class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductOrderItemSerializer()
    class Meta:
        model = OrderItem
        fields = ["id", "order_detail_id", "product", "quantity", "shipping_rate", "shipping_method", "created_at", "modified_at"]
        
class OrderDetailSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True)
    billing_address = AddressSerializer()
    shipping_address = AddressSerializer()
    payment = PaymentSerializer()
    class Meta:
        model = OrderDetail
        fields = ["id", "user_id", "order_items", "shipping_address", "billing_address", "payment",  "stripe_payment_intent_id", "stripe_refund_id" , "order_status", "created_at", "amount_shipping", "amount_paid", "shipping_service_code", "shipping_service_name", "modified_at", "arrive_at"]