from django.urls import path
from users.manager import views

urlpatterns = [
    path("users/signin/", views.UserSigninView.as_view(), name="user-signin"),
    path("users/signup/", views.UserSignupView.as_view(), name="user-signup"),    
    path("users/send-invitation/", views.UserSendInvitation.as_view(), name="users-send-invitation"),    
    path("users/", views.UserList.as_view(), name="user-list"),
    path("users/<int:pk>/", views.UserRetrieveUpdateDestroy.as_view(), name="user-retrieve-update-destroy"),
]
