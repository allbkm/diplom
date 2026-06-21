from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from django.core.exceptions import ValidationError

def validate_image_size(value):
    """Проверка размера изображения (не более 5MB)"""
    filesize = value.size
    if filesize > 5 * 1024 * 1024:
        raise ValidationError("Максимальный размер изображения 5MB")


class User(AbstractUser):
    """Модель пользователя"""
    email = models.EmailField(unique=True, verbose_name='Email')
    first_name = models.CharField(max_length=50, verbose_name='Имя')
    last_name = models.CharField(max_length=50, verbose_name='Фамилия')

    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/%d/',
        blank=True,
        null=True,
        validators=[validate_image_size],
        verbose_name='Аватар'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Shop(models.Model):
    """Модель магазина/поставщика"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'

    def __str__(self):
        return self.name


class Category(models.Model):
    """Модель категории"""
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100, verbose_name='Название')
    shops = models.ManyToManyField(Shop, related_name='categories', blank=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    """Модель товара"""
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200, verbose_name='Наименование')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    quantity = models.IntegerField(default=0, verbose_name='Количество')
    parameters = models.JSONField(default=dict, blank=True, verbose_name='Характеристики')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    main_image = models.ImageField(
        upload_to='products/%Y/%m/%d/',
        blank=True,
        null=True,
        validators=[validate_image_size],
        verbose_name='Главное изображение'
    )

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Contact(models.Model):
    """Модель контакта"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts')
    last_name = models.CharField(max_length=50, verbose_name='Фамилия')
    first_name = models.CharField(max_length=50, verbose_name='Имя')
    middle_name = models.CharField(max_length=50, blank=True, null=True, verbose_name='Отчество')
    email = models.EmailField(verbose_name='Email')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    city = models.CharField(max_length=100, verbose_name='Город')
    street = models.CharField(max_length=200, verbose_name='Улица')
    house = models.CharField(max_length=20, verbose_name='Дом')
    building = models.CharField(max_length=20, blank=True, null=True, verbose_name='Корпус')
    structure = models.CharField(max_length=20, blank=True, null=True, verbose_name='Строение')
    apartment = models.CharField(max_length=20, blank=True, null=True, verbose_name='Квартира')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты'
        unique_together = ['user', 'email']

    def __str__(self):
        return f'{self.first_name} {self.last_name} - {self.phone}'


class Cart(models.Model):
    """Модель корзины"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

    @property
    def total(self):
        """Общая сумма корзины"""
        return sum(item.total for item in self.items.all())

    def __str__(self):
        return f'Корзина #{self.id} - {self.user.email}'


class CartItem(models.Model):
    """Модель позиции в корзине"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')

    class Meta:
        verbose_name = 'Позиция корзины'
        verbose_name_plural = 'Позиции корзины'
        unique_together = ['cart', 'product']

    @property
    def total(self):
        """Сумма позиции"""
        return self.product.price * self.quantity

    @property
    def shop_name(self):
        return self.product.shop.name

    @property
    def product_name(self):
        return self.product.name

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'


class Order(models.Model):
    """Модель заказа"""
    STATUS_CHOICES = [
        ('pending', 'В обработке'),
        ('confirmed', 'Подтвержден'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='orders')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    @property
    def number(self):
        """Номер заказа"""
        return f'ORDER-{self.id:06d}'

    def __str__(self):
        return f'Заказ #{self.number}'

    class ProductImage(models.Model):
    """Дополнительные изображения товара"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Товар'
    )
    image = models.ImageField(
        upload_to='products/%Y/%m/%d/',
        validators=[validate_image_size],
        verbose_name='Изображение'
    )

    # ✅ АВТОМАТИЧЕСКИЕ МИНИАТЮРЫ (создаются через imagekit)
    thumbnail = ImageSpecField(
        source='image',
        processors=[ResizeToFill(200, 200)],
        format='JPEG',
        options={'quality': 80}
    )

    medium = ImageSpecField(
        source='image',
        processors=[ResizeToFill(600, 600)],
        format='JPEG',
        options={'quality': 85}
    )

    large = ImageSpecField(
        source='image',
        processors=[ResizeToFill(1200, 1200)],
        format='JPEG',
        options={'quality': 90}
    )

    is_main = models.BooleanField(default=False, verbose_name='Основное')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товаров'
        ordering = ['-is_main', 'created_at']

    def __str__(self):
        return f'Изображение для {self.product.name}'
