from django.urls import path, include
from products.manager import views


# define category action
urlpatterns = [
    path('categories/', views.CategoryListCreate.as_view(), name='category-list'),
    path('categories/<int:pk>/', views.CategoryRetrieveUpdateDestroy.as_view(), name='category-detail'),
]

# #define product action
urlpatterns += [
    path('products/', views.ProductListCreate.as_view(), name='product-list-create'),
    path('products/<int:pk>/', views.ProductRetrieveUpdateDestroy.as_view(), name='product-retrieve-update-destroy'),
    
]
# #define product action
urlpatterns += [
    path('variants/', views.VariantListCreate.as_view(), name='variant-list-create'),
    path('variants/<int:pk>/', views.VariantRetrieveUpdateDestroy.as_view(), name='variant-retrieve-update-destroy'),
    path('variants/<int:pk>/metadata', views.MetadataListUpdateDestroy.as_view(), name='metadata-create-update-destroy'),
    path('variants/<int:pk>/media', views.MediaCreateUpdateDestroy.as_view(), name='media-create-update-destroy'),
    path('variants/<int:pk>/inventory', views.InventoryCreateUpdateDestroy.as_view(), name='inventory-create-update-destroy'),
    path('variants/<int:pk>/shipping', views.ShippingCreateUpdateDestroy.as_view(), name='shipping-create'),    
]

# define product action
urlpatterns += [
    path('fileupload/', views.FileUploadView.as_view(), name='file-upload'),    
]

urlpatterns += [
    path('products/bulk-update', views.ProductBulkUpdate.as_view(), name='file-upload'),    
]

