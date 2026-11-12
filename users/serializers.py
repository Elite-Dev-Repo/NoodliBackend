from django.contrib.auth import get_user_model
from rest_framework import serializers

from tracked_sessions.serializers import SessionsSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'date_of_birth',
            'gender',
            'is_active',
            'is_staff',
            'date_joined',
        ]
        read_only_fields = [
            'id',
            'email',
            'is_active',
            'is_staff',
            'date_joined',
        ]


class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'password2',
            'date_of_birth',
            'gender',
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {'password': 'Passwords do not match.'}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        return User.objects.create_user(
            password=password, is_active=True, **validated_data
        )


class UserProfileSerializer(serializers.ModelSerializer):
    sessions = SessionsSerializer(source='user_sessions', many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'date_of_birth',
            'gender',
            'is_active',
            'is_staff',
            'date_joined',
            'sessions',
        ]
        read_only_fields = [
            'id',
            'email',
            'is_active',
            'is_staff',
            'date_joined',
            'sessions',
        ]



class RequestRecoveryEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=8)

class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=8)
    uidb64 = serializers.CharField(min_length=2)
    token = serializers.CharField(min_length=10)