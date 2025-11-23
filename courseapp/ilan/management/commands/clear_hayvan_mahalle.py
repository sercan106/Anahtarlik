import logging
from django.core.management.base import BaseCommand
from django.db import connection

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'HayvanProfili mahalle CharField verilerini temizle'

    def handle(self, *args, **options):
        # SQL injection'dan korumalı - direkt tablo ismi yerine validate edilmeli
        # Ancak bu bir management command ve admin tarafından çalıştırılıyor
        # Tablo ismi hardcoded olduğu için güvenli
        with connection.cursor() as cursor:
            cursor.execute('UPDATE ilan_hayvanprofili SET mahalle = NULL')
            logger.info('HayvanProfili mahalle verileri temizlendi')

        self.stdout.write(self.style.SUCCESS('HayvanProfili mahalle verileri temizlendi'))
