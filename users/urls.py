from django.urls import path


from .views import GoogleLogin, RegisterView, UserProfileView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('google/', GoogleLogin.as_view(), name='google_login'),
]
