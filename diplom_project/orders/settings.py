import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN', ''),
    integrations=[
        DjangoIntegration(),
        CeleryIntegration(),
        RedisIntegration(),
    ],
    traces_sample_rate=float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', 0.1)),
    send_default_pii=True,
    environment=os.environ.get('SENTRY_ENVIRONMENT', 'development'),
    release='1.0.0',
)

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-your-secret-key-here-change-in-production'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'baton',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'django_filters',
    'corsheaders',
    'drf_spectacular',
    'social_django',
    'imagekit',
    'baton.autodiscover',

    # Local
    'backend',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'orders.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'orders.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'backend.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
        'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10/minute',      # Неавторизованные: 10 запросов в минуту
        'user': '30/minute',      # Авторизованные: 30 запросов в минуту
        'register': '3/hour',     # Регистрация: 3 попытки в час
        'login': '5/minute',      # Логин: 5 попыток в минуту
        'cart': '20/minute',      # Корзина: 20 запросов в минуту
    },
}

from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True


# НАСТРОЙКИ CELERY

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Настройки для email (ТОЛЬКО ДЛЯ РАЗРАБОТКИ)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# НАСТРОЙКИ DRF-SPECTACULAR

SPECTACULAR_SETTINGS = {
    'TITLE': 'Diplom Project API',
    'DESCRIPTION': 'API для интернет-магазина с асинхронной обработкой заказов',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'displayRequestDuration': True,
    },
}

# НАСТРОЙКИ SOCIAL AUTH

SITE_ID = 1

AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',      # Google
    'social_core.backends.github.GithubOAuth2',      # GitHub
    'django.contrib.auth.backends.ModelBackend',     # Обычный вход по email/паролю
)

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get('GOOGLE_OAUTH2_KEY', '')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get('GOOGLE_OAUTH2_SECRET', '')
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]

SOCIAL_AUTH_GITHUB_KEY = os.environ.get('GITHUB_KEY', '')
SOCIAL_AUTH_GITHUB_SECRET = os.environ.get('GITHUB_SECRET', '')
SOCIAL_AUTH_GITHUB_SCOPE = ['user:email']

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

SOCIAL_AUTH_UID_LENGTH = 223

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)

# НАСТРОЙКИ DJANGO-BATON

BATON = {
    'SITE_HEADER': 'Diplom Project Admin',
    'SITE_TITLE': 'Diplom Project',
    'INDEX_TITLE': 'Управление интернет-магазином',
    'SUPPORT_HREF': 'https://github.com/your-username/diplom_project/issues',
    'COPYRIGHT': '© 2026 Diplom Project',
    'POWERED_BY': 'Django',
    'CONFIRM_UNSAVED_CHANGES': True,
    'SHOW_MULTIPART_UPLOADING': True,
    'ENABLE_IMAGES_PREVIEW': True,
    'CHANGELIST_FILTERS_IN_MODAL': True,
    'CHANGELIST_FILTERS_ALWAYS_OPEN': False,
    'CHANGELIST_FILTERS_FORM': True,
    'MENU_ALWAYS_COLLAPSED': False,
    'MENU_TITLE': 'Навигация',
    'MENU': (
        {'type': 'title', 'label': 'Основное', 'apps': ('auth',)},
        {
            'type': 'app',
            'name': 'auth',
            'label': 'Пользователи и группы',
            'icon': 'fa fa-users',
            'models': (
                {
                    'name': 'user',
                    'label': 'Пользователи'
                },
                {
                    'name': 'group',
                    'label': 'Группы'
                },
            )
        },
        {
            'type': 'app',
            'name': 'backend',
            'label': 'Магазин',
            'icon': 'fa fa-shopping-cart',
            'models': (
                {
                    'name': 'Product',
                    'label': 'Товары'
                },
                {
                    'name': 'Category',
                    'label': 'Категории'
                },
                {
                    'name': 'Shop',
                    'label': 'Магазины'
                },
                {
                    'name': 'Order',
                    'label': 'Заказы'
                },
                {
                    'name': 'Cart',
                    'label': 'Корзины'
                },
                {
                    'name': 'CartItem',
                    'label': 'Позиции корзин'
                },
                {
                    'name': 'Contact',
                    'label': 'Контакты'
                },
                {
                    'name': 'ProductImage',
                    'label': 'Изображения товаров'
                },

            )
        },
        {
            'type': 'app',
            'name': 'social_django',
            'label': 'Социальные сети',
            'icon': 'fa fa-share-alt',
            'models': (
                {
                    'name': 'UserSocialAuth',
                    'label': 'Социальные аккаунты'
                },
            )
        },
        {'type': 'free'},
    ),
}

# НАСТРОЙКИ IMAGEKIT

IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY = 'imagekit.cachefiles.strategies.Optimistic'
