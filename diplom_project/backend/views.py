from rest_framework import status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import *
from .serializers import *
from .permissions import IsAuthenticated


class RegisterView(APIView):
    """Регистрация пользователя"""
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'status': True,
                'message': 'Регистрация успешна',
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': {
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            'status': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Вход пользователя"""
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            try:
                user = User.objects.get(email=email)
                if user.check_password(password):
                    refresh = RefreshToken.for_user(user)
                    return Response({
                        'status': True,
                        'message': 'Вход выполнен успешно',
                        'access_token': str(refresh.access_token),
                        'refresh_token': str(refresh),
                        'user': {
                            'id': user.id,
                            'email': user.email,
                            'first_name': user.first_name,
                            'last_name': user.last_name
                        }
                    })
                return Response({
                    'status': False,
                    'error': 'Неверный пароль'
                }, status=status.HTTP_401_UNAUTHORIZED)
            except User.DoesNotExist:
                return Response({
                    'status': False,
                    'error': 'Пользователь не найден'
                }, status=status.HTTP_404_NOT_FOUND)
        return Response({
            'status': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ProductListView(ListAPIView):
    """Список товаров с фильтрацией и поиском"""
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'shop', 'price']
    search_fields = ['name', 'description']  # ✅ Исправлено: только существующие поля
    ordering_fields = ['price', 'name', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Product.objects.select_related('category', 'shop').all()
        
        # Фильтр по цене
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': True,
            'count': queryset.count(),
            'results': serializer.data
        })


class ContactView(APIView):
    """Управление контактами"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Получение списка контактов"""
        contacts = Contact.objects.filter(user=request.user)
        serializer = ContactSerializer(contacts, many=True)
        return Response({
            'status': True,
            'contacts': serializer.data
        })
    
    def post(self, request):
        """Добавление контакта"""
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({
                'status': True,
                'message': 'Контакт успешно добавлен',
                'contact': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'status': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, pk):
        """Обновление контакта"""
        try:
            contact = Contact.objects.get(pk=pk, user=request.user)
        except Contact.DoesNotExist:
            return Response({
                'status': False,
                'error': 'Контакт не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ContactSerializer(contact, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': True,
                'message': 'Контакт обновлен',
                'contact': serializer.data
            })
        return Response({
            'status': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """Удаление контакта"""
        try:
            contact = Contact.objects.get(pk=pk, user=request.user)
            contact.delete()
            return Response({
                'status': True,
                'message': 'Контакт удален'
            }, status=status.HTTP_204_NO_CONTENT)
        except Contact.DoesNotExist:
            return Response({
                'status': False,
                'error': 'Контакт не найден'
            }, status=status.HTTP_404_NOT_FOUND)


class CartView(APIView):
    """Управление корзиной"""
    permission_classes = [IsAuthenticated]
    
    def get_cart(self, user):
        """Получение или создание активной корзины"""
        cart, _ = Cart.objects.get_or_create(user=user, is_active=True)
        return cart
    
    def get(self, request):
        """Просмотр корзины"""
        cart = self.get_cart(request.user)
        serializer = CartSerializer(cart)
        return Response({
            'status': True,
            'cart': serializer.data
        })
    
    def post(self, request):
        """Добавление товара в корзину"""
        serializer = AddToCartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data.get('quantity', 1)
        
        try:
            product = Product.objects.get(id=product_id)
            if product.quantity < quantity:
                return Response({
                    'status': False,
                    'error': f'Недостаточно товара на складе. Доступно: {product.quantity}'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Product.DoesNotExist:
            return Response({
                'status': False,
                'error': 'Товар не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        
        cart = self.get_cart(request.user)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        serializer = CartSerializer(cart)
        return Response({
            'status': True,
            'message': 'Товар добавлен в корзину',
            'cart': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def delete(self, request, item_id):
        """Удаление товара из корзины"""
        try:
            cart = Cart.objects.get(user=request.user, is_active=True)
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            cart_item.delete()
            
            serializer = CartSerializer(cart)
            return Response({
                'status': True,
                'message': 'Товар удален из корзины',
                'cart': serializer.data
            })
        except Cart.DoesNotExist:
            return Response({
                'status': False,
                'error': 'Корзина не найдена'
            }, status=status.HTTP_404_NOT_FOUND)
        except CartItem.DoesNotExist:
            return Response({
                'status': False,
                'error': 'Позиция не найдена в корзине'
            }, status=status.HTTP_404_NOT_FOUND)


class OrderConfirmView(APIView):
    """Подтверждение заказа"""
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        serializer = OrderConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cart_id = serializer.validated_data['cart_id']
        contact_id = serializer.validated_data['contact_id']
        
        try:
            cart = Cart.objects.get(id=cart_id, user=request.user, is_active=True)
            contact = Contact.objects.get(id=contact_id, user=request.user)
        except Cart.DoesNotExist:
            return Response({
                'status': False,
                'error': 'Корзина не найдена или уже подтверждена'
            }, status=status.HTTP_404_NOT_FOUND)
        except Contact.DoesNotExist:
            return Response({
                'status': False,
                'error': 'Контакт не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if not cart.items.exists():
            return Response({
                'status': False,
                'error': 'Корзина пуста'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверяем наличие товаров на складе
        for item in cart.items.all():
            if item.product.quantity < item.quantity:
                return Response({
                    'status': False,
                    'error': f'Недостаточно товара "{item.product.name}" на складе'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Создаем заказ
        order = Order.objects.create(
            user=request.user,
            cart=cart,
            contact=contact,
            total_amount=cart.total,
            status='confirmed'
        )
        
        # Уменьшаем количество товаров на складе
        for item in cart.items.all():
            product = item.product
            product.quantity -= item.quantity
            product.save()
        
        # Деактивируем корзину
        cart.is_active = False
        cart.save()
        
        # Создаем новую активную корзину для пользователя
        Cart.objects.create(user=request.user, is_active=True)
        
        return Response({
            'status': True,
            'message': 'Заказ успешно подтвержден',
            'order': {
                'id': order.id,
                'number': order.number,
                'created_at': order.created_at,
                'total_amount': order.total_amount,
                'status': order.status
            }
        }, status=status.HTTP_201_CREATED)


class OrderHistoryView(APIView):
    """История и статусы заказов"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, order_id=None):
        """Получение истории заказов или статуса конкретного заказа"""
        if order_id:
            try:
                order = Order.objects.get(id=order_id, user=request.user)
                serializer = OrderDetailSerializer(order)
                return Response({
                    'status': True,
                    'order': serializer.data
                })
            except Order.DoesNotExist:
                return Response({
                    'status': False,
                    'error': 'Заказ не найден'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            orders = Order.objects.filter(user=request.user)
            serializer = OrderSerializer(orders, many=True)
            return Response({
                'status': True,
                'orders': serializer.data
            })
