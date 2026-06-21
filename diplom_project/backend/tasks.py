from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Order, User
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_order_confirmation_email(order_id):
    """Отправка email подтверждения заказа"""
    try:
        order = Order.objects.select_related('user', 'contact').get(id=order_id)
        user = order.user

        subject = f'Подтверждение заказа #{order.number}'
        message = f"""
        Здравствуйте, {user.first_name} {user.last_name}!

        Ваш заказ #{order.number} успешно оформлен.

        Детали заказа:
        - Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}
        - Сумма: {order.total_amount} руб.
        - Статус: {order.get_status_display()}

        Спасибо за покупку!
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
        )

        logger.info(f'Email подтверждения отправлен для заказа #{order.number}')
        return True

    except Order.DoesNotExist:
        logger.error(f'Заказ {order_id} не найден')
        return False
    except Exception as e:
        logger.error(f'Ошибка отправки email: {e}')
        return False


@shared_task
def process_user_avatar(user_id):
    try:
        user = User.objects.get(id=user_id)

        if not user.avatar:
            logger.warning(f'У пользователя {user_id} нет аватара')
            return False

        if not os.path.exists(user.avatar.path):
            logger.error(f'Файл аватара не найден для пользователя {user_id}')
            return False

        img = Image.open(user.avatar.path)

        sizes = [
            {'size': (50, 50), 'suffix': '_tiny'},
            {'size': (100, 100), 'suffix': '_thumb'},
            {'size': (300, 300), 'suffix': '_medium'},
        ]

        for size_config in sizes:
            size = size_config['size']
            suffix = size_config['suffix']
            img_copy = img.copy()
            img_copy.thumbnail(size, Image.Resampling.LANCZOS)

            base, ext = os.path.splitext(user.avatar.path)
            new_path = f"{base}{suffix}{ext}"
            img_copy.save(new_path, quality=85)

        logger.info(f'Аватар обработан для пользователя {user_id}')
        return True

    except User.DoesNotExist:
        logger.error(f'Пользователь {user_id} не найден')
        return False
    except Exception as e:
        logger.error(f'Ошибка обработки аватара для пользователя {user_id}: {e}')
        return False


@shared_task
def process_product_image(product_image_id):
    try:
        from .models import ProductImage

        product_image = ProductImage.objects.get(id=product_image_id)

        if not product_image.image:
            logger.warning(f'Изображение товара {product_image_id} не найдено')
            return False

        if not os.path.exists(product_image.image.path):
            logger.error(f'Файл изображения не найден для {product_image_id}')
            return False

        img = Image.open(product_image.image.path)

        sizes = [
            {'size': (200, 200), 'suffix': '_thumb'},
            {'size': (600, 600), 'suffix': '_medium'},
            {'size': (1200, 1200), 'suffix': '_large'},
        ]

        for size_config in sizes:
            size = size_config['size']
            suffix = size_config['suffix']

            img_copy = img.copy()
            img_copy.thumbnail(size, Image.Resampling.LANCZOS)

            base, ext = os.path.splitext(product_image.image.path)
            new_path = f"{base}{suffix}{ext}"
            img_copy.save(new_path, quality=85)

        logger.info(f'Изображение товара обработано {product_image_id}')
        return True

    except Exception as e:
        logger.error(f'Ошибка обработки изображения товара {product_image_id}: {e}')
        return False


@shared_task
def process_all_product_images(product_id):

    try:
        from .models import Product

        product = Product.objects.get(id=product_id)
        images = product.images.all()

        if not images.exists():
            logger.warning(f'У товара {product_id} нет изображений')
            return False

        for image in images:
            process_product_image.delay(image.id)

        logger.info(f'Запущена обработка {images.count()} изображений для товара {product_id}')
        return True

    except Product.DoesNotExist:
        logger.error(f'Товар {product_id} не найден')
        return False
    except Exception as e:
        logger.error(f'Ошибка обработки изображений товара {product_id}: {e}')
        return False
