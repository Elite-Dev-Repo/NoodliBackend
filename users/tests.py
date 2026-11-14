from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class RegisterAPITests(APITestCase):
    url = '/api/register/'

    def payload(self, **overrides):
        data = {
            'username': 'new-user',
            'email': 'new-user@example.com',
            'password': 'strong-pass-123',
            'password2': 'strong-pass-123',
        }
        data.update(overrides)
        return data

    def test_register_creates_active_user_and_returns_tokens(self):
        response = self.client.post(self.url, self.payload(), format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['email'], 'new-user@example.com')

        user = User.objects.get(email='new-user@example.com')
        self.assertTrue(user.is_active)
        self.assertTrue(user.check_password('strong-pass-123'))

    def test_register_works_without_gender_or_date_of_birth(self):
        response = self.client.post(self.url, self.payload(), format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email='new-user@example.com')
        self.assertEqual(user.gender, '')
        self.assertIsNone(user.date_of_birth)

    def test_register_rejects_mismatched_passwords(self):
        response = self.client.post(
            self.url,
            self.payload(password2='different-pass-123'),
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_register_rejects_duplicate_email(self):
        User.objects.create_user(
            email='new-user@example.com',
            password='existing-pass-123',
            username='existing-user',
            is_active=True,
        )

        response = self.client.post(self.url, self.payload(), format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
