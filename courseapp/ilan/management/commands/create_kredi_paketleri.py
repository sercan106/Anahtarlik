from django.core.management.base import BaseCommand
from ilan.models import KrediPaketi


class Command(BaseCommand):
    help = 'Kredi paketlerini oluşturur'

    def handle(self, *args, **options):
        # Mevcut paketleri temizle
        KrediPaketi.objects.all().delete()
        self.stdout.write(self.style.WARNING('Mevcut kredi paketleri temizlendi.'))

        # Kredi paketlerini oluştur
        paketler = [
            {
                'ad': 'Başlangıç Paketi',
                'aciklama': 'Hızlı başlangıç için ideal paket',
                'kredi_adet': 50,
                'fiyat': 20.00,
                'aktif': True,
                'sira': 1,
                'one_cikan': False,
                'etiket': ''
            },
            {
                'ad': 'Popüler Paket',
                'aciklama': 'En çok tercih edilen paket',
                'kredi_adet': 150,
                'fiyat': 50.00,
                'aktif': True,
                'sira': 2,
                'one_cikan': True,
                'etiket': 'En Popüler'
            },
            {
                'ad': 'Küçük Paket',
                'aciklama': 'Küçük ihtiyaçlar için',
                'kredi_adet': 100,
                'fiyat': 35.00,
                'aktif': True,
                'sira': 3,
                'one_cikan': False,
                'etiket': ''
            },
            {
                'ad': 'Avantajlı Paket',
                'aciklama': 'Daha fazla kredi, daha uygun fiyat',
                'kredi_adet': 300,
                'fiyat': 95.00,
                'aktif': True,
                'sira': 4,
                'one_cikan': False,
                'etiket': ''
            },
            {
                'ad': 'Mega Paket',
                'aciklama': 'En avantajlı paket',
                'kredi_adet': 500,
                'fiyat': 150.00,
                'aktif': True,
                'sira': 5,
                'one_cikan': True,
                'etiket': 'En Avantajlı'
            },
            {
                'ad': 'Premium Paket',
                'aciklama': 'Büyük ihtiyaçlar için maximum paket',
                'kredi_adet': 1000,
                'fiyat': 280.00,
                'aktif': True,
                'sira': 6,
                'one_cikan': True,
                'etiket': 'Premium'
            }
        ]

        created_count = 0
        for paket_data in paketler:
            paket = KrediPaketi.objects.create(**paket_data)
            created_count += 1
            birim_fiyat = paket_data['fiyat'] / paket_data['kredi_adet']
            self.stdout.write(
                self.style.SUCCESS(
                    f'[OK] {paket.ad} olusturuldu: {paket_data["kredi_adet"]} kredi - '
                    f'TL {paket_data["fiyat"]} (Birim: TL {birim_fiyat:.4f})'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n[SUCCESS] Toplam {created_count} kredi paketi basariyla olusturuldu!'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                '\nNot: İlan başına 150 kredi harcanıyor (öne çıkarma: +50 kredi)'
            )
        )
