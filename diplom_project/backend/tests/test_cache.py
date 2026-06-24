from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.core.cache import cache
from ..models import Product, Shop, Category
import time

User = get_user_model()


class CacheTest(TestCase):
    """Тесты для кэширования"""

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.url = reverse('products')

        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
            is_staff=True
        )

        # Создаем тестовые данные
        self.shop = Shop.objects.create(name='Test Shop')
        self.category = Category.objects.create(id=1, name='Test Category')

        for i in range(10):
            Product.objects.create(
                id=i + 1,
                name=f'Test Product {i}',
                price=1000 + i * 100,
                quantity=10,
                shop=self.shop,
                category=self.category
            )

    def test_cache_works(self):
        """
        Тест: проверка работы кэширования
        """
        # Первый запрос - должен быть MISS
        response1 = self.client.get(self.url)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response1['X-Cache-Status'], 'MISS')

        # Второй запрос - должен быть HIT
        response2 = self.client.get(self.url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2['X-Cache-Status'], 'HIT')

    def test_cache_clearing(self):
        """
        Тест: очистка кэша
        """
        # Делаем запрос для создания кэша
        self.client.get(self.url)

        # Очищаем кэш
        self.client.force_authenticate(user=self.user)
        clear_url = reverse('clear-cache')
        response = self.client.post(clear_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])

        # Проверяем, что кэш очищен
        self.assertIsNone(cache.get('products_'))

    def test_cache_stats(self):
        """
        Тест: получение статистики кэша
        """
        self.client.force_authenticate(user=self.user)
        stats_url = reverse('cache-stats')
        response = self.client.get(stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertIn('cache_stats', response.data)

    def test_cache_unauthorized_clear(self):
        """
        Тест: попытка очистки кэша неавторизованным пользователем
        """
        clear_url = reverse('clear-cache')
        response = self.client.post(clear_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cache_clear_non_staff(self):
        """
        Тест: попытка очистки кэша обычным пользователем
        """
        # Создаем обычного пользователя
        user = User.objects.create_user(
            email='user@example.com',
            password='userpass123',
            first_name='User',
            last_name='User'
        )
        self.client.force_authenticate(user=user)

        clear_url = reverse('clear-cache')
        response = self.client.post(clear_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cache_timeout(self):
        """
        Тест: проверка времени жизни кэша
        """
        # Делаем запрос
        self.client.get(self.url)

        # Проверяем, что кэш существует
        cache_key = f'products_{self.client.get(self.url).query_params.urlencode()}'
        self.assertIsNotNone(cache.get(cache_key))

        # Очищаем кэш принудительно (имитация истечения времени)
        cache.delete(cache_key)
        self.assertIsNone(cache.get(cache_key))

    def test_performance_improvement(self):
        """
        Тест: проверка улучшения производительности
        """
        # Первый запрос (без кэша)
        start_time = time.time()
        response1 = self.client.get(self.url)
        time1 = time.time() - start_time

        # Второй запрос (с кэшем)
        start_time = time.time()
        response2 = self.client.get(self.url)
        time2 = time.time() - start_time

        # Второй запрос должен быть быстрее
        self.assertLess(time2, time1)

        # Проверяем наличие заголовков
        self.assertIn('X-Query-Time', response1)
        self.assertIn('X-Query-Time', response2)
