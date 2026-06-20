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
