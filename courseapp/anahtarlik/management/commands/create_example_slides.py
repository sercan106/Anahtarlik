# anahtarlik/management/commands/create_example_slides.py
from django.core.management.base import BaseCommand
from anahtarlik.models import HeroSlide, HizmetKarti, AnaSayfaAyar


class Command(BaseCommand):
    help = 'Ana sayfa için örnek slide ve hizmet kartları oluşturur'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Mevcut veriler temizleniyor...'))

        # Mevcut verileri temizle
        HeroSlide.objects.all().delete()
        HizmetKarti.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('[OK] Eski veriler temizlendi'))

        # Ana sayfa ayarlarını yapılandır
        ayarlar = AnaSayfaAyar.load()
        ayarlar.hizmetler_baslik = "Hizmetlerimiz"
        ayarlar.hizmetler_aciklama = "Evcil dostlarınız için her şey bir arada! QR etiketlerden sağlık takibine, alışverişten randevulara kadar kapsamlı hizmetlerimizi keşfedin."
        ayarlar.slide_gecis_suresi = 5000
        ayarlar.slide_animasyon = 'fade'
        ayarlar.save()

        self.stdout.write(self.style.SUCCESS('[OK] Ana sayfa ayarları güncellendi'))

        # Hero Slide'ları oluştur
        slides = [
            {
                'baslik': 'Evcil Dostunuz İçin Akıllı Kimlik',
                'aciklama': 'QR kodlu etiketlerimizle kayıp evcil hayvanlar anında sahipleriyle buluşuyor. Konum takibi, sağlık bilgileri ve acil durum iletişimi tek bir QR kodda!',
                'arka_plan_renk': 'linear-gradient(135deg, rgba(255, 107, 157, 0.95) 0%, rgba(78, 205, 196, 0.85) 100%)',
                'buton_1_metin': '',
                'buton_1_url': '',
                'buton_2_metin': '',
                'buton_2_url': '',
                'sira': 1,
                'aktif': True,
            },
            {
                'baslik': 'Veteriner Randevuları Artık Çok Kolay',
                'aciklama': 'Yakınınızdaki veterinerleri keşfedin, online randevu alın ve dostunuzun sağlık geçmişini tek yerden yönetin. Aşı takibi, muayene geçmişi hep elinizin altında!',
                'arka_plan_renk': 'linear-gradient(135deg, rgba(91, 155, 213, 0.95) 0%, rgba(112, 193, 179, 0.85) 100%)',
                'buton_1_metin': 'Veteriner Bul',
                'buton_1_url': '/veteriner/liste/',
                'buton_2_metin': 'Randevu Al',
                'buton_2_url': '/veteriner/randevu/',
                'sira': 2,
                'aktif': True,
            },
            {
                'baslik': 'Pet Shop ve Market Alışverişi',
                'aciklama': 'Evcil hayvan ihtiyaçlarınız için güvenilir pet shopları keşfedin veya online market alışverişi yapın. Mama, oyuncak, aksesuar ve daha fazlası!',
                'arka_plan_renk': 'linear-gradient(135deg, rgba(255, 140, 66, 0.95) 0%, rgba(255, 107, 157, 0.85) 100%)',
                'buton_1_metin': 'Pet Shop Keşfet',
                'buton_1_url': '/petshop/liste/',
                'buton_2_metin': 'Markete Git',
                'buton_2_url': '/shop/',
                'sira': 3,
                'aktif': True,
            },
            {
                'baslik': 'Kayıp İlanları ve Sahiplendirme',
                'aciklama': 'Kayıp evcil hayvanınızı bildirin veya sahiplendirmek istediğiniz dostunuzu ilan verin. Binlerce hayvan severle buluşun, bir patiyi kurtarın!',
                'arka_plan_renk': 'linear-gradient(135deg, rgba(111, 207, 151, 0.95) 0%, rgba(91, 155, 213, 0.85) 100%)',
                'buton_1_metin': 'İlanları Gör',
                'buton_1_url': '/ilanlar/liste/',
                'buton_2_metin': 'İlan Ver',
                'buton_2_url': '/ilanlar/yeni/',
                'sira': 4,
                'aktif': True,
            },
        ]

        for slide_data in slides:
            HeroSlide.objects.create(**slide_data)

        self.stdout.write(self.style.SUCCESS(f'[OK] {len(slides)} adet hero slide olusturuldu'))

        # Hizmet Kartları oluştur
        hizmetler = [
            {
                'baslik': 'QR Etiket Sistemi',
                'aciklama': 'Akıllı QR etiketlerimiz ile evcil dostunuzun kimlik bilgilerini, sağlık kayıtlarını ve acil durum iletişim bilgilerini güvenle saklayın. Kaybolma durumunda anında bildirim alın!',
                'ikon': 'fas fa-qrcode',
                'buton_metin': 'Etiket Al',
                'buton_url': '/shop/',
                'sira': 1,
                'aktif': True,
                'animasyon_gecikmesi': 0,
            },
            {
                'baslik': 'Veteriner Randevuları',
                'aciklama': 'Yakınınızdaki veteriner kliniklerini keşfedin, online randevu alın. Aşı takibi, muayene geçmişi ve sağlık raporlarını tek bir platformda yönetin.',
                'ikon': 'fas fa-heartbeat',
                'buton_metin': 'Randevu Al',
                'buton_url': '/veteriner/liste/',
                'sira': 2,
                'aktif': True,
                'animasyon_gecikmesi': 100,
            },
            {
                'baslik': 'Pet Shop Ağı',
                'aciklama': 'Güvenilir pet shopları keşfedin, ürün ve hizmetlerini inceleyin. Yorumları okuyun, fiyatları karşılaştırın ve en yakın mağazayı bulun.',
                'ikon': 'fas fa-store',
                'buton_metin': 'Keşfet',
                'buton_url': '/petshop/liste/',
                'sira': 3,
                'aktif': True,
                'animasyon_gecikmesi': 200,
            },
            {
                'baslik': 'Online Market',
                'aciklama': 'Evcil hayvan mama, aksesuar, oyuncak ve bakım ürünlerini online olarak sipariş edin. Hızlı teslimat ve güvenli ödeme seçenekleri ile alışverişin keyfini çıkarın.',
                'ikon': 'fas fa-shopping-cart',
                'buton_metin': 'Alışverişe Başla',
                'buton_url': '/shop/',
                'sira': 4,
                'aktif': True,
                'animasyon_gecikmesi': 0,
            },
            {
                'baslik': 'Kayıp İlanları',
                'aciklama': 'Kayıp evcil hayvanınızı bildirin veya bulduğunuz hayvana sahip çıkmak isteyenlere ulaşın. Anlık bildirimler ve konum paylaşımı ile hızlı sonuç alın.',
                'ikon': 'fas fa-search',
                'buton_metin': 'İlanlar',
                'buton_url': '/ilanlar/liste/',
                'sira': 5,
                'aktif': True,
                'animasyon_gecikmesi': 100,
            },
            {
                'baslik': 'Sahiplendirme',
                'aciklama': 'Sahiplenmek istediğiniz evcil hayvanı bulun veya dostunuza yeni bir yuva bulmasında yardımcı olun. Güvenli ve kontrollü sahiplendirme süreci.',
                'ikon': 'fas fa-home',
                'buton_metin': 'Sahiplen',
                'buton_url': '/ilanlar/sahiplenme/',
                'sira': 6,
                'aktif': True,
                'animasyon_gecikmesi': 200,
            },
        ]

        for hizmet_data in hizmetler:
            HizmetKarti.objects.create(**hizmet_data)

        self.stdout.write(self.style.SUCCESS(f'[OK] {len(hizmetler)} adet hizmet karti olusturuldu'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Ornek veriler basariyla olusturuldu!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        self.stdout.write(f'  Toplam {len(slides)} hero slide')
        self.stdout.write(f'  Toplam {len(hizmetler)} hizmet karti')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Not: Admin paneli yerine ozel CMS arayuzunu kullanabilirsiniz:'))
        self.stdout.write(self.style.WARNING('   URL: /yonetim/icerik/'))
        self.stdout.write('')
