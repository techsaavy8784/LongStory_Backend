from django.urls import path, include
from orders import views


# define category action
urlpatterns = [
    path('orders/orderItems', views.OrderItemListCreate.as_view(), name='orderItem-list-create'),
    path('orders/orderItems/<int:pk>', views.OrderItemRetrieveUpdateDestroy.as_view(), name='orderItem-retrieve-update-destroy'),
]

urlpatterns += [
    path('orders/orderDetails', views.OrderDetailListCreate.as_view(), name='orderDetail-list'),
    path('orders/orderDetails/<int:pk>', views.OrderDetailRetrieveUpdateDestroy.as_view(), name='orderDetail-list'),    
]

urlpatterns += [
    path('orders/easyship/get-rates', views.EasyShipRate.as_view(), name='get-rates'),
]

urlpatterns += [
    path('admin/', include('orders.manager.urls'))
]