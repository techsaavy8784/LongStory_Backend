from django.urls import path, include
from products import views

urlpatterns = [
    path('admin/', include('products.manager.urls'))
]

# define category action
urlpatterns += [
    path('categories/', views.CategoryListCreate.as_view(), name='category-list'),
    path('categories/<int:pk>/', views.CategoryRetrieveUpdateDestroy.as_view(), name='category-detail'),
]

# #define product action
urlpatterns += [
    path('products/', views.ProductListCreate.as_view(), name='product-list-create'),
    path('products/<int:pk>/', views.ProductRetrieveUpdateDestroy.as_view(), name='product-retrieve-update-destroy'),
    
]
