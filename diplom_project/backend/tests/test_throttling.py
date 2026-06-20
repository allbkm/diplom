from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.core.cache import cache
from ..models import Product, Shop, Category

User = get_user_model()


class ThrottlingTest(TestCase):
    """
    Тесты для проверки DRF throttling
    """

    def setUp(self):
        # Очищаем кэш перед каждым тестом
        cache.clear()

        self.client = APIClient()

        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        # Создаем тестовые данные для корзины
        self.shop = Shop.objects.create(name='Test Shop')
        self.category = Category.objects.create(id=1, name='Test Category')
        self.product = Product.objects.create(
            id=1,
            name='Test Product',
            price=1000,
            quantity=10,
            shop=self.shop,
            category=self.category
        )

        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.cart_url = reverse('cart')
        self.cart_add_url = reverse('cart-add')

    def test_register_throttling(self):
        """
        Тест: ограничение на регистрацию (3 попытки в час)
        """
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password': 'SecurePass123',
            'password_confirm': 'SecurePass123'
        }

        # Делаем 4 запроса на регистрацию
        for i in range(4):
            response = self.client.post(self.register_url, data, format='json')

            if i < 3:
                # Первые 3 запроса должны проходить
                # Могут быть ошибки валидации (дубликат email), но не throttling
                self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
            else:
                # 4-й запрос должен быть отклонен из-за throttling
                self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
                self.assertIn('Request was throttled', str(response.data))

    def test_login_throttling(self):
        """
        Тест: ограничение на логин (5 попыток в минуту)
        """
        # Создаем пользователя для логина
        User.objects.create_user(
            email='loginuser@example.com',
            password='SecurePass123',
            first_name='Login',
            last_name='User'
        )

        data = {
            'email': 'loginuser@example.com',
            'password': 'WrongPassword'
        }

        # Делаем 6 запросов на логин с неверным паролем
        for i in range(6):
            response = self.client.post(self.login_url, data, format='json')

            if i < 5:
                # Первые 5 запросов - ошибка аутентификации, но не throttling
                self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
            else:
                # 6-й запрос должен быть отклонен из-за throttling
                self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
                self.assertIn('Request was throttled', str(response.data))

    def test_cart_throttling_authenticated(self):
        """
        Тест: ограничение на операции с корзиной (20 запросов в минуту)
        """
        self.client.force_authenticate(user=self.user)

        # Делаем 21 запрос к корзине (GET)
        for i in range(21):
            response = self.client.get(self.cart_url)

            if i < 20:
                # Первые 20 запросов должны проходить
                self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
            else:
                # 21-й запрос должен быть отклонен
                self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
                self.assertIn('Request was throttled', str(response.data))

    def test_cart_add_throttling(self):
        """
        Тест: ограничение на добавление в корзину (20 запросов в минуту)
        """
        self.client.force_authenticate(user=self.user)

        data = {
            'product_id': 1,
            'quantity': 1
        }

        # Делаем 21 запрос на добавление в корзину
        for i in range(21):
            response = self.client.post(self.cart_add_url, data, format='json')

            if i < 20:
                # Первые 20 запросов должны проходить
                self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
            else:
                # 21-й запрос должен быть отклонен
                self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
                self.assertIn('Request was throttled', str(response.data))

    def test_products_no_throttling_for_anon(self):
        """
        Тест: просмотр товаров не имеет строгих ограничений
        """
        # Делаем 15 запросов к списку товаров (должны пройти все)
        for i in range(15):
            response = self.client.get(reverse('products'))
            self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_throttling_headers(self):
        """
        Тест: проверка наличия заголовков throttling в ответе
        """
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.cart_url)

        # Проверяем наличие заголовков throttling
        self.assertIn('X-Throttle-Wait-Seconds', response.headers)
        self.assertIn('X-Throttle-Remaining', response.headers)

    def test_throttling_reset_after_wait(self):
        """
        Тест: сброс throttling после ожидания
        """
        self.client.force_authenticate(user=self.user)

        # Превышаем лимит
        for i in range(21):
            response = self.client.get(self.cart_url)
            if i == 20:
                self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # Ждем 1 секунду (в реальном тесте этого достаточно)
        import time
        time.sleep(1)

        # После ожидания запрос должен пройти
        response = self.client.get(self.cart_url)
        self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_different_throttle_scopes(self):
        """
        Тест: разные scope throttling работают независимо
        """
        # Регистрация имеет свой лимит (3/час)
        # Логин имеет свой лимит (5/мин)
        # Они не должны влиять друг на друга

        register_data = {
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'password': 'SecurePass123',
            'password_confirm': 'SecurePass123'
        }

        # Делаем 3 запроса на регистрацию
        for i in range(3):
            response = self.client.post(self.register_url, register_data, format='json')
            # Может быть 400 из-за дубликата, но не 429
            self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # Проверяем, что логин все еще работает (не затронут регистрацией)
        login_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
