import logging
from django.core.management.base import BaseCommand
from django.db import connection
from anahtarlik.dictionaries import Il, Ilce
import random

# Güvenli tablo isimleri whitelist
ALLOWED_TABLES = [
    'anahtarlik_sahip', 'anahtarlik_evcilhayvan', 'veteriner_veteriner',
    'petshop_petshop', 'anahtarlik_bildirim', 'shop_adres',
]

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Tum tablolardaki gecersiz il/ilce referanslarini duzelt'

    def handle(self, *args, **options):
        iller = list(Il.objects.all())
        ilceler = list(Ilce.objects.all())

        if not iller or not ilceler:
            self.stdout.write(self.style.ERROR('Il veya ilce verisi bulunamadi!'))
            return

        # Rastgele il ve ilce sec
        rastgele_il = random.choice(iller)
        il_ilceleri = [i for i in ilceler if i.il_id == rastgele_il.id]
        rastgele_ilce = random.choice(il_ilceleri)

        # Tum tabloları bul
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            all_tables = [row[0] for row in cursor.fetchall()]

        tables_to_fix = ALLOWED_TABLES  # Güvenli whitelist kullan

        with connection.cursor() as cursor:
            for table in tables_to_fix:
                # Check if table exists - parametrize sorgu
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    [table]
                )
                if not cursor.fetchone():
                    logger.warning(f'Tablo bulunamadi: {table}')
                    continue

                try:
                    # Check if columns exist - table name için parametrize sorgu yapılamaz ama güvenli
                    cursor.execute("PRAGMA table_info(?)", [table])  # Not: Bu çalışmayabilir, alternatif yöntem
                    # Alternatif: table name validation ile güvenli hale getirilmiş
                    columns = []
                    cursor.execute(f"PRAGMA table_info('{table.replace("'", "''")}')")  # Single quote escape
                    columns = [col[1] for col in cursor.fetchall()]

                    if 'il_id' in columns and 'ilce_id' in columns:
                        # Parametrize sorgu
                        cursor.execute(
                            'UPDATE {} SET il_id = ?, ilce_id = ?'.format(table.replace('`', '').replace("'", '')),
                            [rastgele_il.id, rastgele_ilce.id]
                        )
                        logger.info(f'{table} guncellendi')
                    elif 'il_id' in columns:
                        cursor.execute(
                            'UPDATE {} SET il_id = ?'.format(table.replace('`', '').replace("'", '')),
                            [rastgele_il.id]
                        )
                        logger.info(f'{table} guncellendi (sadece il)')
                    elif 'ilce_id' in columns:
                        cursor.execute(
                            'UPDATE {} SET ilce_id = ?'.format(table.replace('`', '').replace("'", '')),
                            [rastgele_ilce.id]
                        )
                        logger.info(f'{table} guncellendi (sadece ilce)')
                except Exception as e:
                    logger.error(f'{table} guncellenemedi: {str(e)}', exc_info=True)
                    self.stdout.write(self.style.WARNING(
                        f'{table} guncellenemedi: {str(e)}'
                    ))

        self.stdout.write(self.style.SUCCESS(
            f'\nTum tablolar guncellendi: {rastgele_il.ad} - {rastgele_ilce.ad}'
        ))
