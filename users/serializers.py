from rest_framework import serializers
from users.models import (
    User,
    Address,
    Follow,
    Payment,
    Sponsor,
    Inquiry
)

class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'username', 'first_name', 'last_name']
        extra_kwargs = {'password': {'write_only': True}}

class UserSigninSerializer(serializers.ModelSerializer):
    
    email = serializers.EmailField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}
        
class UserMainInfoSerializer(serializers.ModelSerializer):
    # email = serializers.EmailField()
    class Meta:
        model = User
        fields = ["id", "email", "username", "is_vip", "is_deleted", "is_private", "is_staff","is_superuser", "avatar_url", "is_active", "created_at", "modified_at", "first_name", "last_name", "birthday", "phone", "country", "auth_status"]
        
class UserLikeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['id', 'email', 'avatar_url', 'username']

# from products.serializers import(
#     LikeSerializer
# )
        
class AddressSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Address
        fields = ["id", "user_id", "name", "address", "city", "state", "zip",  "country", "phone", "is_default", "is_deleted", "created_at", "modified_at"]
        
class PaymentSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Payment
        fields = ["id", "user_id", "stripe_payment_method_id", "is_default", "is_deleted", "created_at", "modified_at", "brand", "bank_name", "last4", "name", "email", "country", "type"]

class InquirySerializer(serializers.ModelSerializer):

    class Meta:
        model = Inquiry
        fields = ['user_id', 'persona_inquiry_id', 'status', 'created_at', 'modified_at']

class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ["id", "followee_id", "follower_id", "is_active", "is_accepted", "is_deleted", "created_at", "modified_at"]

class FollowDetailSerializer(serializers.ModelSerializer):
    followee = UserMainInfoSerializer()
    follower = UserMainInfoSerializer()
    class Meta:
        model = Follow
        fields = ["id", "followee", "follower", "is_active", "is_accepted", "is_deleted", "created_at", "modified_at"]
        
class UserInfoSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True)
    followers = FollowDetailSerializer(many=True)
    followees = FollowDetailSerializer(many=True)
    # likes =LikeSerializer(many=True)
    inquiry = InquirySerializer()
    class Meta:
        model = User
        fields = ["id", "email", "username",  "is_vip", "is_deleted", "is_staff", "avatar_url", "addresses", "payments", "is_superuser", "is_online","signup_device", "last_signin_device", "total_spent", "order_count", "is_active", "created_at", "modified_at", "first_signin_ip", "last_signin_ip", "signup_ip", "first_signin_at", "last_signin_at", "signup_at", "followees", "followers", "first_name", "last_name", "birthday", "country", "phone", "is_private", "auth_status", "stripe_customer_id", "stripe_subscription_id", "inquiry" ]

class UserSponsorSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['id', 'email', 'avatar_url', 'username', "auth_status"]


class SponsorSerializer(serializers.ModelSerializer):
    
    sponsored_user = UserSponsorSerializer()
    sponsor_user = UserSponsorSerializer()
    subscription_payment = PaymentSerializer()
    order_payment = PaymentSerializer()

    class Meta:
        model = Sponsor
        fields = ['sponsored_user', 'sponsor_user', 'subscription_payment', 'order_payment']
        

        


