from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from ..models import Product, Shop, Category, Cart, CartItem, Contact, Order

User = get_user_model()


class RegisterViewTest(TestCase):
    """Тесты регистрации пользователя"""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('register')
        self.valid_data = {
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': 'ivan@example.com',
            'password': 'SecurePass123',
            'password_confirm': 'SecurePass123'
        }

    def test_register_success(self):
        """Тест успешной регистрации"""
        response = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['status'])
        self.assertEqual(response.data['user']['email'], 'ivan@example.com')
        self.assertTrue(User.objects.filter(email='ivan@example.com').exists())

    def test_register_password_mismatch(self):
        """Тест регистрации с несовпадающими паролями"""
        data = self.valid_data.copy()
        data['password_confirm'] = 'WrongPassword'
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])

    def test_register_duplicate_email(self):
        """Тест регистрации с уже существующим email"""
        User.objects.create_user(
            email='ivan@example.com',
            password='SecurePass123',
            first_name='Иван',
            last_name='Иванов'
        )
        response = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginViewTest(TestCase):
    """Тесты входа пользователя"""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('login')
        self.user = User.objects.create_user(
            email='ivan@example.com',
            password='SecurePass123',
            first_name='Иван',
            last_name='Иванов'
        )
        self.valid_data = {
            'email': 'ivan@example.com',
            'password': 'SecurePass123'
        }

    def test_login_success(self):
        """Тест успешного входа"""
        response = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertIn('access_token', response.data)

    def test_login_wrong_password(self):
        """Тест входа с неверным паролем"""
        data = self.valid_data.copy()
        data['password'] = 'WrongPassword'
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['status'])

    def test_login_nonexistent_user(self):
        """Тест входа с несуществующим пользователем"""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'password'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['status'])


class CartViewTest(TestCase):
    """Тесты корзины"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client.force_authenticate(user=self.user)

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
        self.cart_url = reverse('cart')
        self.cart_add_url = reverse('cart-add')

    def test_get_empty_cart(self):
        """Тест просмотра пустой корзины"""
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertEqual(len(response.data['cart']['items']), 0)

    def test_add_to_cart_success(self):
        """Тест добавления товара в корзину"""
        data = {'product_id': 1, 'quantity': 2}
        response = self.client.post(self.cart_add_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['status'])
        self.assertEqual(len(response.data['cart']['items']), 1)
        self.assertEqual(response.data['cart']['items'][0]['quantity'], 2)

    def test_add_to_cart_insufficient_quantity(self):
        """Тест добавления товара с недостаточным количеством"""
        self.product.quantity = 1
        self.product.save()

        data = {'product_id': 1, 'quantity': 5}
        response = self.client.post(self.cart_add_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])

    def test_remove_from_cart(self):
        """Тест удаления товара из корзины"""
        cart = Cart.objects.get(user=self.user, is_active=True)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)

        item_id = cart.items.first().id
        remove_url = reverse('cart-remove', kwargs={'item_id': item_id})

        response = self.client.delete(remove_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertEqual(len(response.data['cart']['items']), 0)


class OrderConfirmViewTest(TestCase):
    """Тесты подтверждения заказа"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client.force_authenticate(user=self.user)

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

        self.contact = Contact.objects.create(
            user=self.user,
            last_name='Иванов',
            first_name='Иван',
            email='ivan@example.com',
            phone='+79001234567',
            city='Москва',
            street='Тверская',
            house='15'
        )

        self.cart = Cart.objects.create(user=self.user, is_active=True)
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)

        self.url = reverse('order-confirm')

    def test_order_confirm_success(self):
        """Тест успешного подтверждения заказа"""
        data = {'cart_id': self.cart.id, 'contact_id': self.contact.id}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['status'])

        order = Order.objects.first()
        self.assertIsNotNone(order)
        self.assertEqual(order.total_amount, 2000)

    def test_order_confirm_empty_cart(self):
        """Тест подтверждения с пустой корзиной"""
        self.cart.items.all().delete()

        data = {'cart_id': self.cart.id, 'contact_id': self.contact.id}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])

    def test_order_confirm_insufficient_stock(self):
        """Тест подтверждения с недостаточным количеством товара"""
        self.product.quantity = 1
        self.product.save()

        data = {'cart_id': self.cart.id, 'contact_id': self.contact.id}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])


class ProductListViewTest(TestCase):
    """Тесты списка товаров"""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('products')

        self.shop = Shop.objects.create(name='Test Shop')
        self.category = Category.objects.create(id=1, name='Test Category')

        Product.objects.create(
            id=1,
            name='iPhone 13',
            description='Apple iPhone 13',
            price=80000,
            quantity=10,
            shop=self.shop,
            category=self.category
        )
        Product.objects.create(
            id=2,
            name='Samsung Galaxy S21',
            description='Samsung flagship',
            price=70000,
            quantity=5,
            shop=self.shop,
            category=self.category
        )

    def test_get_products_list(self):
        """Тест получения списка товаров"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertEqual(response.data['count'], 2)

    def test_search_products(self):
        """Тест поиска товаров"""
        response = self.client.get(f'{self.url}?search=iPhone')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_filter_by_price(self):
        """Тест фильтрации по цене"""
        response = self.client.get(f'{self.url}?min_price=60000&max_price=90000')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
