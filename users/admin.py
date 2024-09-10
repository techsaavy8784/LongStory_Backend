from users.models import (
        User, 
        Address,
        Follow,
        Payment,
        Sponsor,
        Inquiry
    )
from django.contrib import admin


# Register your models here.
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "username",  "is_vip", "is_deleted", "is_staff", "avatar_url", "is_active", "created_at", "modified_at", "approved_at", "auth_status", "auth_token", "stripe_customer_id", "stripe_subscription_id")
class AddressAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "address", "city","zip", "name", "state",  "country", "phone")
    
class FollowAdmin(admin.ModelAdmin):
    list_display = ("id", "followee", "follower")

class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "stripe_payment_method_id", "is_default", "created_at", "modified_at", "brand", "bank_name", "last4", "name", "email", "country", "type")

class SponsorAdmin(admin.ModelAdmin):
    list_display = ("sponsored_user", "sponsor_user", "subscription_payment", "order_payment")

class InquiryAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'persona_inquiry_id', 'status', 'created_at', 'modified_at')

admin.site.register(User, UserAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Sponsor, SponsorAdmin)
admin.site.register(Inquiry, InquiryAdmin)