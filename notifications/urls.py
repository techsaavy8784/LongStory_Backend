from django.urls import path, include
from notifications import views


# define category action
urlpatterns = [
    path('notifications/', views.NotificationListCreate.as_view(), name='notification-list-create'),
    path('notifications/<int:pk>', views.NotificationRetrieveUpdateDestory.as_view(), name='notification-retrieve-update-destroy'),
]

urlpatterns += [
    path('admin/', include('notifications.manager.urls'))
]