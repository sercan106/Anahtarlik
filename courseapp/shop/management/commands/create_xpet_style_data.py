# shop/management/commands/create_xpet_style_data.py
from django.core.management.base import BaseCommand
from shop.models import Kategori, Urun, UrunResim
from decimal import Decimal
import random

class Command(BaseCommand):
    help = 'XPET.shop benzeri hiyerarşik kategori ve ürün yapısı oluşturur'

    def handle(self, *args, **options):
        self.stdout.write('Mevcut urunleri ve kategorileri temizliyorum...')
        
        # Mevcut urunleri sil
        Urun.objects.filter(urun_tipi='normal').delete()
        
        # Mevcut kategorileri sil
        Kategori.objects.all().delete()
        
        self.stdout.write('Kategori yapisini olusturuyorum...')
        
        # Ana kategorileri oluştur
        kopek = Kategori.objects.create(
            ad='KÖPEK',
            slug='kopek',
            sira=1,
            icon='🐕',
            aciklama='Köpek ürünleri ve aksesuarları'
        )
        
        kedi = Kategori.objects.create(
            ad='KEDİ',
            slug='kedi',
            sira=2,
            icon='🐱',
            aciklama='Kedi ürünleri ve aksesuarları'
        )
        
        kus = Kategori.objects.create(
            ad='KUŞ',
            slug='kus',
            sira=3,
            icon='🦜',
            aciklama='Kuş ürünleri ve aksesuarları'
        )
        
        kemirgen = Kategori.objects.create(
            ad='KEMİRGEN',
            slug='kemirgen',
            sira=4,
            icon='🐹',
            aciklama='Kemirgen ürünleri ve aksesuarları'
        )
        
        akvaryum = Kategori.objects.create(
            ad='AKVARYUM',
            slug='akvaryum',
            sira=5,
            icon='🐠',
            aciklama='Akvaryum ve balık ürünleri'
        )
        
        surungen = Kategori.objects.create(
            ad='SÜRÜNGEN',
            slug='surungen',
            sira=6,
            icon='🦎',
            aciklama='Sürüngen ürünleri ve aksesuarları'
        )
        
        # Köpek alt kategorileri
        kopek_alt_kategoriler = [
            ('Köpek Kuru Mama', 'kopek-kuru-mama', '🥘'),
            ('Köpek Konserveleri', 'kopek-konservesi', '🥫'),
            ('Besin Takviyeleri', 'kopek-takviye', '💊'),
            ('Köpek Ödülleri', 'kopek-odulleri', '🎾'),
            ('Tasmalar', 'kopek-tasmalari', '🔗'),
            ('Köpek Yatakları', 'kopek-yataklari', '🛏️'),
            ('Oyuncaklar', 'kopek-oyuncaklari', '🪀'),
            ('Mama Kapları', 'kopek-mama-kaplari', '🍽️'),
            ('Bakım Ürünleri', 'kopek-bakim', '🧴'),
            ('Köpek Aksesuarları', 'kopek-aksesuarlari', '🎀'),
        ]
        
        for ad, slug, icon in kopek_alt_kategoriler:
            Kategori.objects.create(
                ad=ad,
                slug=slug,
                parent=kopek,
                icon=icon,
                sira=len(Kategori.objects.filter(parent=kopek)) + 1
            )
        
        # Kedi alt kategorileri
        kedi_alt_kategoriler = [
            ('Kedi Kuru Mama', 'kedi-kuru-mama', '🥘'),
            ('Kedi Konservesi', 'kedi-konservesi', '🥫'),
            ('Kedi Ödülleri', 'kedi-odulleri', '🎾'),
            ('Kedi Kumları', 'kedi-kumlari', '🚿'),
            ('Oyuncaklar', 'kedi-oyuncaklari', '🪀'),
            ('Tasmalar', 'kedi-tasmalari', '🔗'),
            ('Kedi Evi', 'kedi-evi', '🏠'),
            ('Yataklar', 'kedi-yataklari', '🛏️'),
            ('Bakım Ürünleri', 'kedi-bakim', '🧴'),
            ('Kedi Aksesuarları', 'kedi-aksesuarlari', '🎀'),
        ]
        
        for ad, slug, icon in kedi_alt_kategoriler:
            Kategori.objects.create(
                ad=ad,
                slug=slug,
                parent=kedi,
                icon=icon,
                sira=len(Kategori.objects.filter(parent=kedi)) + 1
            )
        
        # Kuş alt kategorileri
        kus_alt_kategoriler = [
            ('Kuş Yemi', 'kus-yemi', '🌾'),
            ('Kafes ve Oyuncaklar', 'kus-kafes', '🪺'),
            ('Kuş Aksesuarları', 'kus-aksesuarlari', '🎀'),
            ('Sağlık Ürünleri', 'kus-saglik', '💊'),
        ]
        
        for ad, slug, icon in kus_alt_kategoriler:
            Kategori.objects.create(
                ad=ad,
                slug=slug,
                parent=kus,
                icon=icon,
                sira=len(Kategori.objects.filter(parent=kus)) + 1
            )
        
        self.stdout.write('Kategoriler olusturuldu')
        
        # Urun ornekleri
        urun_ornekleri = [
            # Köpek Mamaları
            ('Royal Canin Köpek Maması 15kg', 'Yavru köpekler için özel formül', Decimal('1250.00'), None, 'kopek-kuru-mama'),
            ('Pedigree Adult Köpek Maması 14kg', 'Yetişkin köpekler için dengeli beslenme', Decimal('850.00'), Decimal('750.00'), 'kopek-kuru-mama'),
            ('Acana Puppy Köpek Maması 13kg', 'Yavru köpekler için tahılsız mama', Decimal('1800.00'), None, 'kopek-kuru-mama'),
            ('Hill\'s Science Plan Köpek Maması 12kg', 'Beslenme uzmanları tarafından önerilir', Decimal('1400.00'), Decimal('1200.00'), 'kopek-kuru-mama'),
            ('Pro Plan Köpek Maması 14kg', 'Porsiyon kontrolü için ideal', Decimal('1050.00'), None, 'kopek-kuru-mama'),
            
            # Köpek Konserveleri
            ('Goody Tavuklu Köpek Konservesi 400g', 'Doğal içerikli konserve', Decimal('45.00'), None, 'kopek-konservesi'),
            ('Royal Canin Köpek Konservesi 140g', 'Hassas mideler için', Decimal('28.00'), None, 'kopek-konservesi'),
            ('Animonda Etli Köpek Konservesi 150g', 'Premium et içeriği', Decimal('35.00'), Decimal('30.00'), 'kopek-konservesi'),
            
            # Köpek Ödülleri
            ('Pedigree DentaStix Köpek Ödülü', 'Diş temizliği için', Decimal('120.00'), None, 'kopek-odulleri'),
            ('Whiskas Köpek Ödül Çubukları', 'Lezzetli ödül', Decimal('65.00'), None, 'kopek-odulleri'),
            ('Happy Dog Köpek Ödül Maması', 'Eğitim için idealdir', Decimal('95.00'), Decimal('85.00'), 'kopek-odulleri'),
            
            # Tasmalar
            ('Flexi Köpek Tasması Küçük Boy', 'Güvenli tasma sistemi', Decimal('280.00'), None, 'kopek-tasmalari'),
            ('RedDingo Köpek Tasması Orta Boy', 'Deri tasma', Decimal('145.00'), None, 'kopek-tasmalari'),
            ('Pet Tag Art Köpek Tasması', 'Kişiselleştirilebilir', Decimal('95.00'), Decimal('75.00'), 'kopek-tasmalari'),
            
            # Köpek Yatakları
            ('Doggy Köpek Yatağı Büyük', 'Yumuşak ve konforlu', Decimal('450.00'), None, 'kopek-yataklari'),
            ('Pet Comfort Köpek Yatağı Orta', 'Anti-bakteriyel', Decimal('280.00'), Decimal('250.00'), 'kopek-yataklari'),
            
            # Oyuncaklar
            ('Kong Köpek Oyuncağı Klasik', 'Dayanıklı oyuncak', Decimal('120.00'), None, 'kopek-oyuncaklari'),
            ('GimDog Köpek Oyuncağı', 'Çekmeli oyuncak', Decimal('85.00'), None, 'kopek-oyuncaklari'),
            ('PetFriendly Top Oyuncağı', 'Renkli toplar seti', Decimal('65.00'), Decimal('55.00'), 'kopek-oyuncaklari'),
            
            # Kedi Mamaları
            ('Whiskas Kedi Maması 10kg', 'Yetişkin kediler için', Decimal('850.00'), None, 'kedi-kuru-mama'),
            ('Royal Canin Kedi Maması 10kg', 'Beslenme uzmanları tarafından önerilir', Decimal('1200.00'), Decimal('1100.00'), 'kedi-kuru-mama'),
            ('Pro Plan Kedi Maması 10kg', 'Hassas deri için', Decimal('950.00'), None, 'kedi-kuru-mama'),
            ('Hill\'s Science Plan Kedi Maması', 'Yaşlı kediler için', Decimal('1150.00'), None, 'kedi-kuru-mama'),
            
            # Kedi Konserveleri
            ('Felix Kedi Konservesi 400g', 'Tavuklu', Decimal('42.00'), None, 'kedi-konservesi'),
            ('Sheba Kedi Konservesi', 'Premium konserve', Decimal('38.00'), Decimal('35.00'), 'kedi-konservesi'),
            ('Gourmet Kedi Konservesi', 'Lezzetli çeşitler', Decimal('36.00'), None, 'kedi-konservesi'),
            
            # Kedi Kumları
            ('Ever Clean Kedi Kumu 10L', 'Topaklaşan kum', Decimal('180.00'), None, 'kedi-kumlari'),
            ('Cat\'s Best Kedi Kumu', 'Doğal kum', Decimal('220.00'), Decimal('200.00'), 'kedi-kumlari'),
            ('Silica Kristal Kedi Kumu', 'Hidrasyon için', Decimal('95.00'), None, 'kedi-kumlari'),
            
            # Kedi Oyuncakları
            ('Catnip Kedi Oyuncağı', 'Kediotu oyuncağı', Decimal('45.00'), None, 'kedi-oyuncaklari'),
            ('Tüy Topu Kedi Oyuncağı', 'Avlanma içgüdüsü', Decimal('25.00'), None, 'kedi-oyuncaklari'),
            ('Lazer Pointer Kedi Oyuncağı', 'Etkileşimli oyun', Decimal('85.00'), Decimal('75.00'), 'kedi-oyuncaklari'),
            
            # Kedi Aksesuarları
            ('Kedi Tırmanma Kulesi', 'Tırmalama için', Decimal('850.00'), None, 'kedi-aksesuarlari'),
            ('Kedi Taşıma Çantası', 'Gezi için', Decimal('195.00'), None, 'kedi-aksesuarlari'),
            ('Kedi Künyesi', 'Kaybolmaya karşı', Decimal('65.00'), Decimal('55.00'), 'kedi-aksesuarlari'),
            
            # Kuş Yemleri
            ('Kanarya Yemi 1kg', 'Karışık tohum', Decimal('45.00'), None, 'kus-yemi'),
            ('Muhabbet Kuşu Yemi 1kg', 'Vitamin takviyeli', Decimal('42.00'), None, 'kus-yemi'),
            ('Papağan Yemi 2kg', 'Çekirdek karışımı', Decimal('125.00'), Decimal('110.00'), 'kus-yemi'),
            
            # Kuş Kafesleri
            ('Metal Kuş Kafesi Büyük', 'Geniş konfor', Decimal('450.00'), None, 'kus-kafes'),
            ('Papağan Kafesi Oyun Bahçeli', 'Oyun alanlı', Decimal('850.00'), Decimal('750.00'), 'kus-kafes'),
            
            # Bakım Ürünleri
            ('Köpek Şampuanı 250ml', 'Tüy ve deri bakımı', Decimal('85.00'), None, 'kopek-bakim'),
            ('Kedi Şampuanı Hipojenik', 'Alerji dostu', Decimal('95.00'), None, 'kedi-bakim'),
            ('Diş Temizleme Jeli', 'Ağız bakımı', Decimal('65.00'), Decimal('55.00'), 'kopek-bakim'),
            
            # Mama Kapları
            ('Paslanmaz Çelik Mama Kabı', 'Dayanıklı', Decimal('75.00'), None, 'kopek-mama-kaplari'),
            ('Otomatik Su Fıskiyesi', 'Temiz su', Decimal('180.00'), None, 'kopek-mama-kaplari'),
            ('Yükseltilmiş Mama Kabı', 'Boyun desteği', Decimal('95.00'), Decimal('85.00'), 'kopek-mama-kaplari'),
        ]
        
        self.stdout.write('Urunleri olusturuyorum...')
        
        kategori_map = {}
        for kategori in Kategori.objects.all():
            kategori_map[kategori.slug] = kategori
        
        urunler_created = 0
        
        for ad, aciklama, fiyat, indirimli_fiyat, kategori_slug in urun_ornekleri:
            if kategori_slug in kategori_map:
                kategori_obj = kategori_map[kategori_slug]
                
                urun = Urun.objects.create(
                    ad=ad,
                    kisa_aciklama=aciklama[:200],
                    aciklama=f'{aciklama}\n\nYüksek kaliteli ürün. Tüm evcil hayvanlarınız için güvenli ve sağlıklı.',
                    fiyat=fiyat,
                    indirimli_fiyat=indirimli_fiyat,
                    stok=random.randint(5, 50),
                    urun_tipi='normal',
                    marka='PetSafe Hub',
                    hayvan_turu=kategori_obj.parent.ad if kategori_obj.parent else kategori_obj.ad,
                    yeni_urun=random.choice([True, False]),
                    indirimli=indirimli_fiyat is not None,
                    one_cikan=random.choice([True, False]),
                    aktif=True
                )
                
                # Kategoriye ekle
                urun.kategoriler.add(kategori_obj)
                
                # Ana kategoriye de ekle
                if kategori_obj.parent:
                    urun.kategoriler.add(kategori_obj.parent)
                
                urunler_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'{urunler_created} urun basariyla olusturuldu!'))
        self.stdout.write(self.style.SUCCESS('XPET.shop benzeri magaza hazir!'))

