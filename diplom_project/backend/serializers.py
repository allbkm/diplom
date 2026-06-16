from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import *

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'password_confirm']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """Сериализатор для входа"""
    email = serializers.EmailField()
    password = serializers.CharField()


class ProductSerializer(serializers.ModelSerializer):
    """Сериализатор товара"""
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'shop', 'shop_name',
            'category', 'category_name', 'price', 'quantity',
            'parameters', 'created_at', 'updated_at'
        ]


class ContactSerializer(serializers.ModelSerializer):
    """Сериализатор контакта"""
    class Meta:
        model = Contact
        fields = [
            'id', 'last_name', 'first_name', 'middle_name',
            'email', 'phone', 'city', 'street', 'house',
            'building', 'structure', 'apartment'
        ]
        read_only_fields = ['id']


class CartItemSerializer(serializers.ModelSerializer):
    """Сериализатор позиции корзины"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    shop_name = serializers.CharField(source='product.shop.name', read_only=True)
    price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_name', 'shop_name', 'price', 'quantity', 'total']

    def get_total(self, obj):
        return obj.total


class CartSerializer(serializers.ModelSerializer):
    """Сериализатор корзины"""
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total', 'is_active', 'created_at', 'updated_at']

    def get_total(self, obj):
        return obj.total


class AddToCartSerializer(serializers.Serializer):
    """Сериализатор для добавления в корзину"""
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)


class OrderSerializer(serializers.ModelSerializer):
    """Сериализатор заказа"""
    number = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'number', 'created_at', 'total_amount', 'status', 'status_display']

    def get_number(self, obj):
        return obj.number


class OrderDetailSerializer(serializers.ModelSerializer):
    """Сериализатор деталей заказа"""
    number = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    contact = ContactSerializer(read_only=True)
    items = CartItemSerializer(source='cart.items', many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'number', 'created_at', 'status', 'status_display',
            'total_amount', 'contact', 'items'
        ]

    def get_number(self, obj):
        return obj.number


class OrderConfirmSerializer(serializers.Serializer):
    """Сериализатор подтверждения заказа"""
    cart_id = serializers.IntegerField()
    contact_id = serializers.IntegerField()
