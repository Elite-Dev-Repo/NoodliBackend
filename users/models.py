from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
# Create your models here.


class UserModelManager(BaseUserManager):
    """Manager for email-based authentication."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')

        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', False)

        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_active') is not True:
            raise ValueError('Superuser must have is_active=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if not password:
            raise ValueError('Superuser must have a password.')

        return self.create_user(email, password, **extra_fields)



class User(AbstractUser):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]
    username = models.CharField(
        max_length=150,
        unique=True,
        blank=True,
        null=True,
        validators=[UnicodeUsernameValidator()],
    )
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    objects = UserModelManager()

    def __str__(self):
        return f"User - {self.email}"
