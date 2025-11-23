# shop/management/commands/fix_cat_products.py
from django.core.management.base import BaseCommand
from shop.models import Urun, Kategori, MagazaKarti
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Kedi ürünlerini petshop bölümüne taşır ve örnek ürünler oluşturur'

    def handle(self, *args, **options):
        # Kategorileri oluştur
        kedi_kategori, created = Kategori.objects.get_or_create(
            slug='kedi-urunleri',
            defaults={
                'ad': 'Kedi Ürünleri',
                'icon': '🐱',
                'sira': 1,
                'aktif': True
            }
        )
        
        kopek_kategori, created = Kategori.objects.get_or_create(
            slug='kopek-urunleri',
            defaults={
                'ad': 'Köpek Ürünleri',
                'icon': '🐶',
                'sira': 2,
                'aktif': True
            }
        )
        
        tavsan_kategori, created = Kategori.objects.get_or_create(
            slug='tavsan-urunleri',
            defaults={
                'ad': 'Tavşan Ürünleri',
                'icon': '🐰',
                'sira': 3,
                'aktif': True
            }
        )

        # Örnek kedi ürünleri oluştur
        kedi_urunleri = [
            {
                'ad': 'Premium Kedi Maması',
                'kisa_aciklama': 'Yüksek proteinli, doğal içerikli kedi maması',
                'aciklama': 'Evcil kediniz için özel olarak formüle edilmiş premium mama. Doğal protein kaynakları ve vitaminler içerir.',
                'fiyat': 89.99,
                'indirimli_fiyat': 69.99,
                'stok': 50,
                'hayvan_turu': 'Kedi',
                'one_cikan': True,
                'yeni_urun': True,
                'kategoriler': [kedi_kategori]
            },
            {
                'ad': 'Kedi Oyuncağı - Tüylü Top',
                'kisa_aciklama': 'Kedilerin favori oyuncağı',
                'aciklama': 'Renkli tüylü top, kedinizin oyun ihtiyacını karşılar.',
                'fiyat': 24.99,
                'stok': 100,
                'hayvan_turu': 'Kedi',
                'one_cikan': True,
                'kategoriler': [kedi_kategori]
            },
            {
                'ad': 'Kedi Kumu - Kokusuz',
                'kisa_aciklama': 'Kokuyu hapseden doğal kedi kumu',
                'aciklama': 'Kokuyu hapseden bentonit kedi kumu. 10L paket.',
                'fiyat': 45.99,
                'stok': 30,
                'hayvan_turu': 'Kedi',
                'one_cikan': True,
                'kategoriler': [kedi_kategori]
            },
            {
                'ad': 'Kedi Tasması - Deri',
                'kisa_aciklama': 'Yumuşak deri kedi tasması',
                'aciklama': 'Yumuşak deri malzemeden üretilmiş, ayarlanabilir kedi tasması.',
                'fiyat': 35.99,
                'stok': 25,
                'hayvan_turu': 'Kedi',
                'one_cikan': True,
                'kategoriler': [kedi_kategori]
            },
            {
                'ad': 'Kedi Tırmalama Tahtası',
                'kisa_aciklama': 'Doğal ahşap tırmalama tahtası',
                'aciklama': 'Kedilerin tırnaklarını törpülemesi için doğal ahşap tahta.',
                'fiyat': 79.99,
                'stok': 20,
                'hayvan_turu': 'Kedi',
                'one_cikan': True,
                'kategoriler': [kedi_kategori]
            }
        ]

        # Örnek köpek ürünleri oluştur
        kopek_urunleri = [
            {
                'ad': 'Köpek Maması - Yetişkin',
                'kisa_aciklama': 'Yetişkin köpekler için dengeli beslenme',
                'aciklama': 'Yetişkin köpeklerin ihtiyaçlarına göre formüle edilmiş mama.',
                'fiyat': 129.99,
                'indirimli_fiyat': 99.99,
                'stok': 40,
                'hayvan_turu': 'Köpek',
                'one_cikan': True,
                'yeni_urun': True,
                'kategoriler': [kopek_kategori]
            },
            {
                'ad': 'Köpek Oyuncağı - Kemik',
                'kisa_aciklama': 'Dayanıklı köpek kemik oyuncağı',
                'aciklama': 'Köpeklerin çiğneme ihtiyacını karşılayan dayanıklı oyuncak.',
                'fiyat': 39.99,
                'stok': 60,
                'hayvan_turu': 'Köpek',
                'one_cikan': True,
                'kategoriler': [kopek_kategori]
            },
            {
                'ad': 'Köpek Tasması - Nylon',
                'kisa_aciklama': 'Güçlü nylon köpek tasması',
                'aciklama': 'Dayanıklı nylon malzemeden üretilmiş köpek tasması.',
                'fiyat': 29.99,
                'stok': 50,
                'hayvan_turu': 'Köpek',
                'one_cikan': True,
                'kategoriler': [kopek_kategori]
            }
        ]

        # Örnek tavşan ürünleri oluştur
        tavsan_urunleri = [
            {
                'ad': 'Tavşan Yemi - Karışık',
                'kisa_aciklama': 'Tavşanlar için özel karışık yem',
                'aciklama': 'Tavşanların beslenme ihtiyaçlarına uygun karışık yem.',
                'fiyat': 34.99,
                'stok': 35,
                'hayvan_turu': 'Tavşan',
                'one_cikan': True,
                'kategoriler': [tavsan_kategori]
            },
            {
                'ad': 'Tavşan Kafesi - Büyük',
                'kisa_aciklama': 'Geniş tavşan kafesi',
                'aciklama': 'Tavşanların rahatça hareket edebileceği geniş kafes.',
                'fiyat': 199.99,
                'stok': 15,
                'hayvan_turu': 'Tavşan',
                'one_cikan': True,
                'kategoriler': [tavsan_kategori]
            }
        ]

        # Tüm ürünleri birleştir
        tum_urunler = kedi_urunleri + kopek_urunleri + tavsan_urunleri

        # Ürünleri oluştur
        for urun_data in tum_urunler:
            kategoriler = urun_data.pop('kategoriler')
            urun, created = Urun.objects.get_or_create(
                ad=urun_data['ad'],
                defaults={
                    **urun_data,
                    'urun_tipi': 'normal',
                    'aktif': True
                }
            )
            
            if created:
                # Kategorileri ekle
                urun.kategoriler.set(kategoriler)
                self.stdout.write(
                    self.style.SUCCESS(f'[OK] "{urun.ad}" ürünü başarıyla eklendi!')
                )
            else:
                # Mevcut ürünü güncelle
                for key, value in urun_data.items():
                    setattr(urun, key, value)
                urun.kategoriler.set(kategoriler)
                urun.save()
                self.stdout.write(
                    self.style.WARNING(f'[!] "{urun.ad}" ürünü güncellendi.')
                )

        # Mağaza kartlarını güncelle
        try:
            petshop_kart = MagazaKarti.objects.get(baslik__icontains='Pet Ürünleri')
            petshop_kart.urun_sayisi = Urun.objects.filter(urun_tipi='normal', aktif=True).count()
            petshop_kart.save()
            self.stdout.write(
                self.style.SUCCESS(f'Pet Ürünleri kartı güncellendi: {petshop_kart.urun_sayisi} ürün')
            )
        except MagazaKarti.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Pet Ürünleri kartı bulunamadı!')
            )

        self.stdout.write(
            self.style.SUCCESS('\n[BASARILI] Kedi ürünleri petshop bölümüne taşındı ve örnek ürünler oluşturuldu!')
        )
