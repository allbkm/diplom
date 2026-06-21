from django.contrib import admin
from .models import *


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Админка для пользователей"""
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    readonly_fields = ('date_joined', 'last_login')
    list_per_page = 25
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Личная информация', {'fields': ('first_name', 'last_name')}),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Даты', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    """Админка для магазинов"""
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Админка для категорий"""
    list_display = ('id', 'name')
    filter_horizontal = ('shops',)
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Админка для товаров"""
    list_display = ('id', 'name', 'shop', 'category', 'price', 'quantity')
    list_filter = ('shop', 'category', 'created_at')
    search_fields = ('name', 'description', 'model')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('price', 'quantity')
    list_per_page = 25
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'category', 'shop')
        }),
        ('Цены и количество', {
            'fields': ('price', 'quantity')
        }),
        ('Характеристики', {
            'fields': ('parameters',),
            'classes': ('collapse',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """Админка для контактов"""
    list_display = ('first_name', 'last_name', 'email', 'phone', 'city')
    list_filter = ('city',)
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    list_per_page = 25


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Админка для корзин"""
    list_display = ('id', 'user', 'is_active', 'created_at', 'total')
    list_filter = ('is_active', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Админка для позиций корзины"""
    list_display = ('id', 'cart', 'product', 'quantity', 'total')
    list_filter = ('cart__is_active',)
    search_fields = ('product__name',)
    list_per_page = 25


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Админка для заказов"""
    list_display = ('id', 'number', 'user', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at', 'user')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'number')
    list_editable = ('status',)
    list_per_page = 25
    fieldsets = (
        ('Информация о заказе', {
            'fields': ('user', 'contact', 'cart', 'status')
        }),
        ('Сумма', {
            'fields': ('total_amount',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
