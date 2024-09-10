from django.urls import path, include
from orders.manager import views

# define category action
urlpatterns = [
    # path('orders/orderItems', views.OrderItemListCreate.as_view(), name='orderItem-list-create'),
    # path('orders/orderItems/<int:pk>', views.OrderItemRetrieveUpdateDestroy.as_view(), name='orderItem-retrieve-update-destroy'),
]

urlpatterns += [
    path('orders/orderDetails', views.OrderDetailList.as_view(), name='orderDetail-list'),
    path('orders/orderDetails/<int:pk>', views.OrderDetailRetrieveUpdateDestroy.as_view(), name='orderDetail-list'),    
]

urlpatterns += [
    path('orders/orderDetails/<int:pk>/cancel', views.CancelOrderDetail.as_view(), name='orderDetail-cancel'),    
]