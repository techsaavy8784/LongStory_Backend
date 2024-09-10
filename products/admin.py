from products.models import (
        Category, 
        Product,
        Variant,
        Metadata,
        Media,
        Inventory,
        Like,
        Shipping
    )
from django.contrib import admin


# Register your models here.
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description", "created_at", "modified_at", "is_active")
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "category", "source_url", "currency", "price", "published_at", "name", "description", "created_at", "modified_at", "is_active")
class VariantAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "index", "created_at", "modified_at", "is_active")
class MetadataAdmin(admin.ModelAdmin):
    list_display = ("id", "variant", "field", "value", "index", "created_at", "modified_at", "is_active")
class MediaAdmin(admin.ModelAdmin):
    list_display = ("id", "variant", "media_type", "index", "url", "created_at", "modified_at", "is_active")
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("variant", "currency", "quantity", "price", "created_at", "modified_at", "is_active")
class LikeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product")
    
class ShippingAdmin(admin.ModelAdmin):
    list_display = ("variant_id", "dimension_l", "dimension_w", "dimension_h", "unit_d", "weight", "unit_w",  "created_at", "modified_at")

admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Variant, VariantAdmin)
admin.site.register(Metadata, MetadataAdmin)
admin.site.register(Inventory, InventoryAdmin)
admin.site.register(Media, MediaAdmin)
admin.site.register(Like, LikeAdmin)
admin.site.register(Shipping, ShippingAdmin)