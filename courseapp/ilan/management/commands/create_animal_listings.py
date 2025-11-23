# ilan/management/commands/create_animal_listings.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from ilan.models import HayvanProfili, Ilan, HayvanResmi
from anahtarlik.dictionaries import Tur, Irk, Il, Ilce, Mahalle
import random

class Command(BaseCommand):
    help = '20 adet hayvan ilanı oluşturur (kedi, köpek, tavşan, vb.)'

    def handle(self, *args, **options):
        # Test kullanıcısı oluştur veya al
        test_user, created = User.objects.get_or_create(
            username='test_user',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        if created:
            test_user.set_password('test123')
            test_user.save()
            self.stdout.write(
                self.style.SUCCESS('Test kullanıcısı oluşturuldu: test_user / test123')
            )

        # Tür ve ırk verilerini al
        try:
            kedi_tur = Tur.objects.get(ad='Kedi')
            kopek_tur = Tur.objects.get(ad='Köpek')
            tavsan_tur = Tur.objects.get(ad='Tavşan')
            kus_tur = Tur.objects.get(ad='Kuş')
            balik_tur = Tur.objects.get(ad='Balık')
        except Tur.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Tür verileri bulunamadı! Önce anahtarlik verilerini yükleyin.')
            )
            return

        # İl ve ilçe verilerini al
        try:
            istanbul = Il.objects.get(ad='İstanbul')
            ankara = Il.objects.get(ad='Ankara')
            izmir = Il.objects.get(ad='İzmir')
            
            # İlçeler
            istanbul_ilceler = list(Ilce.objects.filter(il=istanbul)[:5])
            ankara_ilceler = list(Ilce.objects.filter(il=ankara)[:3])
            izmir_ilceler = list(Ilce.objects.filter(il=izmir)[:3])
        except Il.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('İl verileri bulunamadı! Önce il-ilçe verilerini yükleyin.')
            )
            return

        # Hayvan verileri
        hayvan_verileri = [
            # Kedi ilanları
            {
                'hayvan_adi': 'Mırmır',
                'tur': kedi_tur,
                'irk_adi': 'British Shorthair',
                'yas': '2 yaş',
                'cinsiyet': 'ERKEK',
                'asi_durumu': True,
                'ic_parazit': True,
                'dis_parazit': True,
                'sehir_disi_gonderim': True,
                'il': istanbul,
                'ilce_listesi': istanbul_ilceler,
                'aciklama': 'Çok sevimli ve oyuncu bir kedi. Aşıları tam, sağlıklı ve ev ortamına uyumlu.',
                'ilan_turu': 'SAHIPLENDIRME',
                'baslik': 'Sevimli Kedi Sahiplendirme',
                'fiyat': None,
                'onemli_mi': True
            },
            {
                'hayvan_adi': 'Pamuk',
                'tur': kedi_tur,
                'irk_adi': 'Van Kedisi',
                'yas': '1 yaş',
                'cinsiyet': 'DISI',
                'asi_durumu': True,
                'ic_parazit': True,
                'dis_parazit': True,
                'sehir_disi_gonderim': False,
                'il': ankara,
                'ilce_listesi': ankara_ilceler,
                'aciklama': 'Beyaz tüylü, çok temiz ve bakımlı kedi. Çocuklarla iyi anlaşır.',
                'ilan_turu': 'SAHIPLENDIRME',
                'baslik': 'Beyaz Van Kedisi Sahiplendirme',
                'fiyat': None,
                'onemli_mi': False
            },
            {
                'hayvan_adi': 'Sarman',
                'tur': kedi_tur,
                'irk_adi': 'Tekir',
                'yas': '6 aylık',
                'cinsiyet': 'ERKEK',
                'asi_durumu': False,
                'ic_parazit': False,
                'dis_parazit': False,
                'sehir_disi_gonderim': True,
                'il': izmir,
                'ilce_listesi': izmir_ilceler,
                'aciklama': 'Genç ve enerjik yavru kedi. Aşıları yapılacak, çok sevimli.',
                'ilan_turu': 'SAHIPLENDIRME',
                'baslik': 'Yavru Tekir Kedi Sahiplendirme',
                'fiyat': None,
                'onemli_mi': True
            },
            {
                'hayvan_adi': 'Luna',
                'tur': kedi_tur,
                'irk_adi': 'Persian',
                'yas': '3 yaş',
                'cinsiyet': 'DISI',
                'asi_durumu': True,
                'ic_parazit': True,
                'dis_parazit': True,
                'sehir_disi_gonderim': True,
                'il': istanbul,
                'ilce_listesi': istanbul_ilceler,
                'aciklama': 'Safkan Persian kedisi. Çok sakin ve uyumlu. Özel bakım gerektirir.',
                'ilan_turu': 'SATIS',
                'baslik': 'Safkan Persian Kedisi Satılık',
                'fiyat': 2500.00,
                'onemli_mi': True
            },
            # Köpek ilanları
            {
                'hayvan_adi': 'Max',
                'tur': kopek_tur,
                'irk_adi': 'Golden Retriever',
                'yas': '2 yaş',
                'cinsiyet': 'ERKEK',
                'asi_durumu': True,
                'ic_parazit': True,
                'dis_parazit': True,
                'sehir_disi_gonderim': True,
                'il': istanbul,
                'ilce_listesi': istanbul_ilceler,
                'aciklama': 'Çok sevimli ve eğitimli Golden Retriever. Çocuklarla mükemmel anlaşır.',
                'ilan_turu': 'SAHIPLENDIRME',
                'baslik': 'Eğitimli Golden Retriever Sahiplendirme',
                'fiyat': None,
                'onemli_mi': True
            },
            {
                'hayvan_adi': 'Bella',
                'tur': kopek_tur,
                'irk_adi': 'Labrador',
                'yas': '1 yaş',
                'cinsiyet': 'DISI',
                'asi_durumu': True,
                'ic_parazit': True,
                'dis_parazit': True,
                'sehir_disi_gonderim': False,
                'il': ankara,
                'ilce_listesi': ankara_ilceler,
                'aciklama': 'Genç ve enerjik Labrador. Çok oyuncu ve sevimli.',
                'ilan_turu': 'SAHIPLENDIRME',
                'baslik': 'Genç Labrador Sahiplendirme',
                'fiyat': None,
                'onemli_mi': False
            },
            {
                'hayvan_adi': 'Rocky',
                'tur': kopek_tur,
                'irk_adi': 'Alman Kurdu',
                'yas': '3 yaş',
                'cinsiyet': 'ERKEK',
                'asi_durumu': True,
                'ic_parazit': True,
                'dis_parazit': True,
                'sehir_disi_gonderim': True,
                'il': izmir,
                'ilce_listesi': izmir_ilceler,
                'aciklama': 'Eğitimli ve sadık Alman Kurdu. Koruma köpeği olarak ideal.',
                'ilan_turu': 'SATIS',
                'baslik': 'Eğitimli Alman Kurdu Satılık',
                'fiyat': 3500.00,
                'onemli_mi': True
            },
            {
                'hayvan_adi': 'Mia',
                'tur': kopek_tur,
                'irk_adi': 'Chihuahua',
                'yas': '4 aylık',
                'cinsiyet': 'DISI',
                'asi_durumu': False,
                'ic_parazit': False,
                'dis_parazit': False,
                'sehir_disi_gonderim': True,
                'il': istanbul,
                'ilce_listesi': istanbul_ilceler,
                'aciklama': 'Minik ve sevimli Chihuahua yavrusu. Çok küçük ve şirin.',
                'ilan_turu': 'SAHIPLENDIRME',
                'baslik': 'Minik Chihuahua Yavrusu Sahiplendirme',
                'fiyat': None,
                'onemli_mi': True
            },
            # Tavşan ilanları
            {
                'hayvan_adi': 'Havuç',
                'tur': tavsan_tur,
                'irk_adi': 'Hollanda Cüce Tavşanı',
                'yas': '8 aylık',
                'cinsiyet': 'ERKEK',
                'asi_durumu': False,
                'ic_parazit': False,
                'dis_parazit': False,
                'sehir_disi_gonderim': True,
                'il': ankara,
                'ilce_listesi': ankara_ilceler,
                'aciklama': 'Çok sevimli cüce tavşan. Çocuklar için ideal.',
                'ilan_turu': 'SAHIPLENDIRME',
                'baslik': 'Sevimli Cüce Tavşan Sahiplendirme',
                'fiyat': None,
                'onemli_mi': False
            },
            {
                'hayvan_adi': 'Beyaz',
                'tur': tavsan_tur,
                'irk_adi': 'Angora Tavşanı',
                'yas': '1 yaş',
                'cinsiyet': 'DISI',
                'asi_durumu': False,
                'ic_parazit': False,
                'dis_parazit': False,
                'sehir_disi_gonderim': False,
                'il': izmir,
                'ilce_listesi': izmir_ilceler,
                'aciklama': 'Uzun tüylü Angora tavşanı. Çok yumuşak ve sevimli.',
                'ilan_turu': 'SAHIPLENDIRME',
                'baslik': 'Uzun Tüylü Angora Tavşanı Sahiplendirme',
                'fiyat': None,
                'onemli_mi': False
            },
            # Kuş ilanları
            {
                'hayvan_adi': 'Papağan',
                'tur': kus_tur,
                'irk_adi': 'Sultan Papağanı',
                'yas': '2 yaş',
                'cinsiyet': 'ERKEK',
                'asi_durumu': False,
                'ic_parazit': False,
                'dis_parazit': False,
                'sehir_disi_gonderim': True,
                'il': istanbul,
                'ilce_listesi': istanbul_ilceler,
                'aciklama': 'Konuşkan ve sevimli sultan papağanı. Çok zeki.',
                'ilan_turu': 'SATIS',
                'baslik': 'Konuşkan Sultan Papağanı Satılık',
                'fiyat': 800.00,
                'onemli_mi': False
            },
            {
                'hayvan_adi': 'Kanarya',
                'tur': kus_tur,
                'irk_adi': 'Sarı Kanarya',
                'yas': '1 yaş',
                'cinsiyet': 'ERKEK',
                'asi_durumu': False,
                'ic_parazit': False,
                'dis_parazit': False,
                'sehir_disi_gonderim': True,
                'il': ankara,
                'ilce_listesi': ankara_ilceler,
                'aciklama': 'Güzel öten sarı kanarya. Çok melodik sesi var.',
                'ilan_turu': 'SAHIPLENDIRME',
                'baslik': 'Güzel Öten Kanarya Sahiplendirme',
                'fiyat': None,
                'onemli_mi': False
            },
            # Balık ilanları
            {
                'hayvan_adi': 'Akvaryum Balıkları',
                'tur': balik_tur,
                'irk_adi': 'Japon Balığı',
                'yas': '6 aylık',
                'cinsiyet': 'BILINMIYOR',
                'asi_durumu': False,
                'ic_parazit': False,
                'dis_parazit': False,
                'sehir_disi_gonderim': False,
                'il': izmir,
                'ilce_listesi': izmir_ilceler,
                'aciklama': 'Renkli ve sağlıklı japon balıkları. Akvaryum ile birlikte.',
                'ilan_turu': 'SAHIPLENDIRME',
                'baslik': 'Japon Balıkları ve Akvaryum Sahiplendirme',
                'fiyat': None,
                'onemli_mi': False
            },
            # Daha fazla kedi
            {
                'hayvan_adi': 'Simba',
                'tur': kedi_tur,
                'irk_adi': 'Maine Coon',
                'yas': '4 yaş',
                'cinsiyet': 'ERKEK',
                'asi_durumu': True,
                'ic_parazit': True,
                'dis_parazit': True,
                'sehir_disi_gonderim': True,
                'il': istanbul,
                'ilce_listesi': istanbul_ilceler,
                'aciklama': 'Büyük ve güçlü Maine Coon kedisi. Çok sakin ve sevimli.',
                'ilan_turu': 'SATIS',
                'baslik': 'Büyük Maine Coon Kedisi Satılık',
                'fiyat': 3000.00,
                'onemli_mi': True
            },
            {
                'hayvan_adi': 'Nala',
                'tur': kedi_tur,
                'irk_adi': 'Siam Kedisi',
                'yas': '2 yaş',
                'cinsiyet': 'DISI',
                'asi_durumu': True,
                'ic_parazit': True,
                'dis_parazit': True,
                'sehir_disi_gonderim': True,
                'il': ankara,
                'ilce_listesi': ankara_ilceler,
                'aciklama': 'Zeki ve konuşkan Siam kedisi. Çok aktif ve oyuncu.',
                'ilan_turu': 'SAHIPLENDIRME',
                'baslik': 'Zeki Siam Kedisi Sahiplendirme',
                'fiyat': None,
                'onemli_mi': False
            },
            # Daha fazla köpek
            {
                'hayvan_adi': 'Buddy',
                'tur': kopek_tur,
                'irk_adi': 'Beagle',
                'yas': '3 yaş',
                'cinsiyet': 'ERKEK',
                'asi_durumu': True,
                'ic_parazit': True,
                'dis_parazit': True,
                'sehir_disi_gonderim': True,
                'il': izmir,
                'ilce_listesi': izmir_ilceler,
                'aciklama': 'Eğitimli ve sadık Beagle. Çok sevimli ve oyuncu.',
                'ilan_turu': 'SAHIPLENDIRME',
                'baslik': 'Eğitimli Beagle Sahiplendirme',
                'fiyat': None,
                'onemli_mi': True
            },
            {
                'hayvan_adi': 'Luna',
                'tur': kopek_tur,
                'irk_adi': 'Husky',
                'yas': '2 yaş',
                'cinsiyet': 'DISI',
                'asi_durumu': True,
                'ic_parazit': True,
                'dis_parazit': True,
                'sehir_disi_gonderim': True,
                'il': istanbul,
                'ilce_listesi': istanbul_ilceler,
                'aciklama': 'Güzel mavi gözlü Husky. Çok enerjik ve sevimli.',
                'ilan_turu': 'SATIS',
                'baslik': 'Mavi Gözlü Husky Satılık',
                'fiyat': 4000.00,
                'onemli_mi': True
            },
            # Daha fazla tavşan
            {
                'hayvan_adi': 'Kahve',
                'tur': tavsan_tur,
                'irk_adi': 'Rex Tavşanı',
                'yas': '1 yaş',
                'cinsiyet': 'ERKEK',
                'asi_durumu': False,
                'ic_parazit': False,
                'dis_parazit': False,
                'sehir_disi_gonderim': True,
                'il': ankara,
                'ilce_listesi': ankara_ilceler,
                'aciklama': 'Yumuşak tüylü Rex tavşanı. Çok sakin ve sevimli.',
                'ilan_turu': 'SAHIPLENDIRME',
                'baslik': 'Yumuşak Tüylü Rex Tavşanı Sahiplendirme',
                'fiyat': None,
                'onemli_mi': False
            },
            # Daha fazla kuş
            {
                'hayvan_adi': 'Muhabbet',
                'tur': kus_tur,
                'irk_adi': 'Muhabbet Kuşu',
                'yas': '1 yaş',
                'cinsiyet': 'DISI',
                'asi_durumu': False,
                'ic_parazit': False,
                'dis_parazit': False,
                'sehir_disi_gonderim': True,
                'il': izmir,
                'ilce_listesi': izmir_ilceler,
                'aciklama': 'Renkli ve sevimli muhabbet kuşu. Çok oyuncu.',
                'ilan_turu': 'SAHIPLENDIRME',
                'baslik': 'Renkli Muhabbet Kuşu Sahiplendirme',
                'fiyat': None,
                'onemli_mi': False
            },
            # Son kedi
            {
                'hayvan_adi': 'Miyav',
                'tur': kedi_tur,
                'irk_adi': 'Scottish Fold',
                'yas': '3 yaş',
                'cinsiyet': 'DISI',
                'asi_durumu': True,
                'ic_parazit': True,
                'dis_parazit': True,
                'sehir_disi_gonderim': True,
                'il': istanbul,
                'ilce_listesi': istanbul_ilceler,
                'aciklama': 'Kıvrık kulaklı Scottish Fold kedisi. Çok sakin ve sevimli.',
                'ilan_turu': 'SATIS',
                'baslik': 'Kıvrık Kulaklı Scottish Fold Satılık',
                'fiyat': 2200.00,
                'onemli_mi': True
            }
        ]

        # Hayvan profilleri ve ilanları oluştur
        for i, hayvan_data in enumerate(hayvan_verileri):
            # Irk oluştur veya al
            irk, created = Irk.objects.get_or_create(
                ad=hayvan_data['irk_adi'],
                tur=hayvan_data['tur']
            )
            
            # İlçe seç
            ilce = random.choice(hayvan_data['ilce_listesi'])
            
            # Hayvan profili oluştur
            hayvan_profili = HayvanProfili.objects.create(
                kullanici=test_user,
                hayvan_adi=hayvan_data['hayvan_adi'],
                tur=hayvan_data['tur'],
                irk=irk,
                yas=hayvan_data['yas'],
                cinsiyet=hayvan_data['cinsiyet'],
                asi_durumu=hayvan_data['asi_durumu'],
                ic_parazit=hayvan_data['ic_parazit'],
                dis_parazit=hayvan_data['dis_parazit'],
                sehir_disi_gonderim=hayvan_data['sehir_disi_gonderim'],
                il=hayvan_data['il'],
                ilce=ilce,
                aciklama=hayvan_data['aciklama'],
                aktif=True
            )
            
            # İlan oluştur
            ilan = Ilan.objects.create(
                hayvan_profili=hayvan_profili,
                baslik=hayvan_data['baslik'],
                ilan_turu=hayvan_data['ilan_turu'],
                aciklama=hayvan_data['aciklama'],
                fiyat=hayvan_data['fiyat'],
                onemli_mi=hayvan_data['onemli_mi'],
                aktif=True,
                onaylandi=True,
                bitis_tarihi=timezone.now() + timedelta(days=30)
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'[OK] {i+1}/20 - {hayvan_data["hayvan_adi"]} ({hayvan_data["tur"].ad}) ilanı oluşturuldu!')
            )

        self.stdout.write(
            self.style.SUCCESS('\n[BASARILI] 20 adet hayvan ilanı başarıyla oluşturuldu!')
        )
        self.stdout.write(
            self.style.SUCCESS('Test kullanıcısı: test_user / test123')
        )
