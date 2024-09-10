from django.db import models
from users.models import (
    User,
    Payment,
    Address
)
from products.models import (
    Product
)

class OrderDetail(models.Model):
    user = models.ForeignKey(User, related_name="orders", on_delete=models.CASCADE,)
    shipping_address = models.ForeignKey(Address, related_name="order_shipping_addresses", on_delete=models.RESTRICT, blank=True, null=True)
    billing_address = models.ForeignKey(Address,related_name="order_billing_addresses", on_delete=models.RESTRICT, blank=True, null=True)
    payment = models.ForeignKey(Payment, related_name="orders", on_delete=models.RESTRICT, blank=True, null=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_refund_id = models.CharField(max_length=255, blank=True, null=True)
    amount_paid = models.IntegerField(default=0)
    amount_shipping = models.IntegerField(default=0)
    shipping_service_name = models.CharField(blank=True, null=True)
    shipping_service_code = models.CharField(blank=True, null=True)
    amount_saved = models.IntegerField(default=0)
    
    order_status = models.CharField(max_length=255, default="pending")
    created_at = models.DateTimeField(auto_now=True)
    arrive_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    modified_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    def __str__(self) -> str:
        return f"{self.user} - order: {self.pk}"

    class Meta:
        ordering = ['-created_at',]
        verbose_name = "OrderDetail Model"
    
class OrderItem(models.Model):
    order_detail = models.ForeignKey(OrderDetail, related_name="order_items", on_delete=models.CASCADE,)
    product = models.ForeignKey(Product, on_delete=models.CASCADE,)
    quantity = models.IntegerField(default=1)
    shipping_rate = models.IntegerField(default=0)
    shipping_service_name = models.CharField(blank=True, null=True)
    shipping_service_code = models.CharField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now=True)
    modified_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)    

    def __str__(self) -> str:
        return f"{self.order_detail} - {self.product}"

    class Meta:
        ordering = ['-created_at',]
        verbose_name = "OrderItem Model"