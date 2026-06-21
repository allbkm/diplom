from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from unittest.mock import patch, MagicMock

User = get_user_model()


class SocialAuthTest(TestCase):
    """
    Тесты для авторизации через социальные сети
    """

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('social-auth')

    @patch('social_core.backends.google.GoogleOAuth2.do_auth')
    def test_google_auth_success(self, mock_do_auth):
        """
        Тест успешной авторизации через Google
        """
        # Создаем тестового пользователя
        user = User.objects.create_user(
            email='google@example.com',
            first_name='Google',
            last_name='User',
            password='testpass123'
        )

        # Мокаем do_auth
        mock_do_auth.return_value = user

        data = {
            'provider': 'google-oauth2',
            'access_token': 'fake-google-token'
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertIn('access_token', response.data)
        self.assertEqual(response.data['user']['email'], 'google@example.com')

    @patch('social_core.backends.github.GithubOAuth2.do_auth')
    def test_github_auth_success(self, mock_do_auth):
        """
        Тест успешной авторизации через GitHub
        """
        user = User.objects.create_user(
            email='github@example.com',
            first_name='GitHub',
            last_name='User',
            password='testpass123'
        )

        mock_do_auth.return_value = user

        data = {
            'provider': 'github',
            'access_token': 'fake-github-token'
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertIn('access_token', response.data)
        self.assertEqual(response.data['user']['email'], 'github@example.com')

    def test_social_auth_missing_provider(self):
        """
        Тест: отсутствует provider
        """
        data = {
            'access_token': 'fake-token'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])

    def test_social_auth_missing_token(self):
        """
        Тест: отсутствует access_token
        """
        data = {
            'provider': 'google-oauth2'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])

    @patch('social_core.backends.google.GoogleOAuth2.do_auth')
    def test_social_auth_invalid_token(self, mock_do_auth):
        """
        Тест: неверный access_token
        """
        mock_do_auth.return_value = None

        data = {
            'provider': 'google-oauth2',
            'access_token': 'invalid-token'
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])

    def test_social_auth_throttling(self):
        """
        Тест: ограничение на количество запросов (5 в минуту)
        """
        data = {
            'provider': 'google-oauth2',
            'access_token': 'fake-token'
        }

        # Делаем 6 запросов
        for i in range(6):
            response = self.client.post(self.url, data, format='json')

            if i < 5:
                # Первые 5 запросов - ошибка аутентификации, но не throttling
                self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
            else:
                # 6-й запрос должен быть отклонен
                self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
