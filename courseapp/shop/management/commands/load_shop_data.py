from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from shop.models import Kategori, Urun, UrunResim, MagazaKarti, KargoFirma
from etiket.models import EtiketKategori
from decimal import Decimal
import random


class Command(BaseCommand):
    help = 'Mağaza kategorileri, ürünler ve örnek verileri yükler'

    def handle(self, *args, **options):
        # Mevcut verileri temizle
        self.stdout.write(self.style.WARNING('Mevcut mağaza verileri temizleniyor...'))
        
        # Önce ürün resimlerini sil
        UrunResim.objects.all().delete()
        self.stdout.write('   Ürün resimleri silindi')
        
        # Sonra ürünleri sil
        Urun.objects.all().delete()
        self.stdout.write('   Ürünler silindi')
        
        # Kategorileri sil
        Kategori.objects.all().delete()
        self.stdout.write('   Kategoriler silindi')
        
        # Mağaza kartlarını sil
        MagazaKarti.objects.all().delete()
        self.stdout.write('   Mağaza kartları silindi')

        # Kargo firmalarını oluştur
        self.stdout.write(self.style.WARNING('\nKargo firmaları oluşturuluyor...'))
        kargo_firmalari = [
            {'ad': 'Aras Kargo', 'sabit_ucret': Decimal('15.00'), 'tahmini_sure_gun': 2, 'ucretsiz_kargo_limiti': Decimal('100.00')},
            {'ad': 'Yurtiçi Kargo', 'sabit_ucret': Decimal('12.00'), 'tahmini_sure_gun': 3, 'ucretsiz_kargo_limiti': Decimal('150.00')},
            {'ad': 'MNG Kargo', 'sabit_ucret': Decimal('18.00'), 'tahmini_sure_gun': 2, 'ucretsiz_kargo_limiti': Decimal('200.00')},
            {'ad': 'PTT Kargo', 'sabit_ucret': Decimal('10.00'), 'tahmini_sure_gun': 4, 'ucretsiz_kargo_limiti': Decimal('75.00')},
            {'ad': 'Sürat Kargo', 'sabit_ucret': Decimal('14.00'), 'tahmini_sure_gun': 3, 'ucretsiz_kargo_limiti': Decimal('120.00')},
        ]
        
        for kargo_data in kargo_firmalari:
            kargo, created = KargoFirma.objects.get_or_create(
                ad=kargo_data['ad'],
                defaults={
                    'sabit_ucret': kargo_data['sabit_ucret'],
                    'tahmini_sure_gun': kargo_data['tahmini_sure_gun'],
                    'ucretsiz_kargo_limiti': kargo_data['ucretsiz_kargo_limiti'],
                    'aktif': True
                }
            )
            if created:
                self.stdout.write(f'   Kargo firması eklendi: {kargo.ad}')

        # Kategorileri oluştur
        self.stdout.write(self.style.WARNING('\nKategoriler oluşturuluyor...'))
        
        # Ana kategoriler
        ana_kategoriler = [
            {'ad': 'Köpek Ürünleri', 'slug': 'kopek-urunleri', 'icon': 'fas fa-dog', 'sira': 1},
            {'ad': 'Kedi Ürünleri', 'slug': 'kedi-urunleri', 'icon': 'fas fa-cat', 'sira': 2},
            {'ad': 'Kuş Ürünleri', 'slug': 'kus-urunleri', 'icon': 'fas fa-dove', 'sira': 3},
            {'ad': 'Balık Ürünleri', 'slug': 'balik-urunleri', 'icon': 'fas fa-fish', 'sira': 4},
            {'ad': 'Etiket Ürünleri', 'slug': 'etiket-urunleri', 'icon': 'fas fa-qrcode', 'sira': 5},
        ]
        
        kategori_cache = {}
        for kat_data in ana_kategoriler:
            kategori, created = Kategori.objects.get_or_create(
                slug=kat_data['slug'],
                defaults={
                    'ad': kat_data['ad'],
                    'icon': kat_data['icon'],
                    'sira': kat_data['sira'],
                    'aktif': True
                }
            )
            kategori_cache[kat_data['slug']] = kategori
            if created:
                self.stdout.write(f'   Ana kategori eklendi: {kategori.ad}')

        # Alt kategoriler
        alt_kategoriler = [
            # Köpek alt kategorileri
            {'ad': 'Köpek Maması', 'slug': 'kopek-mamasi', 'parent': 'kopek-urunleri', 'sira': 1},
            {'ad': 'Köpek Oyuncakları', 'slug': 'kopek-oyuncaklari', 'parent': 'kopek-urunleri', 'sira': 2},
            {'ad': 'Köpek Aksesuarları', 'slug': 'kopek-aksesuarlari', 'parent': 'kopek-urunleri', 'sira': 3},
            {'ad': 'Köpek Bakım Ürünleri', 'slug': 'kopek-bakim-urunleri', 'parent': 'kopek-urunleri', 'sira': 4},
            {'ad': 'Köpek Taşıma', 'slug': 'kopek-tasima', 'parent': 'kopek-urunleri', 'sira': 5},
            
            # Kedi alt kategorileri
            {'ad': 'Kedi Maması', 'slug': 'kedi-mamasi', 'parent': 'kedi-urunleri', 'sira': 1},
            {'ad': 'Kedi Oyuncakları', 'slug': 'kedi-oyuncaklari', 'parent': 'kedi-urunleri', 'sira': 2},
            {'ad': 'Kedi Aksesuarları', 'slug': 'kedi-aksesuarlari', 'parent': 'kedi-urunleri', 'sira': 3},
            {'ad': 'Kedi Bakım Ürünleri', 'slug': 'kedi-bakim-urunleri', 'parent': 'kedi-urunleri', 'sira': 4},
            {'ad': 'Kedi Kumu', 'slug': 'kedi-kumu', 'parent': 'kedi-urunleri', 'sira': 5},
            
            # Kuş alt kategorileri
            {'ad': 'Kuş Yemi', 'slug': 'kus-yemi', 'parent': 'kus-urunleri', 'sira': 1},
            {'ad': 'Kuş Kafesi', 'slug': 'kus-kafesi', 'parent': 'kus-urunleri', 'sira': 2},
            {'ad': 'Kuş Oyuncakları', 'slug': 'kus-oyuncaklari', 'parent': 'kus-urunleri', 'sira': 3},
            
            # Balık alt kategorileri
            {'ad': 'Balık Yemi', 'slug': 'balik-yemi', 'parent': 'balik-urunleri', 'sira': 1},
            {'ad': 'Akvaryum', 'slug': 'akvaryum', 'parent': 'balik-urunleri', 'sira': 2},
            {'ad': 'Akvaryum Aksesuarları', 'slug': 'akvaryum-aksesuarlari', 'parent': 'balik-urunleri', 'sira': 3},
        ]
        
        for alt_kat_data in alt_kategoriler:
            parent_kategori = kategori_cache[alt_kat_data['parent']]
            kategori, created = Kategori.objects.get_or_create(
                slug=alt_kat_data['slug'],
                defaults={
                    'ad': alt_kat_data['ad'],
                    'parent': parent_kategori,
                    'sira': alt_kat_data['sira'],
                    'aktif': True
                }
            )
            kategori_cache[alt_kat_data['slug']] = kategori
            if created:
                self.stdout.write(f'   Alt kategori eklendi: {kategori.ad}')

        # Etiket kategorilerini oluştur
        self.stdout.write(self.style.WARNING('\nEtiket kategorileri oluşturuluyor...'))
        etiket_kategorileri = [
            {'ad': 'Köpek Künyesi', 'renk': '#FF6B6B', 'aciklama': 'Köpekler için özel tasarlanmış künyeler'},
            {'ad': 'Kedi Künyesi', 'renk': '#4ECDC4', 'aciklama': 'Kediler için özel tasarlanmış künyeler'},
            {'ad': 'Kuş Künyesi', 'renk': '#45B7D1', 'aciklama': 'Kuşlar için özel tasarlanmış künyeler'},
            {'ad': 'Premium Künye', 'renk': '#FFA07A', 'aciklama': 'Premium malzemeden üretilmiş künyeler'},
            {'ad': 'Çocuk Güvenlik Künyesi', 'renk': '#98D8C8', 'aciklama': 'Çocuklar için güvenlik künyeleri'},
        ]
        
        etiket_kategori_cache = {}
        for etiket_kat_data in etiket_kategorileri:
            etiket_kategori, created = EtiketKategori.objects.get_or_create(
                ad=etiket_kat_data['ad'],
                defaults={
                    'renk': etiket_kat_data['renk'],
                    'aciklama': etiket_kat_data['aciklama'],
                    'aktif': True
                }
            )
            etiket_kategori_cache[etiket_kat_data['ad']] = etiket_kategori
            if created:
                self.stdout.write(f'   Etiket kategorisi eklendi: {etiket_kategori.ad}')

        # Örnek ürünler oluştur
        self.stdout.write(self.style.WARNING('\nÖrnek ürünler oluşturuluyor...'))
        
        # Normal ürünler
        normal_urunler = [
            {
                'ad': 'Royal Canin Köpek Maması 15kg',
                'kisa_aciklama': 'Yetişkin köpekler için premium mama',
                'aciklama': 'Royal Canin marka yetişkin köpek maması. Yüksek protein içeriği ile köpeğinizin sağlıklı gelişimini destekler.',
                'fiyat': Decimal('450.00'),
                'indirimli_fiyat': Decimal('380.00'),
                'stok': 25,
                'kategori': 'kopek-mamasi',
                'hayvan_turu': 'Köpek',
                'marka': 'Royal Canin',
                'boyut': '15kg',
                'one_cikan': True,
                'indirimli': True
            },
            {
                'ad': 'Whiskas Kedi Maması 10kg',
                'kisa_aciklama': 'Yetişkin kediler için dengeli beslenme',
                'aciklama': 'Whiskas marka yetişkin kedi maması. Vitamin ve mineral açısından zengin içeriği ile kedinizin sağlığını korur.',
                'fiyat': Decimal('280.00'),
                'stok': 30,
                'kategori': 'kedi-mamasi',
                'hayvan_turu': 'Kedi',
                'marka': 'Whiskas',
                'boyut': '10kg',
                'yeni_urun': True
            },
            {
                'ad': 'Köpek Tasma Seti',
                'kisa_aciklama': 'Deri tasma ve kayış seti',
                'aciklama': 'Kaliteli deri malzemeden üretilmiş köpek tasma ve kayış seti. Ayarlanabilir boyut özelliği.',
                'fiyat': Decimal('85.00'),
                'stok': 15,
                'kategori': 'kopek-aksesuarlari',
                'hayvan_turu': 'Köpek',
                'marka': 'PetSafe',
                'renk': 'Kahverengi',
                'boyut': 'M'
            },
            {
                'ad': 'Kedi Kum Kabı',
                'kisa_aciklama': 'Kapaklı kedi kum kabı',
                'aciklama': 'Kapaklı ve sızdırmaz kedi kum kabı. Kolay temizlenebilir tasarım.',
                'fiyat': Decimal('45.00'),
                'stok': 20,
                'kategori': 'kedi-aksesuarlari',
                'hayvan_turu': 'Kedi',
                'marka': 'Catit',
                'renk': 'Beyaz',
                'boyut': 'L'
            },
            {
                'ad': 'Kuş Kafesi 50cm',
                'kisa_aciklama': 'Orta boy kuş kafesi',
                'aciklama': '50cm boyutunda kuş kafesi. İçinde yemlik ve suluk bulunur.',
                'fiyat': Decimal('120.00'),
                'stok': 8,
                'kategori': 'kus-kafesi',
                'hayvan_turu': 'Kuş',
                'marka': 'BirdCage',
                'boyut': '50x30x40cm'
            },
            {
                'ad': 'Akvaryum 60L',
                'kisa_aciklama': '60 litre akvaryum seti',
                'aciklama': '60 litre kapasiteli akvaryum. Filtre ve ışık sistemi dahil.',
                'fiyat': Decimal('350.00'),
                'stok': 5,
                'kategori': 'akvaryum',
                'hayvan_turu': 'Balık',
                'marka': 'AquaWorld',
                'boyut': '60L'
            }
        ]
        
        # Etiket ürünleri
        etiket_urunler = [
            {
                'ad': 'Köpek Künyesi - QR Kodlu',
                'kisa_aciklama': 'QR kodlu köpek künyesi',
                'aciklama': 'QR kodlu köpek künyesi. Köpeğinizin kaybolması durumunda kolayca bulunmasını sağlar.',
                'fiyat': Decimal('25.00'),
                'petshop_veteriner_fiyat': Decimal('18.00'),
                'petshop_veteriner_fiyat_aktif': True,
                'stok': 100,
                'kategori': 'etiket-urunleri',
                'etiket_kategori': 'Köpek Künyesi',
                'hayvan_turu': 'Köpek',
                'urun_tipi': 'etiket',
                'kullanim_suresi': 365,
                'one_cikan': True
            },
            {
                'ad': 'Kedi Künyesi - QR Kodlu',
                'kisa_aciklama': 'QR kodlu kedi künyesi',
                'aciklama': 'QR kodlu kedi künyesi. Kedinizin güvenliği için tasarlanmış.',
                'fiyat': Decimal('22.00'),
                'petshop_veteriner_fiyat': Decimal('16.00'),
                'petshop_veteriner_fiyat_aktif': True,
                'stok': 80,
                'kategori': 'etiket-urunleri',
                'etiket_kategori': 'Kedi Künyesi',
                'hayvan_turu': 'Kedi',
                'urun_tipi': 'etiket',
                'kullanim_suresi': 365
            },
            {
                'ad': 'Premium Köpek Künyesi',
                'kisa_aciklama': 'Premium malzemeden köpek künyesi',
                'aciklama': 'Paslanmaz çelikten üretilmiş premium köpek künyesi. QR kod özelliği dahil.',
                'fiyat': Decimal('45.00'),
                'petshop_veteriner_fiyat': Decimal('32.00'),
                'petshop_veteriner_fiyat_aktif': True,
                'stok': 50,
                'kategori': 'etiket-urunleri',
                'etiket_kategori': 'Premium Künye',
                'hayvan_turu': 'Köpek',
                'urun_tipi': 'etiket',
                'kullanim_suresi': 730,
                'one_cikan': True
            }
        ]
        
        # Normal ürünleri oluştur
        for urun_data in normal_urunler:
            kategori = kategori_cache[urun_data['kategori']]
            urun, created = Urun.objects.get_or_create(
                ad=urun_data['ad'],
                defaults={
                    'kisa_aciklama': urun_data['kisa_aciklama'],
                    'aciklama': urun_data['aciklama'],
                    'fiyat': urun_data['fiyat'],
                    'indirimli_fiyat': urun_data.get('indirimli_fiyat'),
                    'stok': urun_data['stok'],
                    'hayvan_turu': urun_data['hayvan_turu'],
                    'marka': urun_data.get('marka', ''),
                    'boyut': urun_data.get('boyut', ''),
                    'renk': urun_data.get('renk', ''),
                    'one_cikan': urun_data.get('one_cikan', False),
                    'yeni_urun': urun_data.get('yeni_urun', False),
                    'indirimli': urun_data.get('indirimli', False),
                    'aktif': True
                }
            )
            if created:
                urun.kategoriler.add(kategori)
                self.stdout.write(f'   Normal ürün eklendi: {urun.ad}')

        # Etiket ürünlerini oluştur
        for urun_data in etiket_urunler:
            kategori = kategori_cache[urun_data['kategori']]
            etiket_kategori = etiket_kategori_cache[urun_data['etiket_kategori']]
            
            urun, created = Urun.objects.get_or_create(
                ad=urun_data['ad'],
                defaults={
                    'kisa_aciklama': urun_data['kisa_aciklama'],
                    'aciklama': urun_data['aciklama'],
                    'fiyat': urun_data['fiyat'],
                    'petshop_veteriner_fiyat': urun_data.get('petshop_veteriner_fiyat'),
                    'petshop_veteriner_fiyat_aktif': urun_data.get('petshop_veteriner_fiyat_aktif', False),
                    'stok': urun_data['stok'],
                    'etiket_kategori': etiket_kategori,
                    'hayvan_turu': urun_data['hayvan_turu'],
                    'urun_tipi': urun_data['urun_tipi'],
                    'kullanim_suresi': urun_data['kullanim_suresi'],
                    'one_cikan': urun_data.get('one_cikan', False),
                    'aktif': True
                }
            )
            if created:
                urun.kategoriler.add(kategori)
                self.stdout.write(f'   Etiket ürünü eklendi: {urun.ad}')

        # Mağaza kartları oluştur
        self.stdout.write(self.style.WARNING('\nMağaza kartları oluşturuluyor...'))
        magaza_kartlari = [
            {
                'baslik': 'Köpek Ürünleri',
                'aciklama': 'Köpekleriniz için en kaliteli ürünler',
                'link_url': '/shop/kategori/kopek-urunleri/',
                'buton_metni': 'Köpek Ürünlerini İncele',
                'icon': '🐕',
                'renk': '#FF6B6B',
                'aktif': True
            },
            {
                'baslik': 'Kedi Ürünleri',
                'aciklama': 'Kedileriniz için özel seçilmiş ürünler',
                'link_url': '/shop/kategori/kedi-urunleri/',
                'buton_metni': 'Kedi Ürünlerini İncele',
                'icon': '🐱',
                'renk': '#4ECDC4',
                'aktif': True
            },
            {
                'baslik': 'Etiket Ürünleri',
                'aciklama': 'QR kodlu etiket ve künyeler',
                'link_url': '/shop/kategori/etiket-urunleri/',
                'buton_metni': 'Etiket Ürünlerini İncele',
                'icon': '🏷️',
                'renk': '#45B7D1',
                'aktif': True
            }
        ]
        
        for kart_data in magaza_kartlari:
            kart, created = MagazaKarti.objects.get_or_create(
                baslik=kart_data['baslik'],
                defaults={
                    'aciklama': kart_data['aciklama'],
                    'link_url': kart_data['link_url'],
                    'buton_metni': kart_data['buton_metni'],
                    'icon': kart_data['icon'],
                    'renk': kart_data['renk'],
                    'aktif': kart_data['aktif']
                }
            )
            if created:
                self.stdout.write(f'   Mağaza kartı eklendi: {kart.baslik}')

        # Özet
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('MAĞAZA VERİLERİ BAŞARIYLA YÜKLENDİ!'))
        self.stdout.write('='*60)
        self.stdout.write(f'Kategoriler: {Kategori.objects.count()}')
        self.stdout.write(f'Ürünler: {Urun.objects.count()}')
        self.stdout.write(f'Etiket Kategorileri: {EtiketKategori.objects.count()}')
        self.stdout.write(f'Mağaza Kartları: {MagazaKarti.objects.count()}')
        self.stdout.write(f'Kargo Firmaları: {KargoFirma.objects.count()}')
        self.stdout.write('='*60)

        # Örnek veriler göster
        self.stdout.write('\nÖrnek Kategoriler:')
        for kategori in Kategori.objects.filter(parent__isnull=True)[:3]:
            self.stdout.write(f'   {kategori.ad}:')
            for alt_kategori in kategori.get_children()[:2]:
                self.stdout.write(f'      - {alt_kategori.ad}')

        self.stdout.write('\nÖrnek Ürünler:')
        for urun in Urun.objects.filter(aktif=True)[:5]:
            self.stdout.write(f'   {urun.ad} - {urun.fiyat}₺')
