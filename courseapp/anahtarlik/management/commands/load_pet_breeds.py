from django.core.management.base import BaseCommand
from anahtarlik.dictionaries import Tur, Irk


class Command(BaseCommand):
    help = 'Pet türleri ve ırklarını yükler'

    def handle(self, *args, **options):
        # Pet türleri ve ırkları verisi
        pet_data = {
            'Köpek': [
                'Toy Poodle', 'Maltipoo', 'Pomeranian Boo', 'Maltese Terrier', 'Doberman',
                'Golden Retriever', 'Border Collie', 'Chihuahua', 'Labrador Retriever',
                'French Bulldog', 'Cane Corso', 'Cavalier King Charles', 'Çin Aslanı',
                'Rottweiler', 'Sibirya Kurdu (Husky)', 'Belçika Kurdu', 'Akita Inu',
                'Pug', 'Shih Tzu', 'Alman Kurdu', 'Morkie', 'Labradoodle',
                'Bernese Dağ Köpeği', 'Dakhund - Sosis Köpek', 'Jack Russell Terrier',
                'Yorkshire Terrier', 'Amerikan Cocker', 'İngiliz Bulldog', 'Beagle',
                'İngiliz Cocker', 'Pekinez', 'Schnauzer', 'Samoyed', 'American Bully',
                'Shiba Köpek', 'bernedoodle', 'corgi', 'Goldendoodle', 'Lagotto Romagnolo',
                'Saint Bernard', 'Avustralya Çoban Köpeği', 'Alabay (Alabai)',
                'Amerikan Bulldog', 'Cavapoo', 'Cockapoo', 'Dogo Argentino',
                'Bişon Çuha Köpeği', 'Dalmaçyalı', 'Afgan Tazısı', 'Boxer Köpek',
                'Danua (Great Dane)', 'Fransız Mastiff', 'İngiliz Çoban Köpeği',
                'İngiliz Staffordshire', 'Kangal', 'Kaniş', 'Newfoundland Köpek',
                'Pitbull', 'Spitz', 'Tibet Mastifi', 'Wolfdog'
            ],
            'Kedi': [
                'British Shorthair', 'Scottish Fold', 'British Longhair', 'Ragdoll Kedisi',
                'Bengal Kedisi', 'Maine Coon', 'Scottish Straight', 'İran Kedisi',
                'Sfenks Kedisi', 'Diğer Irklar', 'Munchkin Kedisi', 'Scottish Fold Longhair',
                'Siyam Kedisi', 'Bombay Kedisi', 'Chinchilla', 'Exotic Shorthair',
                'Sarman Kedi'
            ]
        }

        # Mevcut verileri temizle
        self.stdout.write(self.style.WARNING('Mevcut pet verileri temizleniyor...'))
        
        irk_count = Irk.objects.count()
        tur_count = Tur.objects.count()
        
        self.stdout.write(f'   Silinecek: {irk_count} ırk, {tur_count} tür')
        
        # Önce ırkları sil (foreign key constraint nedeniyle)
        Irk.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('   Irklar silindi'))
        
        # Sonra türleri sil
        Tur.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('   Türler silindi'))

        # Verileri yükle
        self.stdout.write(self.style.WARNING('\nPet türleri ve ırkları yükleniyor...'))
        
        created_tur_count = 0
        created_irk_count = 0

        for tur_adi, irk_listesi in pet_data.items():
            # Türü oluştur
            tur, tur_created = Tur.objects.get_or_create(ad=tur_adi)
            if tur_created:
                created_tur_count += 1
                self.stdout.write(f'   Tür eklendi: {tur_adi}')

            # Bu türe ait ırkları oluştur
            for irk_adi in irk_listesi:
                irk, irk_created = Irk.objects.get_or_create(
                    tur=tur,
                    ad=irk_adi
                )
                if irk_created:
                    created_irk_count += 1

        # Özet
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('BASARIYLA TAMAMLANDI!'))
        self.stdout.write('='*60)
        self.stdout.write(f'{created_tur_count} tür eklendi')
        self.stdout.write(f'{created_irk_count} ırk eklendi')
        self.stdout.write('='*60)

        # Doğrulama
        self.stdout.write('\nVeritabani Durumu:')
        self.stdout.write(f'   Toplam Tür: {Tur.objects.count()}')
        self.stdout.write(f'   Toplam Irk: {Irk.objects.count()}')

        # Örnek veriler göster
        self.stdout.write('\nÖrnek Veriler:')
        for tur in Tur.objects.all():
            self.stdout.write(f'   {tur.ad}:')
            for irk in tur.irklari.all()[:5]:  # İlk 5 ırkı göster
                self.stdout.write(f'      - {irk.ad}')
            if tur.irklari.count() > 5:
                self.stdout.write(f'      ... ve {tur.irklari.count() - 5} ırk daha')





