from django.urls import path


from .views import GoogleLogin, RegisterView, UserProfileView,RequestRecoveryEmailAPIView,ConfirmResetLinkAPIView, ResetPasswordAPIView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('google/', GoogleLogin.as_view(), name='google_login'),
    path('forgot_password/', RequestRecoveryEmailAPIView.as_view(), name="forgot_password"),
    path('forgot_password/<uidb64>/<token>/', ConfirmResetLinkAPIView.as_view()),
    path('change_password/', ResetPasswordAPIView.as_view())
]
