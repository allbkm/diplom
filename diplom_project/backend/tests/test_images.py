from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import Product, Shop, Category, ProductImage
from unittest.mock import patch

User = get_user_model()


class ImageUploadTest(TestCase):
    """Тесты для загрузки изображений"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client.force_authenticate(user=self.user)

        # Тестовое изображение
        self.test_image = SimpleUploadedFile(
            'test_image.jpg',
            b'file_content',
            content_type='image/jpeg'
        )

        # Создаем тестовый товар
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

        self.avatar_url = reverse('user-avatar')
        self.upload_image_url = reverse('upload-product-image')
        self.product_images_url = reverse('product-images', kwargs={'product_id': 1})

    @patch('backend.tasks.process_user_avatar.delay')
    def test_upload_avatar_success(self, mock_task):
        """Тест успешной загрузки аватара"""
        data = {'avatar': self.test_image}
        response = self.client.post(self.avatar_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        mock_task.assert_called_once_with(self.user.id)

    def test_upload_avatar_no_file(self):
        """Тест загрузки аватара без файла"""
        response = self.client.post(self.avatar_url, {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])

    @patch('backend.tasks.process_product_image.delay')
    def test_upload_product_image_success(self, mock_task):
        """Тест успешной загрузки изображения товара"""
        data = {
            'product_id': 1,
            'image': self.test_image
        }
        response = self.client.post(self.upload_image_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['status'])
        mock_task.assert_called_once()

    def test_upload_product_image_invalid_product(self):
        """Тест загрузки изображения для несуществующего товара"""
        data = {
            'product_id': 9999,
            'image': self.test_image
        }
        response = self.client.post(self.upload_image_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['status'])

    def test_get_product_images(self):
        """Тест получения изображений товара"""
        # Создаем изображение
        ProductImage.objects.create(
            product=self.product,
            image=self.test_image
        )

        response = self.client.get(self.product_images_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertEqual(len(response.data['data']), 1)
