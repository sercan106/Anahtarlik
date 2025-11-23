# shop/management/commands/create_shop_cards.py
from django.core.management.base import BaseCommand
from shop.models import MagazaKarti, Urun


class Command(BaseCommand):
    help = 'QR Künye ve Pet Ürünleri mağaza kartlarını oluşturur'

    def handle(self, *args, **options):
        # Mevcut kartları kontrol et (hem "QR Künye" hem "Etiket Ürünleri" için)
        existing_qr = MagazaKarti.objects.filter(
            baslik__icontains='QR Künye'
        ).first() or MagazaKarti.objects.filter(
            baslik__icontains='Etiket'
        ).first()
        
        existing_pet = MagazaKarti.objects.filter(
            baslik__icontains='Pet Ürünleri'
        ).first()

        # QR Künye / Etiket Ürünleri Kartı (İlk sırada - Sıra: 0)
        if not existing_qr:
            qr_kart = MagazaKarti.objects.create(
                baslik='Etiket Ürünleri',
                alt_baslik='Evcil dostlarınızın güvenliği için akıllı QR künye çözümleri',
                aciklama='Kaybolan evcil hayvanlarınızı bulmak hiç bu kadar kolay olmamıştı. Sunduğumuz QR künye çözümleri ile dostlarınızın bilgilerini dijital olarak paylaşın.',
                icon='🏷️',
                renk='#28a745',
                link_url='/shop/etiket/',
                buton_metni='Etiket Ürünleri',
                sira=0,
                aktif=True,
                urun_sayisi=Urun.objects.filter(urun_tipi='etiket', aktif=True).count()
            )
            self.stdout.write(
                self.style.SUCCESS(f'Etiket Ürünleri kartı oluşturuldu: {qr_kart.baslik}')
            )
        else:
            # Mevcut kartı güncelle
            existing_qr.baslik = 'Etiket Ürünleri'
            existing_qr.alt_baslik = 'Evcil dostlarınızın güvenliği için akıllı QR künye çözümleri'
            existing_qr.aciklama = 'Kaybolan evcil hayvanlarınızı bulmak hiç bu kadar kolay olmamıştı. Sunduğumuz QR künye çözümleri ile dostlarınızın bilgilerini dijital olarak paylaşın.'
            existing_qr.icon = '🏷️'
            existing_qr.renk = '#28a745'
            existing_qr.link_url = '/shop/etiket/'
            existing_qr.buton_metni = 'Etiket Ürünleri'
            existing_qr.sira = 0
            existing_qr.aktif = True
            existing_qr.urun_sayisi = Urun.objects.filter(urun_tipi='etiket', aktif=True).count()
            existing_qr.save()
            self.stdout.write(
                self.style.SUCCESS(f'Etiket Ürünleri kartı güncellendi: {existing_qr.baslik}')
            )

        # Pet Ürünleri Kartı (İkinci sırada - Sıra: 1)
        if not existing_pet:
            pet_kart = MagazaKarti.objects.create(
                baslik='Pet Ürünleri',
                alt_baslik='Evcil dostlarınız için yüksek kaliteli pet ürünleri',
                aciklama='Kedi, köpek ve diğer evcil hayvanlarınız için geniş ürün yelpazesi. Oyuncaklardan mama kaplarına, bakım ürünlerinden aksesuarlara kadar her şey burada.',
                icon='🐾',
                renk='#ff8533',
                link_url='/shop/petshop/',
                buton_metni='Pet Ürünleri',
                sira=1,
                aktif=True,
                urun_sayisi=Urun.objects.filter(urun_tipi='normal', aktif=True).count()
            )
            self.stdout.write(
                self.style.SUCCESS(f'Pet Ürünleri kartı oluşturuldu: {pet_kart.baslik}')
            )
        else:
            # Mevcut kartı güncelle ve aktif yap
            existing_pet.baslik = 'Pet Ürünleri'
            existing_pet.alt_baslik = 'Evcil dostlarınız için yüksek kaliteli pet ürünleri'
            existing_pet.aciklama = 'Kedi, köpek ve diğer evcil hayvanlarınız için geniş ürün yelpazesi. Oyuncaklardan mama kaplarına, bakım ürünlerinden aksesuarlara kadar her şey burada.'
            existing_pet.icon = '🐾'
            existing_pet.renk = '#ff8533'
            existing_pet.link_url = '/shop/petshop/'
            existing_pet.buton_metni = 'Pet Ürünleri'
            existing_pet.sira = 1
            existing_pet.aktif = True  # Aktif olduğundan emin ol
            existing_pet.urun_sayisi = Urun.objects.filter(urun_tipi='normal', aktif=True).count()
            existing_pet.save()
            self.stdout.write(
                self.style.SUCCESS(f'Pet Ürünleri kartı güncellendi ve aktif yapıldı: {existing_pet.baslik}')
            )

        self.stdout.write(
            self.style.SUCCESS('\nMagaza kartlari basariyla hazirlandi!')
        )

