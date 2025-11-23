# courseapp/context_processors.py (Global sepet context için)
from shop.models import Urun
from django.urls import reverse
from django.utils.functional import cached_property

def user_panel_target(request):
    """
    Kullanıcı paneli menüsü için hedef URL'yi belirler:
    - Veteriner: profil tamam ise veteriner paneli, değilse profil tamamlama
    - Petshop: profil tamamlama (panel yoksa), aksi halde panel
    - Son kullanıcı: evcil hayvan kullanıcı paneli
    """
    try:
        user = request.user
        if not user.is_authenticated:
            return { 'user_panel_url': reverse('user_login') }

        # Veteriner profili var mı?
        vet = getattr(user, 'veteriner_profili', None)
        if vet is not None:
            if not vet.il or not vet.adres_detay:
                return { 'user_panel_url': reverse('veteriner:veteriner_profil_tamamla') }
            return { 'user_panel_url': reverse('veteriner:veteriner_paneli') }

        # Petshop profili var mı?
        shop = getattr(user, 'petshop_profili', None)
        if shop is not None:
            # Panel URL'i tanımlı değilse profil tamamlama sayfasına yönlendir.
            try:
                return { 'user_panel_url': reverse('petshop:petshop_paneli') }
            except Exception:
                return { 'user_panel_url': reverse('petshop:petshop_profil_tamamla') }

        # Misafir kullan�c� m�?
        guest = getattr(user, 'misafir_profili', None)
        if guest is not None:
            return { 'user_panel_url': reverse('guest_dashboard') }

        # Son kullan�c� (Sahip)
        return { 'user_panel_url': reverse('kullanici_paneli') }
    except Exception:
        # Her ihtimale karşı, kullanıcı paneline veya girişe düş
        try:
            return { 'user_panel_url': reverse('kullanici_paneli') }
        except Exception:
            return { 'user_panel_url': reverse('user_login') }

def sepet_ozeti(request):
    """Sepet bilgilerini global olarak tüm template'lere gönderir"""
    from shop.models import Sepet, SepetKalemi
    from shop.cart_utils import get_guest_cart_items, get_guest_cart_total, get_guest_cart_count
    
    sepet_adet = 0
    sepet_toplam = 0
    sepet_items = []
    
    if request.user.is_authenticated:
        try:
            sepet = Sepet.objects.get(kullanici=request.user)
            sepet_items = list(sepet.kalemler.select_related('urun', 'urun__etiket_kategori').prefetch_related(
                'urun__resimler',
                'urun__etiket_kategori__fotograflar'
            ))
            sepet_adet = sepet.toplam_adet
            sepet_toplam = sepet.toplam_fiyat
        except Sepet.DoesNotExist:
            pass
    else:
        # Misafir kullanıcı için session sepetini kullan
        sepet_items = get_guest_cart_items(request)
        sepet_adet = get_guest_cart_count(request)
        sepet_toplam = get_guest_cart_total(request)
    
    return {
        'sepet_items': sepet_items,
        'sepet_toplam': sepet_toplam,
        'sepet_adet': sepet_adet,
    }

