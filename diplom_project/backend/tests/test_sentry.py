from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from unittest.mock import patch


class SentryTest(TestCase):
    """Тесты для проверки интеграции Sentry"""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('sentry-test')

    @patch('sentry_sdk.capture_exception')
    def test_sentry_error_captured(self, mock_capture):
        """
        Тест: проверка, что ошибка отправляется в Sentry
        """
        response = self.client.get(self.url)

        # Проверяем, что ошибка была отправлена в Sentry
        mock_capture.assert_called_once()

        # Проверяем, что API вернул ошибку 500
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['status'])
        self.assertIn('Проверьте Sentry', response.data['error'])

    def test_sentry_error_response(self):
        """
        Тест: проверка структуры ответа при ошибке
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('status', response.data)
        self.assertIn('error', response.data)
        self.assertFalse(response.data['status'])
