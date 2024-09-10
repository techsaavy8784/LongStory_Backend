from django.db import models
from users.models import User
from decimal import Decimal

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)    
    description = models.TextField(blank=True, null=True)    
    created_at = models.DateTimeField(auto_now=True)
    modified_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.name}"

    class Meta:
        verbose_name = "Category Model"
        
class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.RESTRICT, blank=True, null=True)
    name = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)    
    source_url = models.TextField(blank=True, null=True)    
    currency = models.CharField(max_length=500, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now=True)
    modified_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    
    def __str__(self) -> str:
        return f"{self.name}"

    class Meta:
        ordering = ['-created_at',]
        verbose_name = "Product Model"
        
class Variant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    index = models.IntegerField()
    created_at = models.DateTimeField(auto_now=True)
    modified_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.product}-{self.index}"

    class Meta:
        verbose_name = "Variant Model"
        
class Metadata(models.Model):
    variant = models.ForeignKey(Variant, related_name='metadata', on_delete=models.CASCADE)
    field = models.CharField(max_length=255, blank=True, null=True)
    value = models.CharField(max_length=500)
    
    index = models.IntegerField()
    
    created_at = models.DateTimeField(auto_now=True)
    modified_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.variant} - {self.field} - {self.value} - {self.index}"

    class Meta:
        verbose_name = "Metadata Model"

        
class Media(models.Model):
    variant = models.ForeignKey(Variant, related_name='media', on_delete=models.CASCADE)

    media_type = models.CharField(max_length=500)
    index = models.IntegerField()
    url = models.CharField(max_length=500)

    created_at = models.DateTimeField(auto_now=True)
    modified_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.variant} - {self.media_type} - {self.index}"

    class Meta:
        verbose_name = "Media Model"
        
        
class Inventory(models.Model): 
    variant = models.OneToOneField(Variant, related_name='inventory', on_delete=models.CASCADE, primary_key=True,)
    quantity = models.IntegerField(default=0)
    currency = models.CharField(max_length=50, blank=True, null=True)
    price = models.BigIntegerField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now=True)
    modified_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.variant} - {self.quantity} - {self.price} - product variant inventory"

    class Meta:
        verbose_name = "Inventory Model"
        
class Like(models.Model):    
    user = models.ForeignKey(User, related_name='likes', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='likes', on_delete=models.CASCADE)
    
    created_at = models.DateTimeField(auto_now=True)
    modified_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.user} - {self.product} - like"

    class Meta:
        ordering = ['-created_at',]
        verbose_name = "Like Model"
        
class Shipping(models.Model):    
    variant = models.OneToOneField(Variant, related_name='shipping', on_delete=models.CASCADE, primary_key=True,)
    
    dimension_l = models.IntegerField(blank=True, null=True)
    dimension_w = models.IntegerField(blank=True, null=True)
    dimension_h = models.IntegerField(blank=True, null=True)
    weight = models.CharField(max_length=500, blank=True, null=True)
    unit_d = models.CharField(max_length=255, blank=True, null=True)
    unit_w = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now=True)
    modified_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.variant.index} - shipping"

    class Meta:
        ordering = ['-created_at',]
        verbose_name = "Shipping Model"