def kullanici_kredi(request):
    """
    Global olarak kullanıcı kredi bakiyesini tüm template'lerde kullanmak için context_processor
    Kredi hareketlerinden gerçek bakiyeyi hesaplar
    
    NOT: Sahip kullanıcıları Pro Paket sistemi kullandığı için kredi bakiyesi 0 olur.
    Misafir, Veteriner ve Petshop kullanıcıları için gerçek kredi bakiyesi gösterilir.
    """
    kredi_bakiye = 0
    sahip_ilan_sayisi = 0
    okunmamis_bildirim_sayisi = 0
    sahip_kunye_sayisi = 0
    
    if hasattr(request, 'user') and request.user.is_authenticated:
        try:
            # Kredi hareketlerinden toplam bakiyeyi hesapla
            from ilan.models import KrediHareketi, Ilan
            from anahtarlik.models import Bildirim
            from etiket.models import Etiket
            
            # Tüm kullanıcılar için kredi bakiyesini göster
            # Kullanıcının tüm kredi hareketlerini topla
            hareketler = KrediHareketi.objects.filter(kullanici=request.user)
            hareket_toplami = sum(hareket.miktar for hareket in hareketler)
            
            # Başlangıç kredisi 0 + hareket toplamı
            kredi_bakiye = max(0, hareket_toplami)  # Negatif olamaz
            
            # Kullanıcının tüm ilanlarının sayısını hesapla (her kullanıcı tipi için)
            sahip_ilan_sayisi = Ilan.objects.filter(
                hayvan_profili__kullanici=request.user,
                aktif=True
            ).count()
            
            # Okunmamış bildirim sayısını hesapla (sadece sahip kullanıcıları için)
            if hasattr(request.user, 'sahip'):
                okunmamis_bildirim_sayisi = Bildirim.objects.filter(
                    sahip=request.user.sahip,
                    okundu=False
                ).count()
                
                # Künye sayısını hesapla (sadece sahip kullanıcıları için)
                sahip_kunye_sayisi = Etiket.objects.filter(
                    evcil_hayvan__sahip=request.user.sahip
                ).count()
                
        except Exception as e:
            # Hata durumunda varsayılan değer
            kredi_bakiye = 0
            sahip_ilan_sayisi = 0
            okunmamis_bildirim_sayisi = 0
            sahip_kunye_sayisi = 0
    
    return {
        'user_kredi_bakiye': kredi_bakiye,
        'sahip_ilan_sayisi': sahip_ilan_sayisi,
        'okunmamis_bildirim_sayisi': okunmamis_bildirim_sayisi,
        'sahip_kunye_sayisi': sahip_kunye_sayisi
    }




# from wejegeh.models import Program_Anasayfa,Logos,Proje_anasayfa,Hakkimizda,Ev,Yayıncılık,Settings,Slide_index,Adres
# from wejegeh.models import ,Logo,Slide_anasayfa, Slide_b,

# def logo(request):
#     veri =  Logo.objects.all()
#     return {
#         'logo': veri #Genel temlateye logo ismi ile döndürdük
#     }

# def slide(request):
#     veri =  Slide_anasayfa.objects.all()
#     return {
#         'slide': veri #Genel temlateye logo ismi ile döndürdük
#     }

# def slide_b(request):
#     veri =  Slide_b.objects.all()
#     return {
#         'slide_b': veri #Genel temlateye logo ismi ile döndürdük
#     }

# def photoss(request):
#     veri =  Slide_index.objects.all()
#     return {
#         'photoss': veri #Genel temlateye logo ismi ile döndürdük
#     }


# def program_anasayfa(request):
#     veri =  Program_Anasayfa.objects.all()
#     return {
#         'program_anasayfa': veri #Genel temlateye logo ismi ile döndürdük
#     }

# def logolar_anasayfa(request):
#     veri =  Logos.objects.all()
#     return {
#         'logos': veri #Genel temlateye logo ismi ile döndürdük
#     }

# def projeanasayfa(request):
#     veri =  Proje_anasayfa.objects.all()
#     return {
#         'projeanasayfa': veri #Genel temlateye logo ismi ile döndürdük
#     }
# def hakkımızda(request):
#     veri =  Hakkimizda.objects.all()
#     return {
#         'hakkımızda': veri #Genel temlateye logo ismi ile döndürdük
#     }

# def ev(request):
#     veri =  Ev.objects.all()
#     return {
#         'ev': veri #Genel temlateye logo ismi ile döndürdük
#     }

# def yayıncılık(request):
#     veri =  Yayıncılık.objects.all()
#     return {
#         'yayıncılık': veri #Genel temlateye logo ismi ile döndürdük
#     }

# def ayar(request):
#     veri =  Settings.objects.all()
#     return {
#         'ayar': veri #Genel temlateye logo ismi ile döndürdük
#     }

# def adres(request):
#     veri =  Adres.objects.all()
#     return {
#         'adres': veri #Genel temlateye logo ismi ile döndürdük
#     }
