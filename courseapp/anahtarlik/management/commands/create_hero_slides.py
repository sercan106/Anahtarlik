from django.core.management.base import BaseCommand
from anahtarlik.models import HeroSlide, HizmetKarti, AnaSayfaAyar


class Command(BaseCommand):
    help = 'Hero slide ve hizmet kartları için örnek veriler oluşturur'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Ana sayfa verileri oluşturuluyor...'))
        
        # Hero Slide'ları oluştur
        hero_slides = [
            {
                'baslik': 'Evcil Hayvanlarınız İçin En İyi Güvenlik Çözümü',
                'aciklama': 'QR kodlu künyelerimiz ile evcil hayvanlarınızı kaybetmek artık geçmişte kaldı. Anlık takip ve GPS konum özelliği ile dostlarınızı her zaman güvende tutun.',
                'arka_plan_renk': 'linear-gradient(135deg, rgba(91, 155, 213, 0.95) 0%, rgba(112, 193, 179, 0.9) 100%)',
                'buton_1_metin': 'Hemen Keşfet',
                'buton_1_url': '/shop/',
                'buton_2_metin': 'Nasıl Çalışır?',
                'buton_2_url': '#hizmetler',
                'sira': 1,
                'aktif': True
            },
            {
                'baslik': 'Profesyonel Veteriner ve Pet Shop Ağı',
                'aciklama': 'Güvenilir veteriner klinikleri ve pet shop\'lar ile evcil hayvanlarınızın sağlığı ve ihtiyaçları için en iyi çözümler. Randevu alın, ürün satın alın, her şey bir tık uzağınızda.',
                'arka_plan_renk': 'linear-gradient(135deg, rgba(255, 140, 66, 0.95) 0%, rgba(242, 201, 76, 0.9) 100%)',
                'buton_1_metin': 'Veteriner Bul',
                'buton_1_url': '/vet-listesi/',
                'buton_2_metin': 'Pet Shop Keşfet',
                'buton_2_url': '/pet-shop-listesi/',
                'sira': 2,
                'aktif': True
            },
            {
                'baslik': 'Sahiplendirme ve Evcil Hayvan İlanları',
                'aciklama': 'Evcil hayvan sahiplendirme veya yeni bir dost arayanlar için kapsamlı ilan platformu. Güvenli alışveriş ve sahiplendirme süreçleri ile yeni aile üyelerinizi bulun.',
                'arka_plan_renk': 'linear-gradient(135deg, rgba(111, 207, 151, 0.95) 0%, rgba(168, 230, 207, 0.9) 100%)',
                'buton_1_metin': 'İlan Ver',
                'buton_1_url': '/ilan/ilan-verme-kontrol/',
                'buton_2_metin': 'İlanları İncele',
                'buton_2_url': '/ilanlar/',
                'sira': 3,
                'aktif': True
            }
        ]
        
        created_slides = 0
        for slide_data in hero_slides:
            slide, created = HeroSlide.objects.get_or_create(
                baslik=slide_data['baslik'],
                defaults=slide_data
            )
            if created:
                created_slides += 1
                self.stdout.write(self.style.SUCCESS(f'  ✅ Hero slide oluşturuldu: {slide.baslik}'))
            else:
                self.stdout.write(self.style.WARNING(f'  ⚠️  Hero slide zaten mevcut: {slide.baslik}'))
        
        # Hizmet Kartlarını oluştur
        hizmet_kartlari = [
            {
                'baslik': 'QR Künye Sistemi',
                'aciklama': 'Evcil hayvanlarınız için QR kodlu künyeler ile kayıp durumunda anında bulunma imkanı. GPS takip ve bildirim sistemi dahil.',
                'ikon': 'fas fa-qrcode',
                'buton_metin': 'Keşfet',
                'buton_url': '/etiketler/',
                'sira': 1,
                'aktif': True,
                'animasyon_gecikmesi': 100
            },
            {
                'baslik': 'Veteriner Randevusu',
                'aciklama': 'Bölgenizdeki güvenilir veteriner kliniklerinden online randevu alın. Evcil hayvanlarınızın sağlık takibini dijital ortamda yönetin.',
                'ikon': 'fas fa-calendar-check',
                'buton_metin': 'Randevu Al',
                'buton_url': '/veteriner-listesi/',
                'sira': 2,
                'aktif': True,
                'animasyon_gecikmesi': 200
            },
            {
                'baslik': 'Mağaza & Ürünler',
                'aciklama': 'Evcil hayvanlarınız için ihtiyaç duyduğunuz her şey. Yem, aksesuar, oyuncak ve bakım ürünlerinde en uygun fiyatlar.',
                'ikon': 'fas fa-shopping-cart',
                'buton_metin': 'Alışveriş Yap',
                'buton_url': '/shop/',
                'sira': 3,
                'aktif': True,
                'animasyon_gecikmesi': 300
            },
            {
                'baslik': 'Sahiplendirme',
                'aciklama': 'Evcil hayvan sahiplendirme veya yeni bir dost arayanlar için güvenli platform. Doğru eşleşme ile mutlu yuvalar.',
                'ikon': 'fas fa-heart',
                'buton_metin': 'İlan Ver',
                'buton_url': '/ilan/ilan-verme-kontrol/',
                'sira': 4,
                'aktif': True,
                'animasyon_gecikmesi': 400
            }
        ]
        
        created_kartlar = 0
        for kart_data in hizmet_kartlari:
            kart, created = HizmetKarti.objects.get_or_create(
                baslik=kart_data['baslik'],
                defaults=kart_data
            )
            if created:
                created_kartlar += 1
                self.stdout.write(self.style.SUCCESS(f'  ✅ Hizmet kartı oluşturuldu: {kart.baslik}'))
            else:
                self.stdout.write(self.style.WARNING(f'  ⚠️  Hizmet kartı zaten mevcut: {kart.baslik}'))
        
        # Ana Sayfa Ayarlarını oluştur
        ayarlar, created = AnaSayfaAyar.objects.get_or_create(
            pk=1,
            defaults={
                'hizmetler_baslik': 'Hizmetlerimiz',
                'hizmetler_aciklama': 'Evcil dostlarınız için en iyi dijital kimlik ve sağlık takip çözümleri',
                'slide_gecis_suresi': 5000,
                'slide_animasyon': 'fade'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'  ✅ Ana sayfa ayarları oluşturuldu'))
        else:
            self.stdout.write(self.style.WARNING(f'  ⚠️  Ana sayfa ayarları zaten mevcut'))
        
        # Özet
        self.stdout.write(self.style.SUCCESS(''))
        self.stdout.write(self.style.SUCCESS('✅ Tüm veriler başarıyla oluşturuldu!'))
        self.stdout.write(self.style.SUCCESS(f'📊 Oluşturulan Hero Slide: {created_slides}'))
        self.stdout.write(self.style.SUCCESS(f'📊 Oluşturulan Hizmet Kartı: {created_kartlar}'))
        self.stdout.write(self.style.SUCCESS(''))
        self.stdout.write(self.style.SUCCESS('🎉 Admin panelinden bu verileri düzenleyebilirsiniz!'))
