from django.contrib import admin

# Register your models here.
from orders.models import (
    OrderDetail,
    OrderItem
)

class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order_detail", "product", "quantity", "created_at", "modified_at")
    
class OrderDetailAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "shipping_address_id", "billing_address_id", "payment_id", "stripe_payment_intent_id", "amount_paid", "order_status", "created_at", "modified_at")
    
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(OrderDetail, OrderDetailAdmin)