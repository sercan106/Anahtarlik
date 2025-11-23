import logging
from django.core.management.base import BaseCommand
from django.db import connection
from anahtarlik.dictionaries import Il, Ilce, Mahalle
import csv
import os

logger = logging.getLogger(__name__)

# Güvenli tablo isimleri
ALLOWED_LOCATION_TABLES = ['anahtarlik_il', 'anahtarlik_ilce', 'anahtarlik_mahalle']


class Command(BaseCommand):
    help = 'Türkiye il/ilçe/mahalle verilerini CSV dosyasından yükler'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            default=r'C:\Users\user\Downloads\archive (1)\turkey_province_district_neighborhood.csv',
            help='CSV dosyasının tam yolu'
        )

    def handle(self, *args, **options):
        csv_file_path = options['csv_path']

        if not os.path.exists(csv_file_path):
            self.stdout.write(
                self.style.ERROR(f'CSV dosyası bulunamadı: {csv_file_path}')
            )
            return

        # 1. ADIM: Mevcut verileri temizle
        self.stdout.write(self.style.WARNING('Mevcut veriler temizleniyor...'))

        mahalle_count = Mahalle.objects.count()
        ilce_count = Ilce.objects.count()
        il_count = Il.objects.count()

        self.stdout.write(f'   Silinecek: {mahalle_count} mahalle, {ilce_count} ilce, {il_count} il')

        # Use raw SQL to bypass Django's ORM and directly delete data
        with connection.cursor() as cursor:
            # Disable foreign key constraints temporarily
            cursor.execute('PRAGMA foreign_keys = OFF;')

            try:
                # Delete using raw SQL - whitelist kontrolü ile güvenli
                for table in ALLOWED_LOCATION_TABLES:
                    if table in ALLOWED_LOCATION_TABLES:
                        cursor.execute(f'DELETE FROM {table};')
                        logger.info(f'{table} silindi')
                
                self.stdout.write(self.style.SUCCESS('   Mahalleler silindi'))
                self.stdout.write(self.style.SUCCESS('   Ilceler silindi'))
                self.stdout.write(self.style.SUCCESS('   Iller silindi'))
            except Exception as e:
                logger.error(f'Silme hatası: {str(e)}', exc_info=True)
            finally:
                # Re-enable foreign key constraints
                cursor.execute('PRAGMA foreign_keys = ON;')

        # 2. ADIM: CSV'den verileri yükle
        self.stdout.write(self.style.WARNING('\nCSV dosyasi yukleniyor...'))

        il_cache = {}  # İl nesnelerini cache'le (performans için)
        ilce_cache = {}  # İlçe nesnelerini cache'le

        created_il_count = 0
        created_ilce_count = 0
        created_mahalle_count = 0

        with open(csv_file_path, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)

            for index, row in enumerate(reader, start=1):
                il_adi = row['il'].strip().capitalize()
                ilce_adi = row['ilce'].strip().capitalize()
                mahalle_adi = row['mahalle'].strip().capitalize()

                # İl'i oluştur veya cache'den al
                if il_adi not in il_cache:
                    il, il_created = Il.objects.get_or_create(ad=il_adi)
                    il_cache[il_adi] = il
                    if il_created:
                        created_il_count += 1
                else:
                    il = il_cache[il_adi]

                # İlçe'yi oluştur veya cache'den al
                ilce_key = f"{il_adi}_{ilce_adi}"
                if ilce_key not in ilce_cache:
                    ilce, ilce_created = Ilce.objects.get_or_create(
                        il=il,
                        ad=ilce_adi
                    )
                    ilce_cache[ilce_key] = ilce
                    if ilce_created:
                        created_ilce_count += 1
                else:
                    ilce = ilce_cache[ilce_key]

                # Mahalle'yi oluştur
                mahalle, mahalle_created = Mahalle.objects.get_or_create(
                    ilce=ilce,
                    ad=mahalle_adi
                )
                if mahalle_created:
                    created_mahalle_count += 1

                # İlerleme göster (her 1000 satırda bir)
                if index % 1000 == 0:
                    self.stdout.write(f'   Islenen satir: {index:,}')

        # 3. ADIM: Özet
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('BASARIYLA TAMAMLANDI!'))
        self.stdout.write('='*60)
        self.stdout.write(f'{created_il_count} il eklendi')
        self.stdout.write(f'{created_ilce_count} ilce eklendi')
        self.stdout.write(f'{created_mahalle_count} mahalle eklendi')
        self.stdout.write('='*60)

        # 4. ADIM: Doğrulama
        self.stdout.write('\nVeritabani Durumu:')
        self.stdout.write(f'   Toplam Il: {Il.objects.count()}')
        self.stdout.write(f'   Toplam Ilce: {Ilce.objects.count()}')
        self.stdout.write(f'   Toplam Mahalle: {Mahalle.objects.count()}')

        # Örnek veriler göster
        self.stdout.write('\nOrnek Veriler:')
        for il in Il.objects.all()[:3]:
            self.stdout.write(f'   {il.ad}')
            for ilce in il.ilceler.all()[:2]:
                self.stdout.write(f'      {ilce.ad}')
                for mahalle in ilce.mahalleler.all()[:3]:
                    self.stdout.write(f'         {mahalle.ad}')
