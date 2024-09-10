from django.urls import path, include
from payments import views


urlpatterns = [
    path("payments/subscription/", views.SubscriptionCreate.as_view(), name="user-subscription-create"),
]

urlpatterns += [
    path("payments/webhook/", views.stripe_webhook, name="webhook"),
]

urlpatterns += [
    path('admin/', include('payments.manager.urls'))
]