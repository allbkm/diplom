from django.urls import path
from .views import *

urlpatterns = [
    # Аутентификация
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/login/', LoginView.as_view(), name='login'),

    # Товары
    path('api/products/', ProductListView.as_view(), name='products'),

    # Контакты
    path('api/contacts/', ContactView.as_view(), name='contacts'),
    path('api/contacts/<int:pk>/', ContactView.as_view(), name='contact-detail'),

    # Корзина
    path('api/cart/', CartView.as_view(), name='cart'),
    path('api/cart/add/', CartView.as_view(), name='cart-add'),
    path('api/cart/remove/<int:item_id>/', CartView.as_view(), name='cart-remove'),

    # Заказы
    path('api/orders/confirm/', OrderConfirmView.as_view(), name='order-confirm'),
    path('api/orders/', OrderHistoryView.as_view(), name='orders'),
    path('api/orders/<int:order_id>/', OrderHistoryView.as_view(), name='order-detail'),

    # Соцсети
    path('api/auth/social/', SocialAuthView.as_view(), name='social-auth'),

    path('api/user/avatar/', UploadAvatarView.as_view(), name='user-avatar'),

    # Картинки
    path('api/products/<int:product_id>/images/', ProductImageView.as_view(), name='product-images'),
    path('api/products/<int:product_id>/images/<int:image_id>/', ProductImageView.as_view(), name='product-image-detail'),
    path('api/products/images/upload/', UploadProductImageView.as_view(), name='upload-product-image'),

    # ТЕСТОВЫЙ URL ДЛЯ SENTRY
    path('api/sentry-test/', SentryTestView.as_view(), name='sentry-test'),

    # ДОБАВЛЯЕМ URL ДЛЯ КЭШИРОВАНИЯ
    path('api/cache/clear/', ClearCacheView.as_view(), name='clear-cache'),
    path('api/cache/stats/', ClearCacheView.as_view(), name='cache-stats'),
]

