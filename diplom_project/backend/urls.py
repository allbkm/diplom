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

    path('api/auth/social/', SocialAuthView.as_view(), name='social-auth'),
]
