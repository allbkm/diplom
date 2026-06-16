from django.core.management.base import BaseCommand
from django.db import transaction
import yaml
from backend.models import Shop, Category, Product


class Command(BaseCommand):
    help = 'Импорт товаров из YAML файла'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Путь к YAML файлу')

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = options['file_path']

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Файл {file_path} не найден'))
            return
        except yaml.YAMLError as e:
            self.stdout.write(self.style.ERROR(f'Ошибка парсинга YAML: {e}'))
            return

        # Создаем или получаем магазин
        shop_name = data.get('shop')
        if not shop_name:
            self.stdout.write(self.style.ERROR('В файле не указан магазин'))
            return

        shop, _ = Shop.objects.get_or_create(name=shop_name)
        self.stdout.write(f'Импорт в магазин: {shop.name}')

        # Импортируем категории
        categories = {}
        for cat_data in data.get('categories', []):
            category, _ = Category.objects.get_or_create(
                id=cat_data['id'],
                defaults={'name': cat_data['name']}
            )
            category.shops.add(shop)
            categories[cat_data['id']] = category

        # Импортируем товары
        imported_count = 0
        for product_data in data.get('goods', []):
            category_id = product_data.get('category')
            if category_id not in categories:
                self.stdout.write(self.style.WARNING(
                    f'Категория {category_id} не найдена для товара {product_data["id"]}'
                ))
                continue

            product, created = Product.objects.update_or_create(
                id=product_data['id'],
                defaults={
                    'name': product_data['name'],
                    'description': product_data.get('description', ''),
                    'category': categories[category_id],
                    'shop': shop,
                    'price': product_data['price'],
                    'quantity': product_data.get('quantity', 0),
                    'parameters': product_data.get('parameters', {})
                }
            )
            imported_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Успешно импортировано {imported_count} товаров')
        )
