from django.core.management.base import BaseCommand
from django.core.files import File
from shop.models import Urun, UrunResim
import os
import random
from pathlib import Path

class Command(BaseCommand):
    help = 'Media klasöründeki resimleri otomatik olarak ürünlere atar'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Önce mevcut tüm ürün resimlerini sil',
        )
        parser.add_argument(
            '--per-product',
            type=int,
            default=1,
            help='Her ürüne atanacak maksimum resim sayısı (varsayılan: 1)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('Ürünlere Resim Atama İşlemi Başlatılıyor...'))
        self.stdout.write(self.style.WARNING('=' * 70))

        # Mevcut kayıtları temizle (isteğe bağlı)
        if options['clear']:
            deleted_count = UrunResim.objects.all().count()
            UrunResim.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'[OK] {deleted_count} adet mevcut resim kaydı silindi'))

        # Media klasöründeki resimleri bul
        media_root = Path('media/urunler')

        if not media_root.exists():
            self.stdout.write(self.style.ERROR(f'[HATA] Media klasörü bulunamadı: {media_root}'))
            return

        # Tüm resim dosyalarını al
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        image_files = [
            f for f in media_root.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ]

        if not image_files:
            self.stdout.write(self.style.ERROR('[HATA] Media klasöründe resim dosyası bulunamadı!'))
            return

        self.stdout.write(self.style.SUCCESS(f'[OK] {len(image_files)} adet resim dosyası bulundu'))
        self.stdout.write('')

        # Tüm ürünleri al
        urunler = Urun.objects.all()
        total_products = urunler.count()

        if total_products == 0:
            self.stdout.write(self.style.ERROR('[HATA] Sistemde hiç ürün yok!'))
            return

        self.stdout.write(f'[INFO] {total_products} adet ürüne resim atanacak...')
        self.stdout.write('')

        # İstatistikler
        created_count = 0
        skipped_count = 0
        per_product = options['per_product']

        # Her ürün için resim ata
        for index, urun in enumerate(urunler, 1):
            try:
                # Her ürüne random resimler ata
                num_images = random.randint(1, min(per_product, len(image_files)))
                selected_images = random.sample(image_files, num_images)

                for img_file in selected_images:
                    # Resim yolunu media klasörüne göre ayarla
                    relative_path = f'urunler/{img_file.name}'

                    # UrunResim oluştur
                    urun_resim, created = UrunResim.objects.get_or_create(
                        urun=urun,
                        resim=relative_path
                    )

                    if created:
                        created_count += 1

                # İlerleme göster (her 5 üründe bir)
                if index % 5 == 0 or index == total_products:
                    progress = (index / total_products) * 100
                    self.stdout.write(
                        f'[PROGRESS] {index}/{total_products} '
                        f'({progress:.1f}%) - {created_count} resim atandı'
                    )

            except Exception as e:
                skipped_count += 1
                self.stdout.write(
                    self.style.ERROR(f'[HATA] Ürün #{urun.id} - {urun.ad}: {str(e)}')
                )

        # Özet rapor
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.SUCCESS('ISLEM TAMAMLANDI!'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(f'[RAPOR] OZET RAPOR:')
        self.stdout.write(f'  - Toplam Urun: {total_products}')
        self.stdout.write(f'  - Atanan Resim: {created_count}')
        self.stdout.write(f'  - Atlanan Urun: {skipped_count}')
        self.stdout.write(f'  - Basari Orani: {((total_products - skipped_count) / total_products * 100):.1f}%')
        self.stdout.write('')

        # Doğrulama
        self.stdout.write(self.style.SUCCESS('[DOGRULAMA]'))
        resimsiz_urunler = Urun.objects.filter(resimler__isnull=True).count()
        resimli_urunler = total_products - resimsiz_urunler

        self.stdout.write(f'  - Resimli Urunler: {resimli_urunler}')
        self.stdout.write(f'  - Resimsiz Urunler: {resimsiz_urunler}')

        if resimsiz_urunler > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'\n[DIKKAT] {resimsiz_urunler} adet urunun hala resmi yok!'
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS('\n[OK] Tum urunlerin resmi basariyla atandi!'))

        self.stdout.write(self.style.WARNING('=' * 70))
