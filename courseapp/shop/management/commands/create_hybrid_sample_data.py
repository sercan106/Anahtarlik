from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from shop.models import Kategori, Urun, UrunResim
from etiket.models import EtiketKategori
import json

class Command(BaseCommand):
    help = 'Hibrit mağaza için örnek veri oluşturur'

    def handle(self, *args, **options):
        self.stdout.write('Hibrit mağaza örnek verileri oluşturuluyor...')
        
        # 1. Normal Kategoriler (Petshop)
        petshop_kategoriler = [
            {'ad': 'Kedi Mamaları', 'slug': 'kedi-mamalari'},
            {'ad': 'Köpek Mamaları', 'slug': 'kopek-mamalari'},
            {'ad': 'Oyuncaklar', 'slug': 'oyuncaklar'},
            {'ad': 'Bakım Ürünleri', 'slug': 'bakim-urunleri'},
            {'ad': 'Aksesuarlar', 'slug': 'aksesuarlar'},
        ]
        
        for kat_data in petshop_kategoriler:
            kategori, created = Kategori.objects.get_or_create(
                slug=kat_data['slug'],
                defaults={'ad': kat_data['ad']}
            )
            if created:
                self.stdout.write(f'Kategori olusturuldu: {kategori.ad}')
        
        # 2. Etiket Kategorileri (Mevcut etiket app'ten)
        etiket_kategoriler = [
            {'ad': 'Premium Etiketler', 'slug': 'premium-etiketler', 'renk': '#28a745'},
            {'ad': 'Standart Etiketler', 'slug': 'standart-etiketler', 'renk': '#007bff'},
            {'ad': 'Özel Tasarım Etiketler', 'slug': 'ozel-tasarim-etiketler', 'renk': '#dc3545'},
        ]
        
        for kat_data in etiket_kategoriler:
            kategori, created = EtiketKategori.objects.get_or_create(
                ad=kat_data['ad'],
                defaults={
                    'renk': kat_data['renk'],
                    'aktif': True
                }
            )
            if created:
                self.stdout.write(f'Etiket Kategorisi olusturuldu: {kategori.ad}')
        
        # 3. Örnek Ürünler - Etiket Ürünleri
        etiket_urunler = [
            {
                'ad': 'Premium Kedi Etiketi',
                'kisa_aciklama': 'Su geçirmez, dayanıklı kedi etiketi',
                'aciklama': 'Premium kalitede, su geçirmez malzemeden üretilmiş kedi etiketi. QR kod ile hızlı erişim.',
                'fiyat': 25.00,
                'stok': 100,
                'urun_tipi': 'etiket',
                'etiket_kategori': 'Premium Etiketler',
                'hayvan_turu': 'Kedi',
                'kullanim_suresi': 365,
                'etiket_ozellikler': {
                    'malzeme': 'Su geçirmez',
                    'boyut': '3x2 cm',
                    'renk': 'Mavi'
                }
            },
            {
                'ad': 'Standart Köpek Etiketi',
                'kisa_aciklama': 'Ekonomik köpek etiketi',
                'aciklama': 'Standart kalitede, dayanıklı köpek etiketi. QR kod ile kolay erişim.',
                'fiyat': 15.00,
                'stok': 200,
                'urun_tipi': 'etiket',
                'etiket_kategori': 'Standart Etiketler',
                'hayvan_turu': 'Köpek',
                'kullanim_suresi': 180,
                'etiket_ozellikler': {
                    'malzeme': 'Plastik',
                    'boyut': '2.5x1.5 cm',
                    'renk': 'Kırmızı'
                }
            },
            {
                'ad': 'Özel Tasarım Kuş Etiketi',
                'kisa_aciklama': 'Kişiselleştirilebilir kuş etiketi',
                'aciklama': 'Özel tasarım, kişiselleştirilebilir kuş etiketi. QR kod ile hızlı erişim.',
                'fiyat': 35.00,
                'stok': 50,
                'urun_tipi': 'etiket',
                'etiket_kategori': 'Özel Tasarım Etiketler',
                'hayvan_turu': 'Kuş',
                'kullanim_suresi': 730,
                'etiket_ozellikler': {
                    'malzeme': 'Metal',
                    'boyut': '2x1 cm',
                    'renk': 'Altın'
                }
            }
        ]
        
        for urun_data in etiket_urunler:
            etiket_kategori = EtiketKategori.objects.get(ad=urun_data['etiket_kategori'])
            
            urun, created = Urun.objects.get_or_create(
                ad=urun_data['ad'],
                defaults={
                    'kisa_aciklama': urun_data['kisa_aciklama'],
                    'aciklama': urun_data['aciklama'],
                    'fiyat': urun_data['fiyat'],
                    'stok': urun_data['stok'],
                    'urun_tipi': urun_data['urun_tipi'],
                    'etiket_kategori': etiket_kategori,
                    'hayvan_turu': urun_data['hayvan_turu'],
                    'kullanim_suresi': urun_data['kullanim_suresi'],
                    'etiket_ozellikler': urun_data['etiket_ozellikler'],
                    'aktif': True
                }
            )
            if created:
                self.stdout.write(f'Etiket Urunu olusturuldu: {urun.ad}')
        
        # 4. Örnek Ürünler - Petshop Ürünleri
        petshop_urunler = [
            {
                'ad': 'Premium Kedi Maması',
                'kisa_aciklama': 'Yüksek proteinli kedi maması',
                'aciklama': 'Yetişkin kediler için özel formülle üretilmiş, yüksek proteinli kedi maması.',
                'fiyat': 45.00,
                'indirimli_fiyat': 38.00,
                'stok': 50,
                'urun_tipi': 'normal',
                'kategori': 'Kedi Mamaları',
                'hayvan_turu': 'Kedi'
            },
            {
                'ad': 'Köpek Oyuncak Topu',
                'kisa_aciklama': 'Dayanıklı köpek oyuncağı',
                'aciklama': 'Köpekler için özel tasarlanmış, dayanıklı oyuncak top.',
                'fiyat': 25.00,
                'stok': 75,
                'urun_tipi': 'normal',
                'kategori': 'Oyuncaklar',
                'hayvan_turu': 'Köpek'
            },
            {
                'ad': 'Kedi Bakım Seti',
                'kisa_aciklama': 'Kapsamlı kedi bakım seti',
                'aciklama': 'Kedi bakımı için gerekli tüm ürünleri içeren kapsamlı set.',
                'fiyat': 85.00,
                'stok': 30,
                'urun_tipi': 'normal',
                'kategori': 'Bakım Ürünleri',
                'hayvan_turu': 'Kedi'
            },
            {
                'ad': 'Köpek Tasması',
                'kisa_aciklama': 'Konforlu köpek tasması',
                'aciklama': 'Köpekler için konforlu ve güvenli tasma.',
                'fiyat': 35.00,
                'stok': 60,
                'urun_tipi': 'normal',
                'kategori': 'Aksesuarlar',
                'hayvan_turu': 'Köpek'
            }
        ]
        
        for urun_data in petshop_urunler:
            kategori = Kategori.objects.get(ad=urun_data['kategori'])
            
            urun, created = Urun.objects.get_or_create(
                ad=urun_data['ad'],
                defaults={
                    'kisa_aciklama': urun_data['kisa_aciklama'],
                    'aciklama': urun_data['aciklama'],
                    'fiyat': urun_data['fiyat'],
                    'indirimli_fiyat': urun_data.get('indirimli_fiyat'),
                    'stok': urun_data['stok'],
                    'urun_tipi': urun_data['urun_tipi'],
                    'kategori': kategori,
                    'hayvan_turu': urun_data['hayvan_turu'],
                    'aktif': True
                }
            )
            if created:
                self.stdout.write(f'Petshop Urunu olusturuldu: {urun.ad}')
        
        self.stdout.write(
            self.style.SUCCESS('Hibrit magaza ornek verileri basariyla olusturuldu!')
        )
        self.stdout.write('Istatistikler:')
        self.stdout.write(f'   - Toplam Urun: {Urun.objects.count()}')
        self.stdout.write(f'   - Etiket Urunleri: {Urun.objects.filter(urun_tipi="etiket").count()}')
        self.stdout.write(f'   - Petshop Urunleri: {Urun.objects.filter(urun_tipi="normal").count()}')
        self.stdout.write(f'   - Kategoriler: {Kategori.objects.count()}')
        self.stdout.write(f'   - Etiket Kategorileri: {EtiketKategori.objects.count()}')
