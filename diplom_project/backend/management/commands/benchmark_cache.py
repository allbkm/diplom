from django.core.management.base import BaseCommand
from django.core.cache import cache
from rest_framework.test import APIClient
import time


class Command(BaseCommand):
    help = 'Бенчмарк производительности кэширования'

    def handle(self, *args, **options):
        client = APIClient()
        url = '/api/products/'

        self.stdout.write('=== БЕНЧМАРК КЭШИРОВАНИЯ ===\n')

        cache.clear()

        start_time = time.time()
        for i in range(10):
            response = client.get(url)
        no_cache_time = time.time() - start_time

        start_time = time.time()
        for i in range(10):
            response = client.get(url)
        with_cache_time = time.time() - start_time

        self.stdout.write(f'10 запросов БЕЗ кэша: {no_cache_time:.3f} секунд')
        self.stdout.write(f'10 запросов С кэшем: {with_cache_time:.3f} секунд')

        improvement = ((no_cache_time - with_cache_time) / no_cache_time) * 100
        self.stdout.write(f'Ускорение: {improvement:.1f}%\n')

        # Проверяем статус кэша
        self.stdout.write(f'Cache Status: {response.get("X-Cache-Status", "N/A")}')
        self.stdout.write(f'Query Time: {response.get("X-Query-Time", "N/A")}')
