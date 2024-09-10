from rest_framework import serializers
from products.models import (
    Category,
    Product,
    Variant,
    Metadata,
    Inventory,
    Media,
    Like,
    Shipping
)
from users.serializers import (
    UserLikeSerializer
)


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    class Meta:
        model = Category
        fields = ["id", "name", "description", "created_at", "modified_at", "is_active", "product_count"]
    def get_product_count(self, obj):
        # Calculate the count of related objects
        return obj.products.count()
        
class ProductSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Product
        fields = ["id", "category_id", "name", "description", "source_url", "is_active", "published_at", "price", "currency", "created_at", "is_published", "modified_at"]
        
class VariantSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Variant
        fields = ["id", "product_id", "index", "is_active", "created_at", "modified_at"]
        
class MetadataSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Metadata
        fields = ["id", "variant_id", "field", "value", "index", "is_active", "created_at", "modified_at"]
        
class MediaSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Media
        fields = ["id", "variant_id", "index", "url", "is_active", "created_at", "modified_at"]
        
class InventorySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Inventory
        fields = ["variant_id", "price", "currency", "quantity", "is_active"]
        
class LikeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Like
        fields = ["id", "user_id", "product_id", "created_at", "modified_at"]
        
class ShippingSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Shipping
        fields = ["variant_id", "dimension_l", "dimension_w", "dimension_h", "unit_d", "weight", "unit_w","created_at", "modified_at"]
        
class VariantDetailedInfoSerializer(serializers.ModelSerializer):
    metadata = MetadataSerializer(many=True)
    media = MediaSerializer(many=True)
    inventory = InventorySerializer()
    shipping = ShippingSerializer()
    
    
    class Meta:
        model = Variant
        fields = ["id", "product_id", "index", "is_active", "created_at", "modified_at", "metadata", "media", "inventory", "shipping"]
        
class ProductLikeSerializer(serializers.ModelSerializer):
    variants = VariantDetailedInfoSerializer(many=True)
    class Meta:
        model = Product
        fields = ["id",  "name", "description", "source_url", "variants","is_active", "published_at", "price", "currency", "created_at", "is_published", "modified_at"]

        
class LikeSerializer(serializers.ModelSerializer):
    user = UserLikeSerializer()
    product = ProductLikeSerializer()
    
    class Meta:
        model = Like
        fields = ["id", "user", "product"]
        

        
class ProductDetailedInfoSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    variants = VariantDetailedInfoSerializer(many=True)
    likes = LikeSerializer(many=True)
        
    class Meta:
        model = Product
        fields = ["id", "category", "name", "description", "likes","source_url",  "price", "currency", "is_active", "created_at", "modified_at", "is_published",  "published_at", "variants"]
        
class ProductOrderItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    variants = VariantDetailedInfoSerializer(many=True)
    
    class Meta:
        model = Product
        fields = ["id",  "name", "category", "variants", "description", "source_url", "variants","is_active", "published_at", "price", "currency", "created_at", "is_published", "modified_at"]
        

    



