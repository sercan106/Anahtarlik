from django.core.management.base import BaseCommand
from anahtarlik.dictionaries import Il, Ilce
import csv
import os

class Command(BaseCommand):
    help = 'il_ilce.csv dosyasından il ve ilçe verilerini yükler'

    def handle(self, *args, **options):
        # CSV dosyasının yolu
        csv_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'il_ilce.csv')
        
        if not os.path.exists(csv_file_path):
            self.stdout.write(
                self.style.ERROR(f'CSV dosyası bulunamadı: {csv_file_path}')
            )
            return
        
        self.stdout.write('İl-İlçe verileri yükleniyor...')
        
        created_il_count = 0
        created_ilce_count = 0
        
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                il_adi = row['il'].strip()
                ilce_adi = row['ilce'].strip()
                
                # İl'i oluştur veya al
                il, il_created = Il.objects.get_or_create(ad=il_adi)
                if il_created:
                    created_il_count += 1
                
                # İlçe'yi oluştur veya al
                ilce, ilce_created = Ilce.objects.get_or_create(il=il, ad=ilce_adi)
                if ilce_created:
                    created_ilce_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ {created_il_count} yeni il eklendi')
        )
        self.stdout.write(
            self.style.SUCCESS(f'✅ {created_ilce_count} yeni ilçe eklendi')
        )
        self.stdout.write(
            self.style.SUCCESS(f'📊 Toplam il sayısı: {Il.objects.count()}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'📊 Toplam ilçe sayısı: {Ilce.objects.count()}')
        )