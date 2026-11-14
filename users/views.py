import logging

from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from rest_framework import generics, permissions, views, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.utils.encoding import smart_str, force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .models import User
from .serializers import RegisterSerializer, UserProfileSerializer, UserSerializer, RequestRecoveryEmailSerializer,ResetPasswordSerializer

logger = logging.getLogger(__name__)


def get_user_from_uidb64(uidb64):
    try:
        uid = urlsafe_base64_decode(smart_str(uidb64)).decode()
    except (TypeError, ValueError, OverflowError, UnicodeDecodeError):
        return None
    return User.objects.filter(pk=uid).first()


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response(
            data={
                'user': UserSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return User.objects.prefetch_related('user_sessions').get(
            pk=self.request.user.pk
        )

class RequestRecoveryEmailAPIView(generics.GenericAPIView):
    serializer_class = RequestRecoveryEmailSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = User.objects.filter(email__iexact=email).first()
        if user:
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = PasswordResetTokenGenerator().make_token(user)
            reset_url = (
                f"{settings.FRONTEND_URL.rstrip('/')}/reset-password/{uidb64}/{token}"
            )
            message = (
                f"Hi {user.username or user.email},\n\n"
                "We received a request to reset your Noodli password. "
                "Use the link below to choose a new password:\n\n"
                f"{reset_url}\n\n"
                "If you didn't request this, you can safely ignore this email.\n\n"
                "— Noodli"
            )

            try:
                send_mail(
                    "Reset your Noodli password",
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                )
            except Exception:
                logger.exception(
                    "Failed to send password reset email for user %s", user.pk
                )

        return Response(
            data={
                "message": (
                    "If a user with this email address exists, "
                    "an email would be sent to it"
                )
            },
            status=status.HTTP_200_OK,
        )


class ConfirmResetLinkAPIView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request, uidb64, token):
        user = get_user_from_uidb64(uidb64)
        if not user:
            return Response(
                data={"message": "Invalid/expired reset link"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not PasswordResetTokenGenerator().check_token(user, token):
            return Response(
                data={"message": "Invalid password reset token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(data={"message": "valid link"}, status=status.HTTP_200_OK)


class ResetPasswordAPIView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = get_user_from_uidb64(data["uidb64"])
        if not user:
            return Response(
                data={"message": "Invalid/expired reset link"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not PasswordResetTokenGenerator().check_token(user, data["token"]):
            return Response(
                data={"message": "Reset link is used or invalid"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(data["new_password"])
        user.save()
        return Response(
            data={"message": "Password successfully changed"},
            status=status.HTTP_200_OK,
        )
