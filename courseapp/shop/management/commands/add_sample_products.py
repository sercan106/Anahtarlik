from django.core.management.base import BaseCommand
from shop.models import Kategori, Urun
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Mağazaya örnek ürünler ekler'

    def handle(self, *args, **options):
        # Kategorileri oluştur
        kategoriler = {
            'etiket': Kategori.objects.get_or_create(
                slug='qr-etiket',
                defaults={'ad': 'QR Etiket'}
            )[0],
            'abonelik': Kategori.objects.get_or_create(
                slug='abonelik-paketleri',
                defaults={'ad': 'Abonelik Paketleri'}
            )[0],
            'hizmet': Kategori.objects.get_or_create(
                slug='veteriner-hizmetleri',
                defaults={'ad': 'Veteriner Hizmetleri'}
            )[0],
        }

        # Ürünleri oluştur
        urunler = [
            {
                'ad': 'Premium QR Pet Etiket',
                'kisa_aciklama': 'Kayıp evcil hayvanınız kolayca bulunur',
                'aciklama': '''🐾 Premium QR Pet Etiket ile Evcil Dostlarınızı Koruyun!

✅ Özellikler:
• Dayanıklı, su geçirmez malzeme
• Kolay tarama ile anında bildirim
• GPS lokasyon paylaşımı
• Otomatik e-posta bildirimi
• Hayvan profili ve tıbbi bilgiler
• 7/24 online erişim

📱 Nasıl Çalışır:
1. QR kodu evcil dostunuzun tasmasına takın
2. Kayıp durumunda bulan kişi QR'ı tarar
3. Siz anında bildirim alırsınız
4. Konum bilgisi paylaşılır

🎯 Paket İçeriği:
• 1 adet Premium QR Etiket
• Online profil oluşturma
• Sınırsız bilgi güncelleme
• Müşteri desteği

💝 Sevdiklerinizin güvenliği için şimdi sipariş verin!''',
                'fiyat': '299.99',
                'indirimli_fiyat': '249.99',
                'stok': 150,
                'kategori': kategoriler['etiket'],
                'tavsiye_edilen_tur': 'Tümü'
            },
            {
                'ad': 'Yıllık Premium Abonelik',
                'kisa_aciklama': 'Gelişmiş özellikler ve sınırsız erişim',
                'aciklama': '''⭐ Yıllık Premium Abonelik - Tam Kontrol Sizde!

🎁 Premium Avantajlar:
• Sınırsız sayıda evcil hayvan kaydı
• Öncelikli müşteri desteği
• Gelişmiş bildirim sistemi
• Özel veteriner danışmanlığı
• Tarama geçmişi raporları
• Sağlık takip sistemi
• Aşı ve randevu hatırlatıcıları

📊 İstatistikler ve Raporlar:
• QR tarama analizleri
• Aktivite grafikleri
• Sağlık kayıtları
• Veteriner ziyaret geçmişi

🔒 Güvenlik:
• Verileriniz şifreli saklanır
• 7/24 online yedekleme
• KVKK uyumlu

💼 İşletmeler İçin:
• Çoklu kullanıcı desteği
• Toplu işlemler
• API erişimi
• Özel eğitim

🎯 12 aylık kesintisiz hizmet!
💰 %30 indirimli fiyat ile şimdi satın alın!''',
                'fiyat': '999.99',
                'indirimli_fiyat': '699.99',
                'stok': 9999,
                'kategori': kategoriler['abonelik'],
                'tavsiye_edilen_tur': 'Tümü'
            },
            {
                'ad': 'Online Veteriner Danışmanlık Paketi',
                'kisa_aciklama': 'Uzman veterinerlerle 24/7 iletişim',
                'aciklama': '''👨‍⚕️ Online Veteriner Danışmanlık - Uzmanlar Her Zaman Yanınızda!

🏥 Paket İçeriği:
• 3 aylık online danışmanlık
• 10 adet görüntülü görüşme hakkı
• Sınırsız mesajlaşma
• Acil durum danışmanlığı
• Reçete ve teşhis desteği
• Beslenme planı oluşturma

📱 Kullanım Kolaylığı:
• Mobil uygulama desteği
• Video konferans sistemi
• Doküman paylaşımı
• Randevu sistemi

🔬 Veteriner Ekibimiz:
• Uzman veteriner hekimler
• Farklı uzmanlık alanları
• 15+ yıl deneyim
• Türkçe destek

💊 Sağlık Takibi:
• Dijital sağlık dosyası
• Aşı takibi
• İlaç hatırlatıcıları
• Kilo ve gelişim takibi

🎯 Avantajlar:
• Kliniğe gitmeden ön değerlendirme
• Zaman ve maliyet tasarrufu
• Acil durumlarda hızlı destek
• Kişiselleştirilmiş bakım planı

⏰ 7/24 Erişim!
🐕 Tüm evcil hayvan türleri için!''',
                'fiyat': '1499.99',
                'indirimli_fiyat': '1199.99',
                'stok': 50,
                'kategori': kategoriler['hizmet'],
                'tavsiye_edilen_tur': 'Tümü'
            },
        ]

        for urun_data in urunler:
            urun, created = Urun.objects.get_or_create(
                ad=urun_data['ad'],
                defaults=urun_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'[OK] "{urun.ad}" urunu basariyla eklendi!')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'[!] "{urun.ad}" zaten mevcut, atlanıyor.')
                )

        self.stdout.write(
            self.style.SUCCESS('\n[BASARILI] Tum urunler islendi!')
        )

