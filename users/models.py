# Create your models here.

from django.contrib.auth.models import (
    AbstractUser,
    BaseUserManager,
)
from django.db import models
from django.utils import timezone
from decimal import Decimal

class UserManager(BaseUserManager):
    
    def create_user(self, email, password=None, **extra_fields):
        
        if not email:
            raise ValueError("The Email field must be set")
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)
    
class User(AbstractUser):     
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    avatar_url = models.CharField(max_length=255, blank=True, null=True)
    last_signin_ip = models.CharField(max_length=255, blank=True, null=True)
    first_signin_ip = models.CharField(max_length=255, blank=True, null=True)
    signup_ip = models.CharField(max_length=255, blank=True, null=True)
    last_signin_device = models.CharField(max_length=255, blank=True, null=True)
    signup_device = models.CharField(max_length=255, blank=True, null=True)
    
    order_count = models.IntegerField(default=0)
    otp = models.CharField(max_length=255, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    
    
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    auth_status = models.IntegerField(default=0)
    auth_token = models.IntegerField(blank=True, null=True)
    
    is_online = models.BooleanField(default=True)
    is_vip = models.BooleanField(default=False)
    is_private = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    birthday = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now=True)
    modified_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    first_signin_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    last_signin_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    signup_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()    

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
    def __str__(self):
        return self.email
    class Meta:
        ordering = ['-created_at',]
        verbose_name = "User Model"
from phonenumber_field.modelfields import PhoneNumberField
class Address(models.Model):
    user = models.ForeignKey(User, related_name="addresses", on_delete=models.CASCADE,)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    zip = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    phone = PhoneNumberField()
    is_default = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now=True)
    modified_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)    

    def __str__(self) -> str:
        return f"{self.user} - {self.address}"

    class Meta:
        ordering = ['-created_at',]
        verbose_name = "User Address Model"
        
class Follow(models.Model):
    followee = models.ForeignKey(User, related_name="followers", on_delete=models.CASCADE)
    follower = models.ForeignKey(User, related_name="followees", on_delete=models.CASCADE)
   
    is_active = models.BooleanField(default=True)
    is_accepted = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now=True)
    modified_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)    

    def __str__(self) -> str:
        return f"followee:{self.followee} - follower:{self.follower}"

    class Meta:
        ordering = ['-created_at',]
        verbose_name = "User Follow Model"
        
class Payment(models.Model):
    user = models.ForeignKey(User, related_name="payments", on_delete=models.CASCADE)
    stripe_payment_method_id = models.CharField(max_length=255, blank=True, null=True)
    brand = models.CharField(max_length=255, blank=True, null=True)
    last4 = models.CharField(max_length=255, blank=True, null=True)
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    type = models.CharField(max_length=255, blank=True, null=True)
    is_default = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now=True)
    modified_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)   

    def __str__(self) -> str:
        return f"{self.user} - {self.type} -{self.last4}"

    class Meta:
        ordering = ['-created_at',]
        verbose_name = "User Payment Model"

class Sponsor(models.Model):
    sponsored_user = models.OneToOneField(User, related_name='sponsor_user', on_delete=models.CASCADE, primary_key=True,)
    sponsor_user = models.ForeignKey(User, related_name="sponsored_users", on_delete=models.CASCADE)
    subscription_payment = models.ForeignKey(Payment, related_name='sponsor_subscription_payments', on_delete=models.RESTRICT, blank=True, null=True)
    order_payment = models.ForeignKey(Payment, related_name='sponsor_order_payments', on_delete=models.RESTRICT, blank=True, null=True)

    is_active = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now=True)
    modified_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)    

    def __str__(self) -> str:
        return f"sponsored:{self.sponsored_user.username} - sponsor:{self.sponsor_user.username}"

    class Meta:
        ordering = ['-created_at',]
        verbose_name = "Sponsor Model"
        
class Inquiry(models.Model):
    user = models.OneToOneField(User, related_name='inquiry', on_delete=models.CASCADE, primary_key=True,)
    persona_inquiry_id = models.CharField(max_length=255)
    status = models.CharField(default="created")
    
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now=True)
    modified_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)    
    