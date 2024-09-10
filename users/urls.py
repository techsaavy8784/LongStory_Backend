from django.urls import path, include
from users import views

# admin users management
urlpatterns = [
    path('admin/', include('users.manager.urls')),    
]

# consumer users
urlpatterns += [
    path("users/signin/", views.UserSigninView.as_view(), name="user-signin"),
    path("users/signup/", views.UserSignupView.as_view(), name="user-signup"),   
    path("users/me/", views.UserMeView.as_view(), name="user-me"),    
    path("users/get-auth-status/", views.UserAuthStatusView.as_view(), name="user-auth-status"),    
    path('users/account/update-user/', views.UserUpdateView.as_view(), name="forgotPassword"),
    path('users/<int:pk>', views.UserRetrieveUpdateDestroy.as_view(), name="user-retrieve-update-destroy"),
    path("users/resend-activation-mail/", views.UserRecendActivationMail.as_view(), name="resend-activation-mail"),    
    path("users/resend-magic-link/", views.UserRecendMagicLink.as_view(), name="resend-activation-mail"),    
    
    # path('users/signin/<uidb64>/<token>/', views.UserGetToken.as_view(), name="getToken"),
    path('users/account/activate/<uidb64>/<token>/', views.UserAccountActivateView.as_view(), name="activate"),
    
    
    path('users/account/resetPassword/', views.UserResetPasswordView.as_view(), name="resetPassword"),
    
    
    path('users/account/forgotPassword/', views.UserForgotPasswordView.as_view(), name="forgotPassword"),
    path('users/account/checkOTP/', views.UserCheckOTP.as_view(), name="checkOTP"),
    path('users/account/changePassword/', views.UserChangePassword.as_view(), name="change-password"),
]

urlpatterns += [
    path("users/address/", views.AddressListCreate.as_view(), name="address-list-create"),
    path("users/address/<int:pk>", views.AddressRetrieveUpdateDestroy.as_view(), name="address-retrieve-update-destroy"),   
]

urlpatterns += [
    path("users/payment/", views.PaymentListCreate.as_view(), name="payment-list-create"),
    path("users/payment/<int:pk>", views.PaymentRetrieveUpdateDestroy.as_view(), name="payment-retrieve-update-destroy"),   
]

urlpatterns += [
    path("users/like/products", views.LikeList.as_view(), name="like-list"),
    path("users/like/products/<int:pk>", views.LikeRetrieveCreateDestroy.as_view(), name="payment-retrieve-create-destroy"),   
]

urlpatterns += [
    path("users/followers/", views.UserFollowerListView.as_view(), name="followers-list"),
    path("users/followers/<int:pk>", views.UserFollowerRetrieveUpdateView.as_view(), name="follower-retrieve-update"),   
    path("users/followees/", views.UserFolloweeListView.as_view(), name="followees-list"),
    path("users/followees/<int:pk>", views.UserFolloweeCreateRetrieveUpdateView.as_view(), name="followees-create-retrieve-update"),
    path("users/follows/", views.UserFollowRetrieveView.as_view(), name="followers-followees-number"),
]

urlpatterns += [
    path("users/", views.UserList.as_view(), name="user-list"),
    # path("users/like/products/<int:pk>", views.LikeRetrieveCreateDestroy.as_view(), name="payment-retrieve-create-destroy"),   
]

urlpatterns += [
    path("users/sponsors/", views.SponsorListCreate.as_view(), name="sponsors-list-create"),
    path("users/sponsors/<int:pk>", views.SponsorRetrieveUpdate.as_view(), name="sponsors-retrieve-update"),
]

urlpatterns += [
    path("users/inquiry/", views.InquiryView.as_view(), name="inquiry"),
]