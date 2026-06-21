from rest_framework import status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from .models import *
from .serializers import *
from .permissions import IsAuthenticated
from .tasks import send_order_confirmation_email
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle, ScopedRateThrottle
from social_django.utils import psa
from django.contrib.auth import login
from .serializers import SocialAuthSerializer
from .tasks import process_user_avatar, process_product_image, process_all_product_images
from .serializers import UploadImageSerializer, ProductImageSerializer, UserAvatarSerializer


class RegisterThrottle(ScopedRateThrottle):
    scope = 'register'

class LoginThrottle(ScopedRateThrottle):
    scope = 'login'

class CartThrottle(ScopedRateThrottle):
    scope = 'cart'


class RegisterView(APIView):
    """
    Регистрация пользователя
    """

    @extend_schema(
        request=UserRegistrationSerializer,
        responses={201: UserRegistrationSerializer},
        description="Регистрация нового пользователя",
        examples=[
            OpenApiExample(
                'Пример запроса',
                value={
                    'first_name': 'Иван',
                    'last_name': 'Иванов',
                    'email': 'ivan@example.com',
                    'password': 'SecurePass123',
                    'password_confirm': 'SecurePass123'
                },
                request_only=True,
            ),
        ],
    )
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
    """
    Вход пользователя
    """

    @extend_schema(
        request=UserLoginSerializer,
        responses={200: UserLoginSerializer},
        description="Вход в систему",
    )
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
    """
    Список товаров с фильтрацией и поиском
    """
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'shop', 'price']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'name', 'created_at']
    ordering = ['-created_at']

    @extend_schema(
        parameters=[
            OpenApiParameter(name='category', description='ID категории', required=False, type=int),
            OpenApiParameter(name='shop', description='ID магазина', required=False, type=int),
            OpenApiParameter(name='min_price', description='Минимальная цена', required=False, type=float),
            OpenApiParameter(name='max_price', description='Максимальная цена', required=False, type=float),
            OpenApiParameter(name='search', description='Поисковый запрос', required=False, type=str),
        ],
        description="Получение списка товаров с фильтрацией и поиском",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Product.objects.select_related('category', 'shop').all()

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
    """
    Управление контактами
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: ContactSerializer(many=True)},
        description="Получение списка контактов текущего пользователя",
    )
    def get(self, request):
        contacts = Contact.objects.filter(user=request.user)
        serializer = ContactSerializer(contacts, many=True)
        return Response({
            'status': True,
            'contacts': serializer.data
        })

    @extend_schema(
        request=ContactSerializer,
        responses={201: ContactSerializer},
        description="Добавление нового контакта",
    )
    def post(self, request):
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

    @extend_schema(
        request=ContactSerializer,
        responses={200: ContactSerializer},
        description="Обновление существующего контакта",
    )
    def put(self, request, pk):
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

    @extend_schema(
        description="Удаление контакта",
    )
    def delete(self, request, pk):
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
    """
    Управление корзиной
    """
    permission_classes = [IsAuthenticated]

    def get_cart(self, user):
        cart, _ = Cart.objects.get_or_create(user=user, is_active=True)
        return cart

    @extend_schema(
        responses={200: CartSerializer},
        description="Просмотр текущей корзины",
    )
    def get(self, request):
        cart = self.get_cart(request.user)
        serializer = CartSerializer(cart)
        return Response({
            'status': True,
            'cart': serializer.data
        })

    @extend_schema(
        request=AddToCartSerializer,
        responses={201: CartSerializer},
        description="Добавление товара в корзину",
    )
    def post(self, request):
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

    @extend_schema(
        description="Удаление товара из корзины",
    )
    def delete(self, request, item_id):
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
    """
    Подтверждение заказа
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=OrderConfirmSerializer,
        responses={201: OrderSerializer},
        description="Подтверждение заказа",
    )
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

        for item in cart.items.all():
            if item.product.quantity < item.quantity:
                return Response({
                    'status': False,
                    'error': f'Недостаточно товара "{item.product.name}" на складе'
                }, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.create(
            user=request.user,
            cart=cart,
            contact=contact,
            total_amount=cart.total,
            status='confirmed'
        )

        for item in cart.items.all():
            product = item.product
            product.quantity -= item.quantity
            product.save()

        cart.is_active = False
        cart.save()
        Cart.objects.create(user=request.user, is_active=True)

        send_order_confirmation_email.delay(order.id)

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
    """
    История и статусы заказов
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: OrderSerializer(many=True)},
        description="Получение истории всех заказов",
    )
    def get(self, request, order_id=None):
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


class SocialAuthView(APIView):
    """
    Авторизация через социальные сети (Google, GitHub)
    """
    permission_classes = []
    throttle_classes = [LoginThrottle]

    @extend_schema(
        request=SocialAuthSerializer,
        responses={200: {
            'type': 'object',
            'properties': {
                'status': {'type': 'boolean'},
                'message': {'type': 'string'},
                'access_token': {'type': 'string'},
                'refresh_token': {'type': 'string'},
                'user': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'email': {'type': 'string'},
                        'first_name': {'type': 'string'},
                        'last_name': {'type': 'string'}
                    }
                }
            }
        }},
        description="Авторизация через социальные сети",
    )
    @psa('social:complete')
    def post(self, request, backend):

        serializer = SocialAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        provider = serializer.validated_data['provider']
        access_token = serializer.validated_data['access_token']

        try:
            user = request.backend.do_auth(access_token)

            if not user:
                return Response({
                    'status': False,
                    'error': 'Ошибка аутентификации через социальную сеть'
                }, status=status.HTTP_400_BAD_REQUEST)


            login(request, user)

            refresh = RefreshToken.for_user(user)

            return Response({
                'status': True,
                'message': f'Успешная авторизация через {provider}',
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class UploadAvatarView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        request=UserAvatarSerializer,
        responses={200: UserAvatarSerializer},
        description="Загрузка аватара пользователя с асинхронной обработкой",
    )
    def post(self, request):
        user = request.user

        if 'avatar' not in request.FILES:
            return Response({
                'status': False,
                'error': 'Файл аватара не предоставлен'
            }, status=status.HTTP_400_BAD_REQUEST)

        avatar_file = request.FILES['avatar']

        if avatar_file.size > 5 * 1024 * 1024:
            return Response({
                'status': False,
                'error': 'Размер файла не должен превышать 5MB'
            }, status=status.HTTP_400_BAD_REQUEST)

        user.avatar = avatar_file
        user.save()

        process_user_avatar.delay(user.id)

        serializer = UserAvatarSerializer(user)
        return Response({
            'status': True,
            'message': 'Аватар загружен, обработка запущена в фоновом режиме',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        responses={200: UserAvatarSerializer},
        description="Получение аватара пользователя",
    )
    def get(self, request):
        user = request.user
        serializer = UserAvatarSerializer(user)
        return Response({
            'status': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class UploadProductImageView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        request=UploadImageSerializer,
        responses={201: ProductImageSerializer},
        description="Загрузка изображения товара с асинхронной обработкой",
    )
    def post(self, request):
        serializer = UploadImageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        product_id = serializer.validated_data.get('product_id')
        image_file = serializer.validated_data['image']
        is_main = serializer.validated_data.get('is_main', False)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({
                'status': False,
                'error': 'Товар не найден'
            }, status=status.HTTP_404_NOT_FOUND)

        if image_file.size > 5 * 1024 * 1024:
            return Response({
                'status': False,
                'error': 'Размер файла не должен превышать 5MB'
            }, status=status.HTTP_400_BAD_REQUEST)

        product_image = ProductImage.objects.create(
            product=product,
            image=image_file,
            is_main=is_main
        )

        if is_main:
            product.main_image = image_file
            product.save()

        process_product_image.delay(product_image.id)

        result_serializer = ProductImageSerializer(product_image)
        return Response({
            'status': True,
            'message': 'Изображение загружено, обработка запущена в фоновом режиме',
            'data': result_serializer.data
        }, status=status.HTTP_201_CREATED)


class ProductImageView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Получение всех изображений товара",
    )
    def get(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({
                'status': False,
                'error': 'Товар не найден'
            }, status=status.HTTP_404_NOT_FOUND)

        images = product.images.all()
        serializer = ProductImageSerializer(images, many=True)
        return Response({
            'status': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        description="Удаление изображения товара",
    )
    def delete(self, request, product_id, image_id):
        try:
            product = Product.objects.get(id=product_id)
            image = product.images.get(id=image_id)

            # Если это основное изображение, сбрасываем main_image
            if image.is_main:
                product.main_image = None
                product.save()

            image.delete()

            return Response({
                'status': True,
                'message': 'Изображение удалено'
            }, status=status.HTTP_204_NO_CONTENT)

        except Product.DoesNotExist:
            return Response({
                'status': False,
                'error': 'Товар не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        except ProductImage.DoesNotExist:
            return Response({
                'status': False,
                'error': 'Изображение не найдено'
            }, status=status.HTTP_404_NOT_FOUND)
