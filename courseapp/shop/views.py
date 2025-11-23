# shop/views.py
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q, Sum
from .models import Urun, MagazaKarti, Sepet, SepetKalemi, Adres, Siparis, SiparisKalemi
from etiket.models import Etiket, KANAL_ONLINE, KANAL_SHOP, KANAL_VET

def create_etiket_for_order(siparis):
    """
    Sipariş için otomatik etiket oluştur
    """
    try:
        # Etiket ürünlerini kontrol et
        etiket_kalemler = siparis.kalemler.filter(urun__urun_tipi='etiket')
        
        if not etiket_kalemler.exists():
            return
        
        # Bu sipariş için daha önce etiket oluşturulmuş mu kontrol et
        if siparis.kullanici:
            kullanici_adi = siparis.kullanici.get_full_name() or siparis.kullanici.username
        else:
            kullanici_adi = siparis.misafir_ad_soyad
        
        # Sipariş tarih aralığında bu kullanıcı için etiket oluşturulmuş mu kontrol et
        from django.utils import timezone
        from datetime import timedelta
        siparis_tarihi = siparis.olusturulma_tarihi
        kayit_araligi = (siparis_tarihi - timedelta(seconds=60), siparis_tarihi + timedelta(seconds=60))
        
        mevcut_etiket = Etiket.objects.filter(
            musteri_adi=kullanici_adi,
            olusturulma_tarihi__range=kayit_araligi,
            kategori=etiket_kalemler.first().urun.etiket_kategori
        ).first()
        
        if mevcut_etiket:
            # Etiket zaten var, tekrar oluşturma
            return
        
        # Kullanıcı tipini belirle
        kanal = KANAL_ONLINE
        satici_veteriner = None
        satici_petshop = None
        
        if siparis.kullanici:
            if hasattr(siparis.kullanici, 'veteriner_profili'):
                kanal = KANAL_VET
                satici_veteriner = siparis.kullanici.veteriner_profili
            elif hasattr(siparis.kullanici, 'petshop_profili'):
                kanal = KANAL_SHOP
                satici_petshop = siparis.kullanici.petshop_profili
        
        # Her etiket ürünü için etiket oluştur
        for kalem in etiket_kalemler:
            for i in range(kalem.miktar):  # Her birim için ayrı etiket
                etiket_data = {
                    'kanal': kanal,
                    'kategori': kalem.urun.etiket_kategori,
                    'aktif': False,  # Başlangıçta pasif
                    'satis_tarihi': siparis.olusturulma_tarihi,  # ✅ DÜZELTME: Satış tarihi
                }
                
                # Kanal bilgilerini ekle
                if kanal == KANAL_VET and satici_veteriner:
                    etiket_data['satici_veteriner'] = satici_veteriner
                elif kanal == KANAL_SHOP and satici_petshop:
                    etiket_data['satici_petshop'] = satici_petshop
                
                # Müşteri bilgilerini ekle
                if siparis.kullanici:
                    # Authenticated kullanıcı
                    etiket_data['musteri_adi'] = siparis.kullanici.get_full_name() or siparis.kullanici.username
                    # ✅ DÜZELTME: Telefon yerine email yazma hatası düzeltildi
                    etiket_data['musteri_telefon'] = getattr(siparis.kullanici, 'telefon', '') or siparis.kullanici.email
                else:
                    # Misafir kullanıcı
                    etiket_data['musteri_adi'] = siparis.misafir_ad_soyad
                    etiket_data['musteri_telefon'] = siparis.misafir_telefon
                
                # Adres bilgilerini ekle
                if siparis.adres and hasattr(siparis.adres, 'get_full_address'):
                    etiket_data['adres_kullanici'] = siparis.adres.get_full_address()
                elif siparis.adres:
                    etiket_data['adres_kullanici'] = siparis.adres
                else:
                    etiket_data['adres_kullanici'] = "Adres bilgisi yok"
                
                # Etiket oluştur
                etiket = Etiket.objects.create(**etiket_data)
                
    except Exception as e:
        print(f"Etiket oluşturma hatası: {e}")
        import traceback
        traceback.print_exc()

def shop_home(request):
    """
    Ana mağaza sayfası - Mağaza kartları ve ürün slider'ları
    """

    # Aktif mağaza kartlarını sıraya göre getir - Sadece aktif resimleri prefetch et
    from django.db.models import Prefetch
    from .models import MagazaKartiResim
    magaza_kartlari = MagazaKarti.objects.filter(aktif=True).prefetch_related(
        Prefetch(
            'kart_resimleri',
            queryset=MagazaKartiResim.objects.filter(aktif=True).order_by('sira', 'olusturulma_tarihi'),
            to_attr='aktif_resimler'
        )
    ).order_by('sira', 'baslik')

    # Öne çıkan etiket ürünleri (slider için)
    one_cikan_etiketler = Urun.objects.filter(
        urun_tipi='etiket',
        aktif=True,
        one_cikan=True
    ).select_related('etiket_kategori').prefetch_related('resimler')[:8]
    
    # Her etiket ürünü için kullanıcı fiyatını hesapla
    for urun in one_cikan_etiketler:
        urun.kullanici_fiyati = urun.get_kullanici_fiyati(request.user)

    # Öne çıkan petshop ürünleri (slider için) - Kedi ürünleri dahil
    one_cikan_petshop = Urun.objects.filter(
        urun_tipi='normal',
        aktif=True,
        one_cikan=True
    ).prefetch_related('kategoriler', 'resimler')[:8]
    
    # Her petshop ürünü için kullanıcı fiyatını hesapla
    for urun in one_cikan_petshop:
        urun.kullanici_fiyati = urun.get_kullanici_fiyati(request.user)

    # İstatistikler
    petshop_count = Urun.objects.filter(urun_tipi='normal', aktif=True).count()
    etiket_count = Urun.objects.filter(urun_tipi='etiket', aktif=True).count()

    context = {
        'magaza_kartlari': magaza_kartlari,
        'one_cikan_etiketler': one_cikan_etiketler,
        'one_cikan_petshop': one_cikan_petshop,
        'petshop_count': petshop_count,
        'etiket_count': etiket_count,
        'total_count': petshop_count + etiket_count,
    }

    return render(request, 'shop/shop_home.html', context)


def etiket_list(request):
    """
    QR Künye ürünleri listesi - Accordion kategori yapısı ile
    """
    from etiket.models import EtiketKategori
    
    # Pseudo-alt kategori sınıfı (Etiket kategorileri için)
    class PseudoAltKategori:
        def __init__(self, etiket_kat):
            self.id = f"etiket_{etiket_kat.id}"  # Unique ID için prefix
            self.ad = etiket_kat.ad
            self.etiket_kategori_id = etiket_kat.id
            self.urun_sayisi = Urun.objects.filter(
                urun_tipi='etiket',
                aktif=True,
                etiket_kategori=etiket_kat
            ).count()
    
    # Pseudo ana kategori oluştur (Etiket Ürünleri)
    class PseudoAnaKategori:
        def __init__(self):
            self.id = 'etiket_ana'  # Özel ID
            self.ad = 'Etiket Ürünleri'
            self.slug = 'etiket-urunleri'
            self.icon = 'fas fa-qrcode'
            self.urun_sayisi = Urun.objects.filter(
                urun_tipi='etiket',
                aktif=True
            ).count()
            
            # EtiketKategori'lerden alt kategoriler oluştur
            etiket_kategoriler = EtiketKategori.objects.filter(aktif=True).order_by('ad')
            self.alt_kategoriler_liste = []
            for etiket_kat in etiket_kategoriler:
                pseudo_alt = PseudoAltKategori(etiket_kat)
                self.alt_kategoriler_liste.append(pseudo_alt)
    
    # Ana kategori oluştur
    ana_kategori = PseudoAnaKategori()
    ana_kategoriler = [ana_kategori]
    
    # Arama sorgusu
    search_query = request.GET.get('q', '').strip()
    
    # Kategori filtresi
    kategori_id = request.GET.get('kategori')
    secilen_kategori = None
    secilen_etiket_kategori_id = None
    
    urunler = Urun.objects.filter(
        urun_tipi='etiket',
        aktif=True
    ).select_related('etiket_kategori').prefetch_related(
        'resimler',
        'etiket_kategori__fotograflar'
    )
    
    # Arama filtresi
    if search_query:
        urunler = urunler.filter(
            ad__icontains=search_query
        )
    
    # Kategori filtresi
    if kategori_id:
        # Etiket kategori ID'si mi kontrol et (etiket_ prefix ile başlıyorsa)
        if str(kategori_id).startswith('etiket_'):
            # Ana kategori seçildi mi kontrol et
            if str(kategori_id) == 'etiket_ana':
                # Ana kategori seçildi - tüm etiket ürünleri gösterilir (zaten tümü)
                pass
            else:
                # Alt kategori seçildi - sadece o kategorideki ürünleri göster
                try:
                    secilen_etiket_kategori_id = int(str(kategori_id).replace('etiket_', ''))
                    urunler = urunler.filter(etiket_kategori_id=secilen_etiket_kategori_id)
                except ValueError:
                    # Geçersiz ID formatı - tüm ürünleri göster
                    pass
    
    # Sıralama
    sort_by = request.GET.get('sort', '')
    if sort_by == 'price_asc':
        urunler = urunler.order_by('fiyat')
    elif sort_by == 'price_desc':
        urunler = urunler.order_by('-fiyat')
    elif sort_by == 'name_asc':
        urunler = urunler.order_by('ad')
    elif sort_by == 'name_desc':
        urunler = urunler.order_by('-ad')
    else:
        urunler = urunler.order_by('-one_cikan', '-yeni_urun', 'ad')
    
    # Sayfalama
    paginator = Paginator(urunler, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Her ürün için kullanıcı fiyatını hesapla
    for urun in page_obj:
        urun.kullanici_fiyati = urun.get_kullanici_fiyati(request.user)
    
    # Seçili kategori ID'sini belirle
    if secilen_etiket_kategori_id:
        secilen_kategori_id = f"etiket_{secilen_etiket_kategori_id}"
    elif kategori_id == 'etiket_ana':
        secilen_kategori_id = 'etiket_ana'
    else:
        secilen_kategori_id = None
    
    context = {
        'page_obj': page_obj,
        'magaza_tipi': 'QR Künye',
        'toplam_urun': urunler.count(),
        'ana_kategoriler': ana_kategoriler,  # petshop_list ile aynı yapı
        'secilen_kategori': secilen_kategori_id,
        'search_query': search_query,
    }
    
    return render(request, 'shop/urun_list.html', context)


def urun_detay(request, urun_id):
    """Ürün detay sayfası"""
    urun = get_object_or_404(
        Urun.objects.select_related('etiket_kategori').prefetch_related(
            'resimler',
            'etiket_kategori__fotograflar'
        ), 
        id=urun_id, 
        aktif=True
    )
    
    # Kullanıcı tipine göre fiyat al
    kullanici_fiyati = urun.get_kullanici_fiyati(request.user)
    
    # Benzer ürünler
    benzer_urunler = Urun.objects.filter(
        urun_tipi=urun.urun_tipi,
        aktif=True
    ).exclude(id=urun.id)[:4]
    
    context = {
        'urun': urun,
        'benzer_urunler': benzer_urunler,
        'kullanici_fiyati': kullanici_fiyati,
    }
    
    return render(request, 'shop/urun_detay.html', context)


def petshop_list(request):
    """
    Pet ürünleri listesi - Hiyerarşik kategori yapısı ile
    
    Ürün Listeleme Mantığı:
    1. Ana kategori seçilirse -> O kategorinin TÜM alt kategorilerindeki ürünler gösterilir
    2. Alt kategori seçilirse -> Sadece o alt kategorideki ürünler gösterilir
    3. Hiçbir kategori seçilmezse -> Tüm ürünler gösterilir
    """
    from shop.models import Kategori
    
    # EtiketKategori modelini import et
    from etiket.models import EtiketKategori
    
    from collections import defaultdict

    # Tüm aktif kategorileri tek seferde çek ve hiyerarşiyi kur
    tum_kategoriler = list(
        Kategori.objects.filter(aktif=True)
        .select_related('parent')
        .order_by('sira', 'ad')
    )

    kategori_lookup = {}
    cocuk_haritasi = defaultdict(list)

    for kategori in tum_kategoriler:
        kategori_lookup[kategori.id] = kategori
        kategori.alt_kategoriler_liste = []
        kategori.direct_urun_sayisi = 0
        kategori.total_urun_sayisi = 0
        if kategori.parent_id:
            cocuk_haritasi[kategori.parent_id].append(kategori)

    for parent_id, cocuklar in cocuk_haritasi.items():
        if parent_id in kategori_lookup:
            kategori_lookup[parent_id].alt_kategoriler_liste = cocuklar

    # Normal ürünler için doğrudan kategori ürün sayıları
    kategori_dogrudan_sayilar = {
        row['kategoriler']: row['count']
        for row in Urun.objects.filter(
            urun_tipi='normal',
            aktif=True,
            kategoriler__isnull=False
        ).values('kategoriler').annotate(count=Count('id'))
    }

    for kategori_id, sayi in kategori_dogrudan_sayilar.items():
        if kategori_id in kategori_lookup:
            kategori_lookup[kategori_id].direct_urun_sayisi = sayi
            kategori_lookup[kategori_id].urun_sayisi = sayi

    # Descendant hesaplamaları (tek seferde)
    descendants_map = {}

    def toplam_hesapla(kategori):
        toplam = getattr(kategori, 'direct_urun_sayisi', 0)
        descendants = []
        for cocuk in kategori.alt_kategoriler_liste:
            cocuk_toplam, cocuk_descendants = toplam_hesapla(cocuk)
            toplam += cocuk_toplam
            descendants.append(cocuk)
            descendants.extend(cocuk_descendants)
        kategori.total_urun_sayisi = toplam
        descendants_map[kategori.id] = descendants
        return toplam, descendants

    for kategori in tum_kategoriler:
        if kategori.parent_id is None:
            toplam_hesapla(kategori)

    def dogrudan_sayilari_ata(kategori):
        for cocuk in kategori.alt_kategoriler_liste:
            cocuk.urun_sayisi = getattr(cocuk, 'direct_urun_sayisi', 0)
            dogrudan_sayilari_ata(cocuk)

    for kategori in tum_kategoriler:
        if kategori.parent_id is None:
            kategori.urun_sayisi = getattr(kategori, 'total_urun_sayisi', 0)
            dogrudan_sayilari_ata(kategori)
        else:
            kategori.urun_sayisi = getattr(kategori, 'direct_urun_sayisi', 0)

    ana_kategoriler = [kategori for kategori in tum_kategoriler if kategori.parent_id is None]

    # Etiket kategorileri için sayıları tek seferde hazırla
    etiket_kategoriler_qs = EtiketKategori.objects.filter(aktif=True).order_by('ad')
    etiket_urun_sayilari = {
        row['etiket_kategori']: row['count']
        for row in Urun.objects.filter(
            urun_tipi='etiket',
            aktif=True,
            etiket_kategori__isnull=False
        ).values('etiket_kategori').annotate(count=Count('id'))
    }
    toplam_etiket_urun = sum(etiket_urun_sayilari.values())

    # Pseudo-alt kategori sınıfı (Etiket kategorileri için)
    class PseudoAltKategori:
        def __init__(self, etiket_kat, urun_sayisi):
            self.id = f"etiket_{etiket_kat.id}"  # Unique ID için prefix
            self.ad = etiket_kat.ad
            self.etiket_kategori_id = etiket_kat.id
            self.urun_sayisi = urun_sayisi
    
    # Her ana kategori için ürün sayısını hesapla
    for kategori in ana_kategoriler:
        # "Etiket Ürünleri" kategorisi için özel mantık
        if kategori.slug == 'etiket-urunleri' or 'Etiket' in kategori.ad:
            kategori.urun_sayisi = toplam_etiket_urun
            kategori.alt_kategoriler_liste = [
                PseudoAltKategori(etiket_kat, etiket_urun_sayilari.get(etiket_kat.id, 0))
                for etiket_kat in etiket_kategoriler_qs
            ]
    
    # Arama sorgusu
    search_query = request.GET.get('q', '').strip()

    # Kategori filtresi
    kategori_id = request.GET.get('kategori')
    secilen_kategori = None  # Initialize to None
    secilen_etiket_kategori_id = None  # Etiket kategori ID'si

    # Kategori seçimi kontrolü
    urunler = None
    if kategori_id:
        # Etiket kategori ID'si mi kontrol et (etiket_ prefix ile başlıyorsa)
        if str(kategori_id).startswith('etiket_'):
            secilen_etiket_kategori_id = int(str(kategori_id).replace('etiket_', ''))
            urunler = Urun.objects.filter(
                urun_tipi='etiket',
                aktif=True,
                etiket_kategori_id=secilen_etiket_kategori_id
            ).select_related('etiket_kategori').prefetch_related(
                'resimler',
                'etiket_kategori__fotograflar'
            )
        else:
            try:
                secilen_kategori_id = int(kategori_id)
                secilen_kategori = kategori_lookup.get(secilen_kategori_id)
                if secilen_kategori is None:
                    raise ValueError
            except (ValueError, TypeError):
                secilen_kategori = None
            else:
                if secilen_kategori.slug == 'etiket-urunleri' or 'Etiket' in secilen_kategori.ad:
                    urunler = Urun.objects.filter(
                        urun_tipi='etiket',
                        aktif=True
                    ).select_related('etiket_kategori').prefetch_related(
                        'resimler',
                        'etiket_kategori__fotograflar'
                    )
                else:
                    urunler = Urun.objects.filter(
                        urun_tipi='normal',
                        aktif=True
                    ).prefetch_related('kategoriler', 'resimler')
                    if secilen_kategori.parent is None:
                        descendant_ids = [cat.id for cat in descendants_map.get(secilen_kategori.id, [])]
                        kategoriler_ids = [secilen_kategori.id] + descendant_ids
                        urunler = urunler.filter(kategoriler__id__in=kategoriler_ids).distinct()
                    else:
                        urunler = urunler.filter(kategoriler__id=secilen_kategori.id).distinct()
    if urunler is None:
        # Kategori seçilmemişse veya geçersizse, normal ürünleri göster
        urunler = Urun.objects.filter(
            urun_tipi='normal',
            aktif=True
        ).prefetch_related('kategoriler', 'resimler')
        secilen_kategori = None
        secilen_etiket_kategori_id = None

    # Arama filtresi (hem normal hem etiket ürünleri için)
    if search_query:
        urunler = urunler.filter(
            ad__icontains=search_query
        )
    
    # Sıralama
    sort_by = request.GET.get('sort', '')
    if sort_by == 'price_asc':
        urunler = urunler.order_by('fiyat')
    elif sort_by == 'price_desc':
        urunler = urunler.order_by('-fiyat')
    elif sort_by == 'name_asc':
        urunler = urunler.order_by('ad')
    elif sort_by == 'name_desc':
        urunler = urunler.order_by('-ad')
    else:
        urunler = urunler.order_by('-one_cikan', '-yeni_urun', 'ad')
    
    # Sayfalama
    paginator = Paginator(urunler, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Her ürün için kullanıcı fiyatını hesapla
    for urun in page_obj:
        urun.kullanici_fiyati = urun.get_kullanici_fiyati(request.user)
    
    # Seçili kategori ID'sini belirle
    if secilen_etiket_kategori_id:
        secilen_kategori_id = f"etiket_{secilen_etiket_kategori_id}"
    elif secilen_kategori:
        secilen_kategori_id = secilen_kategori.id
    else:
        secilen_kategori_id = None
    
    context = {
        'page_obj': page_obj,
        'magaza_tipi': 'Pet Ürünleri',
        'toplam_urun': urunler.count(),
        'ana_kategoriler': ana_kategoriler,
        'secilen_kategori': secilen_kategori_id,
        'search_query': search_query,
    }
    
    return render(request, 'shop/urun_list.html', context)


def sepet_goster(request):
    """Sepet görüntüleme sayfası - Hem authenticated hem misafir kullanıcılar için"""
    from shop.cart_utils import (
        get_guest_cart_items, get_guest_cart_total, get_guest_cart_count,
        get_cargo_options, calculate_order_total_with_cargo
    )
    
    if request.user.is_authenticated:
        # Authenticated kullanıcı için DB sepetini kullan
        sepet, created = Sepet.objects.get_or_create(kullanici=request.user)
        sepet_items = sepet.kalemler.select_related('urun', 'urun__etiket_kategori').prefetch_related(
            'urun__resimler',
            'urun__etiket_kategori__fotograflar'
        )
        
        # Her sepet kalemi için kullanıcı tipine göre fiyat güncelle
        for item in sepet_items:
            kullanici_fiyati = item.urun.get_kullanici_fiyati(request.user)
            fiyat_degeri = kullanici_fiyati['indirimli_fiyat'] if kullanici_fiyati['indirimli_fiyat'] else kullanici_fiyati['fiyat']
            fiyat_decimal = Decimal(str(fiyat_degeri))
            if item.birim_fiyat != fiyat_decimal:
                item.birim_fiyat = fiyat_decimal
                item.save(update_fields=['birim_fiyat'])
        
        sepet_toplam = float(sepet.toplam_fiyat)
        sepet_adet = sepet.toplam_adet
    else:
        # Misafir kullanıcı için session sepetini kullan
        sepet_items = get_guest_cart_items(request)
        sepet_toplam = float(get_guest_cart_total(request))
        sepet_adet = get_guest_cart_count(request)
        sepet = None  # Misafir kullanıcı için sepet objesi yok
    
    # Kullanıcı tipini belirle (JavaScript için)
    user_type = 'guest'
    if request.user.is_authenticated:
        if hasattr(request.user, 'petshop_profili'):
            user_type = 'petshop'
        elif hasattr(request.user, 'veteriner_profili'):
            user_type = 'veteriner'
        else:
            user_type = 'normal'
    
    # Kargo bilgileri (sepet sayfası için)
    kargo_secenekleri = get_cargo_options(sepet_toplam)
    kargo_bilgisi = calculate_order_total_with_cargo(sepet_toplam)
    
    context = {
        'sepet': sepet,
        'sepet_items': sepet_items,
        'sepet_toplam': sepet_toplam,
        'sepet_adet': sepet_adet,
        'user_type': user_type,
        # Kargo bilgileri
        'kargo_secenekleri': kargo_secenekleri,
        'kargo_bilgisi': kargo_bilgisi,
    }
    
    return render(request, 'shop/sepet.html', context)


def sepet_ekle(request, urun_id):
    """Ürünü sepete ekle - Hem authenticated hem misafir kullanıcılar için"""
    from shop.cart_utils import add_to_guest_cart
    
    urun = get_object_or_404(Urun, id=urun_id, aktif=True)
    miktar = int(request.POST.get('miktar', 1))
    
    if request.user.is_authenticated:
        # Authenticated kullanıcı için DB sepetini kullan
        sepet, created = Sepet.objects.get_or_create(kullanici=request.user)
        
        # Kullanıcı tipine göre fiyat hesapla
        kullanici_fiyati = urun.get_kullanici_fiyati(request.user)
        birim_fiyat = kullanici_fiyati['indirimli_fiyat'] if kullanici_fiyati['indirimli_fiyat'] else kullanici_fiyati['fiyat']
        
        # Aynı ürün varsa miktarı artır, yoksa yeni kalem ekle
        from decimal import Decimal as _Decimal  # local import to avoid circular
        sepet_kalemi, created = SepetKalemi.objects.get_or_create(
            sepet=sepet,
            urun=urun,
            defaults={'miktar': miktar, 'birim_fiyat': Decimal(str(birim_fiyat))}
        )
        
        fiyat_decimal = Decimal(str(birim_fiyat))
        if not created:
            sepet_kalemi.miktar += miktar
            # Fiyatı güncelle (bayi fiyatı değişmiş olabilir)
            sepet_kalemi.birim_fiyat = fiyat_decimal
            sepet_kalemi.save(update_fields=['miktar', 'birim_fiyat'])
        else:
            if sepet_kalemi.birim_fiyat != fiyat_decimal:
                sepet_kalemi.birim_fiyat = fiyat_decimal
                sepet_kalemi.save(update_fields=['birim_fiyat'])
    else:
        # Misafir kullanıcı için session sepetini kullan
        add_to_guest_cart(request, urun_id, miktar)
    
    messages.success(request, f'{urun.ad} sepete eklendi!')
    return redirect(request.META.get('HTTP_REFERER', 'shop:shop_home'))


def sepet_kalemi_sil(request, kalem_id):
    """
    Sepetten ürün çıkar - Hem authenticated hem misafir kullanıcılar için

    NOT:
    - Authenticated kullanıcılar için kalem_id = SepetKalemi.id
    - Misafir kullanıcılar için kalem_id = Urun.id (session sepet ürün ID'si ile çalışır)
    """
    from shop.cart_utils import remove_from_guest_cart, get_guest_cart_total, get_guest_cart_count
    from django.http import JsonResponse

    if request.user.is_authenticated:
        # Authenticated kullanıcı için DB sepetini kullan
        # kalem_id = SepetKalemi.id
        kalem = get_object_or_404(SepetKalemi, id=kalem_id, sepet__kullanici=request.user)
        sepet = kalem.sepet
        kalem.delete()

        # Güncel sepet bilgilerini al
        try:
            sepet.refresh_from_db()
            sepet_toplam = sepet.toplam_fiyat
            sepet_adet = sepet.toplam_adet
        except Sepet.DoesNotExist:
            sepet_toplam = 0
            sepet_adet = 0
    else:
        # Misafir kullanıcı için session sepetini kullan
        # kalem_id = Urun.id
        remove_from_guest_cart(request, kalem_id)

        # Güncel sepet bilgilerini al
        sepet_toplam = get_guest_cart_total(request)
        sepet_adet = get_guest_cart_count(request)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'toplam': sepet_toplam,
            'adet': sepet_adet
        })

    messages.success(request, 'Ürün sepetten çıkarıldı')
    return redirect('shop:sepet_goster')


def sepet_guncelle(request, kalem_id):
    """
    Sepet kalemi miktarını güncelle - Hem authenticated hem misafir kullanıcılar için

    NOT:
    - Authenticated kullanıcılar için kalem_id = SepetKalemi.id
    - Misafir kullanıcılar için kalem_id = Urun.id (session sepet ürün ID'si ile çalışır)
    """
    from shop.cart_utils import update_guest_cart_item, remove_from_guest_cart, get_guest_cart_total, get_guest_cart_items, get_guest_cart_count
    from django.http import JsonResponse

    yeni_miktar = int(request.POST.get('miktar', 1))

    if request.user.is_authenticated:
        # Authenticated kullanıcı için DB sepetini kullan
        # kalem_id = SepetKalemi.id
        kalem = get_object_or_404(SepetKalemi, id=kalem_id, sepet__kullanici=request.user)

        if yeni_miktar > 0:
            kalem.miktar = yeni_miktar
            # Kullanıcı tipine göre fiyat güncelle
            kullanici_fiyati = kalem.urun.get_kullanici_fiyati(request.user)
            fiyat_degeri = kullanici_fiyati['indirimli_fiyat'] if kullanici_fiyati['indirimli_fiyat'] else kullanici_fiyati['fiyat']
            kalem.birim_fiyat = Decimal(str(fiyat_degeri))
            kalem.save(update_fields=['miktar', 'birim_fiyat'])
            item_subtotal = float(kalem.subtotal)
            sepet = kalem.sepet
            ara_toplam = float(sepet.toplam_fiyat)
            toplam_adet = sepet.toplam_adet
        else:
            # Kalemi sil
            sepet = kalem.sepet
            kalem.delete()
            item_subtotal = 0
            # Sepeti yeniden al
            try:
                sepet = Sepet.objects.get(kullanici=request.user)
                ara_toplam = float(sepet.toplam_fiyat)
                toplam_adet = sepet.toplam_adet
            except Sepet.DoesNotExist:
                ara_toplam = 0
                toplam_adet = 0
    else:
        # Misafir kullanıcı için session sepetini kullan
        # kalem_id = Urun.id
        if yeni_miktar > 0:
            update_guest_cart_item(request, kalem_id, yeni_miktar)
            # Güncellenmiş sepet öğelerini al ve subtotal hesapla
            cart_items = get_guest_cart_items(request)
            item_subtotal = 0
            for item in cart_items:
                if item['id'] == kalem_id:
                    item_subtotal = item['subtotal']
                    break
        else:
            remove_from_guest_cart(request, kalem_id)
            item_subtotal = 0

        # Sepet toplamlarını hesapla
        ara_toplam = get_guest_cart_total(request)
        toplam_adet = get_guest_cart_count(request)

    return JsonResponse({
        'success': True,
        'subtotal': item_subtotal,
        'toplam': ara_toplam,
        'item_subtotal': item_subtotal,
        'sepet_toplam': ara_toplam,
        'sepet_ara_toplam': ara_toplam,
        'toplam_adet': toplam_adet
    })


def checkout(request):
    """Ödeme/Checkout sayfası - Hem authenticated hem misafir kullanıcılar için"""
    from shop.cart_utils import (
        get_guest_cart_items, get_guest_cart_total, get_guest_cart_count,
        get_cargo_options, calculate_order_total_with_cargo, get_default_cargo_company
    )
    
    if request.user.is_authenticated:
        # Authenticated kullanıcı için DB sepetini kullan
        sepet, created = Sepet.objects.get_or_create(kullanici=request.user)
        sepet_items = sepet.kalemler.select_related('urun').prefetch_related('urun__resimler')
        sepet_toplam = sepet.toplam_fiyat
        sepet_adet = sepet.toplam_adet
        
        # BAYİLER (Petshop/Veteriner) için minimum 5 adet etiket ürünü kontrolü
        is_bayi = hasattr(request.user, 'petshop_profili') or hasattr(request.user, 'veteriner_profili')
        
        if is_bayi:
            etiket_toplam_adet = 0
            for item in sepet_items:
                if item.urun.urun_tipi == 'etiket':
                    etiket_toplam_adet += item.miktar
            
            if etiket_toplam_adet > 0 and etiket_toplam_adet < 5:
                messages.warning(
                    request,
                    'Bayiler için etiket ürünlerinde minimum 5 adet sipariş şartı bulunmaktadır. '
                    f'Sepetinizde şu anda {etiket_toplam_adet} adet etiket ürünü bulunmaktadır.'
                )
                return redirect('shop:sepet_goster')
        
        # Kullanıcının adreslerini getir
        adresler = Adres.objects.filter(kullanici=request.user)
        
        # Eğer kullanıcının hiç adresi yoksa ve bayi ise (Sahip hariç), profilden otomatik adres oluştur
        if not adresler.exists():
            try:
                with transaction.atomic():
                    if hasattr(request.user, 'veteriner_profili'):
                        # Veteriner için otomatik adres oluştur
                        vet = request.user.veteriner_profili
                        if vet.il and vet.ilce and vet.adres_detay:
                            Adres.objects.create(
                                kullanici=request.user,
                                baslik="Veteriner Kliniği Adresi",
                                adres_tipi='is',
                                ad_soyad=vet.ad,
                                telefon=vet.telefon or '',
                                il=vet.il,
                                ilce=vet.ilce,
                                mahalle=vet.mahalle,
                                mahalle_diger=vet.mahalle_diger,
                                adres_satiri=vet.adres_detay,
                                varsayilan=True
                            )
                    elif hasattr(request.user, 'petshop_profili'):
                        # PetShop için otomatik adres oluştur
                        petshop = request.user.petshop_profili
                        if petshop.il and petshop.ilce and petshop.adres_detay:
                            Adres.objects.create(
                                kullanici=request.user,
                                baslik="PetShop Adresi",
                                adres_tipi='is',
                                ad_soyad=petshop.ad,
                                telefon=petshop.telefon or '',
                                il=petshop.il,
                                ilce=petshop.ilce,
                                mahalle=petshop.mahalle,
                                mahalle_diger=petshop.mahalle_diger,
                                adres_satiri=petshop.adres_detay,
                                varsayilan=True
                            )
                    # Sahipler için otomatik adres oluşturma yapılmaz - kullanıcı manuel eklemelidir
                # Transaction sonrası adres listesini yeniden getir
                adresler = Adres.objects.filter(kullanici=request.user)
            except Exception as e:
                # Hata durumunda mevcut adresleri kullan (loglama yapılabilir)
                adresler = Adres.objects.filter(kullanici=request.user)
        
        guest_checkout = False
        
    else:
        # Misafir kullanıcı için session sepetini kullan
        sepet_items = get_guest_cart_items(request)
        sepet_toplam = get_guest_cart_total(request)
        sepet_adet = get_guest_cart_count(request)
        adresler = []
        guest_checkout = True
        sepet = None
        
        if not sepet_items:
            messages.warning(request, 'Sepetiniz boş!')
            return redirect('shop:shop_home')
        
        # Misafir kullanıcılar için minimum adet kontrolü yok
    
    # Seçili adres (POST'tan gelen veya default)
    secili_adres_id = request.POST.get('adres_id') or request.GET.get('adres_id')
    secili_adres = None
    if secili_adres_id and not guest_checkout:
        secili_adres = adresler.filter(id=secili_adres_id).first()
    
    if not secili_adres and not guest_checkout and adresler.exists():
        secili_adres = adresler.first()
    
    # KARGO HESAPLAMA SİSTEMİ
    # Varsayılan kargo firmasını kullan (kullanıcı seçimi yok)
    secili_kargo_firmasi = get_default_cargo_company()

    if isinstance(sepet_toplam, Decimal):
        sepet_toplam_decimal = sepet_toplam
    else:
        sepet_toplam_decimal = Decimal(str(sepet_toplam))
        sepet_toplam = sepet_toplam_decimal
    
    kargo_ucreti = Decimal('0')
    toplam_fiyat = sepet_toplam
    
    # Varsayılan kargo firması varsa ücretini hesapla
    if secili_kargo_firmasi:
        kargo_ucreti = Decimal(str(secili_kargo_firmasi.kargo_ucreti_hesapla(sepet_toplam_decimal)))
        toplam_fiyat = sepet_toplam + kargo_ucreti
    
    context = {
        'sepet': sepet,
        'sepet_items': sepet_items,
        'sepet_toplam': sepet_toplam,
        'sepet_adet': sepet_adet,
        'adresler': adresler,
        'secili_adres': secili_adres,
        'guest_checkout': guest_checkout,
        # Kargo bilgileri (varsayılan firma, kullanıcı seçimi yok)
        'secili_kargo_firmasi': secili_kargo_firmasi,
        'kargo_ucreti': kargo_ucreti,
        'toplam_fiyat': toplam_fiyat,
    }
    
    return render(request, 'shop/checkout.html', context)


@login_required
def adres_ekle(request):
    """Yeni adres ekle"""
    from shop.forms import AdresForm

    if request.method == 'POST':
        form = AdresForm(request.POST)
        if form.is_valid():
            adres = form.save(commit=False)
            adres.kullanici = request.user
            adres.save()
            messages.success(request, 'Adres başarıyla eklendi!')

            # Checkout sayfasına yönlendir
            if request.POST.get('redirect_to') == 'checkout':
                return redirect('shop:checkout')
            return redirect('shop:adres_yonet')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        # Sahipler için otomatik form doldurma yapılmaz - kullanıcı manuel girmelidir
        form = AdresForm()

    context = {
        'form': form,
    }
    return render(request, 'shop/adres_ekle.html', context)


@login_required
def adres_yonet(request):
    """Adres yönetim sayfası"""
    adresler = Adres.objects.filter(kullanici=request.user)
    
    context = {
        'adresler': adresler,
    }
    
    return render(request, 'shop/adres_yonet.html', context)


@login_required
def adres_sil(request, adres_id):
    """Adres sil"""
    adres = get_object_or_404(Adres, id=adres_id, kullanici=request.user)
    adres.delete()
    messages.success(request, 'Adres silindi!')
    return redirect('shop:adres_yonet')


@transaction.atomic
def siparis_olustur(request):
    """Sipariş oluştur - Hem authenticated hem misafir kullanıcılar için"""
    from shop.cart_utils import (
        get_guest_cart_items, get_guest_cart_total, 
        calculate_cargo_cost, get_default_cargo_company
    )
    
    if request.method != 'POST':
        return redirect('shop:checkout')
    
    try:
        if request.user.is_authenticated:
            # Authenticated kullanıcı için DB sepetini kullan
            sepet, created = Sepet.objects.get_or_create(kullanici=request.user)
            sepet_items = sepet.kalemler.all()
            sepet_toplam = sepet.toplam_fiyat
            
            if not sepet_items.exists():
                messages.error(request, 'Sepetiniz boş!')
                return redirect('shop:checkout')
            
            # BAYİLER (Petshop/Veteriner) için minimum 5 adet etiket ürünü kontrolü
            is_bayi = hasattr(request.user, 'petshop_profili') or hasattr(request.user, 'veteriner_profili')
            
            if is_bayi:
                etiket_toplam_adet = 0
                for item in sepet_items:
                    if item.urun.urun_tipi == 'etiket':
                        etiket_toplam_adet += item.miktar
                
                if etiket_toplam_adet > 0 and etiket_toplam_adet < 5:
                    messages.warning(
                        request,
                        'Bayiler için etiket ürünlerinde minimum 5 adet sipariş şartı bulunmaktadır. '
                        f'Sepetinizde şu anda {etiket_toplam_adet} adet etiket ürünü bulunmaktadır.'
                    )
                    return redirect('shop:checkout')
            
            # Adres kontrolü
            adres_id = request.POST.get('adres_id')
            if not adres_id:
                messages.error(request, 'Lütfen bir adres seçin!')
                return redirect('shop:checkout')
            
            adres = get_object_or_404(Adres, id=adres_id, kullanici=request.user)
            
            # KARGO BİLGİLERİ - Varsayılan kargo firmasını kullan (kullanıcı seçimi yok)
            kargo_firmasi = get_default_cargo_company()
            kargo_ucreti = Decimal('0')
            
            if kargo_firmasi:
                kargo_ucreti = Decimal(str(kargo_firmasi.kargo_ucreti_hesapla(sepet_toplam)))
            
            # Toplam fiyat hesapla (sepet + kargo)
            toplam_fiyat = sepet_toplam + kargo_ucreti
            
            # Sipariş oluştur
            adres_metni = f"{adres.ad_soyad}\n{adres.telefon}\n{adres.il}, {adres.ilce}"
            if adres.mahalle:
                adres_metni += f"\n{adres.mahalle}"
            if adres.mahalle_diger:
                adres_metni += f"\n{adres.mahalle_diger}"
            if adres.adres_satiri:
                adres_metni += f"\n{adres.adres_satiri}"
            if adres.posta_kodu:
                adres_metni += f"\n{adres.posta_kodu}"
            if adres.adres_tarifi:
                adres_metni += f"\n{adres.adres_tarifi}"
            
            siparis = Siparis.objects.create(
                kullanici=request.user,
                toplam_fiyat=toplam_fiyat,  # Kargo dahil toplam
                adres=adres_metni,
                kargo_firma=kargo_firmasi
            )
            
            # Sipariş kalemlerini oluştur ve stok azalt
            for item in sepet_items:
                # Stok kontrolü ve azaltma
                if not item.urun.stok_azalt(item.miktar):
                    messages.error(request, f'{item.urun.ad} ürünü için yeterli stok yok!')
                    return redirect('shop:checkout')
                
                SiparisKalemi.objects.create(
                    siparis=siparis,
                    urun=item.urun,
                    miktar=item.miktar,
                    fiyat=item.birim_fiyat
                )
            
            # Sepeti temizle
            sepet.kalemler.all().delete()
            
        else:
            # Misafir kullanıcı için session sepetini kullan
            guest_cart_items = get_guest_cart_items(request)
            sepet_toplam = get_guest_cart_total(request)
            sepet_toplam_decimal = Decimal(str(sepet_toplam))
            
            if not guest_cart_items:
                messages.error(request, 'Sepetiniz boş!')
                return redirect('shop:checkout')
            
            # Misafir bilgilerini al
            ad_soyad = request.POST.get('ad_soyad')
            telefon = request.POST.get('telefon')
            email = request.POST.get('email')
            il = request.POST.get('il')
            ilce = request.POST.get('ilce')
            mahalle = request.POST.get('mahalle', '')
            cadde_sokak = request.POST.get('cadde_sokak', '')
            bina_no = request.POST.get('bina_no', '')
            daire_no = request.POST.get('daire_no', '')
            adres_notu = request.POST.get('adres_notu', '')
            
            if not all([ad_soyad, telefon, email, il, ilce]):
                messages.error(request, 'Lütfen tüm gerekli alanları doldurun!')
                return redirect('shop:checkout')
            
            # KARGO BİLGİLERİ (Misafir kullanıcı için) - Varsayılan kargo firmasını kullan
            kargo_firmasi = get_default_cargo_company()
            kargo_ucreti = Decimal('0')
            
            if kargo_firmasi:
                kargo_ucreti = Decimal(str(kargo_firmasi.kargo_ucreti_hesapla(sepet_toplam_decimal)))
            
            # Toplam fiyat hesapla (sepet + kargo)
            toplam_fiyat = sepet_toplam_decimal + kargo_ucreti
            
            # Misafir adres bilgilerini birleştir
            adres_metni = f"{ad_soyad}\n{telefon}\n{il}, {ilce}"
            if mahalle:
                adres_metni += f"\n{mahalle}"
            if cadde_sokak:
                adres_metni += f" {cadde_sokak}"
            if bina_no:
                adres_metni += f" {bina_no}"
            if daire_no:
                adres_metni += f"/{daire_no}"
            if adres_notu:
                adres_metni += f"\n{adres_notu}"
            
            # Sipariş oluştur (misafir kullanıcı için)
            siparis = Siparis.objects.create(
                kullanici=None,  # Misafir kullanıcı
                toplam_fiyat=toplam_fiyat,  # Kargo dahil toplam
                adres=adres_metni,
                misafir_email=email,
                misafir_telefon=telefon,
                misafir_ad_soyad=ad_soyad,
                kargo_firma=kargo_firmasi
            )
            
            # Session sepet kalemlerini sipariş kalemlerine dönüştür ve stok azalt
            for item in guest_cart_items:
                # Stok kontrolü ve azaltma
                if not item['urun'].stok_azalt(item['miktar']):
                    messages.error(request, f'{item["urun"].ad} ürünü için yeterli stok yok!')
                    return redirect('shop:checkout')
                
                SiparisKalemi.objects.create(
                    siparis=siparis,
                    urun=item['urun'],
                    miktar=item['miktar'],
                    fiyat=Decimal(str(item['birim_fiyat']))
                )
            
            # Session sepetini temizle ve sipariş ID'sini kaydet
            request.session['guest_cart'] = {}
            request.session['recent_order_id'] = siparis.id
            request.session.modified = True
        
        # Etiket ürünleri için otomatik etiket oluştur
        create_etiket_for_order(siparis)
        
        # Email bildirimi gönder
        try:
            from .email_utils import send_order_confirmation_email
            send_order_confirmation_email(siparis)
        except Exception as e:
            # Email hatası siparişi etkilemesin
            print(f"Email gönderme hatası: {str(e)}")
        
        messages.success(request, f'Siparişiniz başarıyla oluşturuldu! Sipariş No: #{siparis.id}')
        return redirect('shop:siparis_detay', siparis_id=siparis.id)
        
    except Exception as e:
        import traceback
        print(f"ERROR: {str(e)}")
        print(f"TRACEBACK: {traceback.format_exc()}")
        messages.error(request, f'Sipariş oluşturulurken bir hata oluştu: {str(e)}')
        return redirect('shop:checkout')


@login_required
def siparis_listesi(request):
    """Kullanıcının siparişleri"""
    siparisler = Siparis.objects.filter(kullanici=request.user).prefetch_related(
        'kalemler__urun__resimler',
        'kalemler__urun__etiket_kategori__fotograflar'
    ).order_by('-olusturulma_tarihi')
    
    context = {
        'siparisler': siparisler,
    }
    
    return render(request, 'shop/siparis_listesi.html', context)


def siparis_detay(request, siparis_id):
    """Sipariş detay sayfası - Hem authenticated hem misafir kullanıcılar için"""
    if request.user.is_authenticated:
        # Authenticated kullanıcı için
        siparis = get_object_or_404(Siparis, id=siparis_id, kullanici=request.user)
    else:
        # Misafir kullanıcı için - doğrudan erişim (güvenlik için session kontrolü)
        siparis = get_object_or_404(Siparis, id=siparis_id, kullanici=None)
        
        # Güvenlik: Sadece sipariş oluşturan misafir kullanıcı erişebilir
        # Session'da sipariş ID'si varsa erişim ver
        if 'recent_order_id' not in request.session or request.session['recent_order_id'] != siparis_id:
            messages.error(request, 'Bu siparişe erişim yetkiniz yok!')
            return redirect('shop:shop_home')
    
    siparis_items = siparis.kalemler.select_related('urun', 'urun__etiket_kategori').prefetch_related('urun__resimler', 'urun__etiket_kategori__fotograflar')
    
    context = {
        'siparis': siparis,
        'siparis_items': siparis_items,
    }

    return render(request, 'shop/siparis_detay.html', context)


def admin_siparis_detay(request, siparis_id):
    """Admin sipariş detay sayfası - Tüm siparişlere erişim"""
    siparis = get_object_or_404(Siparis, id=siparis_id)
    siparis_items = siparis.kalemler.select_related('urun', 'urun__etiket_kategori').prefetch_related('urun__resimler', 'urun__etiket_kategori__fotograflar')
    
    # Sipariş durum geçmişi
    durum_gecmisi = siparis.durum_gecmisi.all().order_by('-olusturulma_tarihi')
    
    # Bu sipariş için oluşturulan etiketleri getir
    # Sipariş tarihine yakın etiketleri bul (5 dakika içinde)
    from django.utils import timezone
    from datetime import timedelta
    siparis_tarihi = siparis.olusturulma_tarihi
    
    if siparis.kullanici:
        # Authenticated kullanıcı için etiketleri bul
        kullanici_adi = siparis.kullanici.get_full_name() or siparis.kullanici.username
        kayit_araligi = (siparis_tarihi - timedelta(minutes=5), siparis_tarihi + timedelta(minutes=5))
        etiketler = Etiket.objects.filter(
            musteri_adi__icontains=kullanici_adi[:10],  # Kısmi eşleşme
            olusturulma_tarihi__range=kayit_araligi
        ).order_by('-olusturulma_tarihi')
    else:
        # Misafir kullanıcı için etiketleri bul
        if siparis.misafir_ad_soyad:
            kayit_araligi = (siparis_tarihi - timedelta(minutes=5), siparis_tarihi + timedelta(minutes=5))
            etiketler = Etiket.objects.filter(
                musteri_adi__icontains=siparis.misafir_ad_soyad[:10],  # Kısmi eşleşme
                olusturulma_tarihi__range=kayit_araligi
            ).order_by('-olusturulma_tarihi')
        else:
            etiketler = []
    
    context = {
        'siparis': siparis,
        'siparis_items': siparis_items,
        'durum_gecmisi': durum_gecmisi,
        'etiketler': etiketler,
        'is_admin_view': True,
    }

    return render(request, 'shop/admin_siparis_detay.html', context)


def get_ilceler(request):
    """AJAX: İl seçildiğinde ilçeleri JSON olarak döndür"""
    from anahtarlik.dictionaries import Ilce

    il_id = request.GET.get('il_id')

    if il_id:
        ilceler = Ilce.objects.filter(il_id=il_id).order_by('ad').values('id', 'ad')
        return JsonResponse(list(ilceler), safe=False)

    return JsonResponse([], safe=False)


def get_mahalleler(request):
    """AJAX: İlçe seçildiğinde mahalleleri JSON olarak döndür"""
    from anahtarlik.dictionaries import Mahalle

    ilce_id = request.GET.get('ilce_id')

    if ilce_id:
        mahalleler = Mahalle.objects.filter(ilce_id=ilce_id).order_by('ad').values('id', 'ad')
        return JsonResponse(list(mahalleler), safe=False)

    return JsonResponse([], safe=False)


def calculate_cargo_ajax(request):
    """AJAX: Kargo ücreti hesaplama"""
    from shop.cart_utils import calculate_cargo_cost, get_cargo_options
    
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Sepet toplamını al
        if request.user.is_authenticated:
            sepet, created = Sepet.objects.get_or_create(kullanici=request.user)
            sepet_toplam = sepet.toplam_fiyat
        else:
            from shop.cart_utils import get_guest_cart_total
            sepet_toplam = get_guest_cart_total(request)
        
        # Kargo firması ID'sini al
        kargo_firmasi_id = request.GET.get('kargo_firmasi')
        
        if kargo_firmasi_id:
            # Belirli kargo firması için hesapla
            kargo_ucreti = calculate_cargo_cost(int(kargo_firmasi_id), sepet_toplam)
            toplam_fiyat = sepet_toplam + kargo_ucreti
            
            return JsonResponse({
                'success': True,
                'sepet_toplam': float(sepet_toplam),
                'kargo_ucreti': float(kargo_ucreti),
                'toplam_fiyat': float(toplam_fiyat),
                'kargo_ucretsiz': kargo_ucreti == 0
            })
        else:
            # Tüm kargo seçeneklerini döndür
            kargo_secenekleri = get_cargo_options(sepet_toplam)
            options = []
            
            for option in kargo_secenekleri:
                options.append({
                    'id': option['company'].id,
                    'ad': option['company'].ad,
                    'ucret': float(option['cost']),
                    'ucretsiz': option['is_free'],
                    'display_ucret': option['display_cost'],
                    'tahmini_sure': option['company'].tahmini_sure_gun,
                    'ucretsiz_limit': float(option['company'].ucretsiz_kargo_limiti) if option['company'].ucretsiz_kargo_limiti else None
                })
            
            return JsonResponse({
                'success': True,
                'sepet_toplam': float(sepet_toplam),
                'kargo_secenekleri': options
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def kargo_takip(request, siparis_id):
    """Kargo takip sayfası - Hem authenticated hem misafir kullanıcılar için"""
    if request.user.is_authenticated:
        # Authenticated kullanıcı için
        siparis = get_object_or_404(Siparis, id=siparis_id, kullanici=request.user)
    else:
        # Misafir kullanıcı için - email ile kontrol
        if request.method == 'POST':
            email = request.POST.get('email')
            telefon = request.POST.get('telefon')
            if email and telefon:
                siparis = get_object_or_404(Siparis, id=siparis_id, misafir_email=email, misafir_telefon=telefon)
            else:
                messages.error(request, 'Email ve telefon bilgilerini giriniz!')
                return render(request, 'shop/misafir_kargo_takip.html', {'siparis_id': siparis_id})
        else:
            # İlk kez sayfaya geliyorsa form göster
            return render(request, 'shop/misafir_kargo_takip.html', {'siparis_id': siparis_id})
    
    # Sipariş durum geçmişini getir
    durum_gecmisi = siparis.durum_gecmisi.all().order_by('olusturulma_tarihi')
    
    context = {
        'siparis': siparis,
        'durum_gecmisi': durum_gecmisi,
    }

    return render(request, 'shop/kargo_takip.html', context)


def get_user_type(user):
    """Kullanıcı tipini belirle"""
    if not user or not user.is_authenticated:
        return 'misafir'
    
    # Kullanıcı tiplerini kontrol et
    if hasattr(user, 'sahip'):
        return 'sahip'
    elif hasattr(user, 'veteriner_profili'):
        return 'veteriner'
    elif hasattr(user, 'petshop_profili'):
        return 'petshop'
    else:
        return 'normal'

@login_required
def admin_siparis_yonet(request):
    """Admin paneli - Gelişmiş sipariş yönetimi"""
    from django.contrib.auth.decorators import user_passes_test
    from shop.models import SiparisDurum, KargoFirma
    from django.utils import timezone
    from datetime import timedelta
    
    # Sadece staff kullanıcılar erişebilir
    if not request.user.is_staff:
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('shop:shop_home')
    
    # Filtreleme parametreleri
    durum_filtre = request.GET.get('durum', '')
    tarih_filtre = request.GET.get('tarih', '')
    kullanici_tipi_filtre = request.GET.get('kullanici_tipi', '')
    arama = request.GET.get('arama', '')
    
    # Siparişleri getir
    siparisler = (
        Siparis.objects
        .select_related('kullanici')
        .prefetch_related('kalemler__urun', 'durum_gecmisi')
        .annotate(user_order_count=Count('kullanici__siparis', distinct=True))
    )
    
    # Filtreleme
    if durum_filtre:
        siparisler = siparisler.filter(durum=durum_filtre)
    
    if tarih_filtre:
        if tarih_filtre == 'bugun':
            siparisler = siparisler.filter(olusturulma_tarihi__date=timezone.now().date())
        elif tarih_filtre == 'bu_hafta':
            start_date = timezone.now().date() - timedelta(days=7)
            siparisler = siparisler.filter(olusturulma_tarihi__date__gte=start_date)
        elif tarih_filtre == 'bu_ay':
            start_date = timezone.now().date().replace(day=1)
            siparisler = siparisler.filter(olusturulma_tarihi__date__gte=start_date)
    
    # Kullanıcı tipi filtreleme
    if kullanici_tipi_filtre:
        if kullanici_tipi_filtre == 'misafir':
            siparisler = siparisler.filter(kullanici__isnull=True)
        elif kullanici_tipi_filtre == 'sahip':
            siparisler = siparisler.filter(kullanici__sahip__isnull=False)
        elif kullanici_tipi_filtre == 'veteriner':
            siparisler = siparisler.filter(kullanici__veteriner_profili__isnull=False)
        elif kullanici_tipi_filtre == 'petshop':
            siparisler = siparisler.filter(kullanici__petshop_profili__isnull=False)
        elif kullanici_tipi_filtre == 'normal':
            siparisler = siparisler.filter(
                kullanici__isnull=False,
                kullanici__sahip__isnull=True,
                kullanici__veteriner_profili__isnull=True,
                kullanici__petshop_profili__isnull=True
            )
    
    if arama:
        siparisler = siparisler.filter(
            Q(id__icontains=arama) |
            Q(kullanici__username__icontains=arama) |
            Q(misafir_ad_soyad__icontains=arama) |
            Q(misafir_email__icontains=arama)
        )
    
    # Sıralama
    siralama = request.GET.get('siralama', '-olusturulma_tarihi')
    siparisler = siparisler.order_by(siralama)
    
    # Sayfalama
    from django.core.paginator import Paginator
    paginator = Paginator(siparisler, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Kullanıcı sipariş sayısı anotasyonunu misafir kullanıcılar için düzelt
    for siparis in page_obj:
        if siparis.kullanici:
            siparis.user_order_count = siparis.user_order_count or 0
        else:
            siparis.user_order_count = 1
    
    # İstatistikler
    toplam_siparis = Siparis.objects.count()
    bekleyen_siparis = Siparis.objects.filter(durum='bekliyor').count()
    odendi_siparis = Siparis.objects.filter(durum='odendi').count()
    kargoda_siparis = Siparis.objects.filter(durum='kargoda').count()
    teslim_edildi_siparis = Siparis.objects.filter(durum='teslim_edildi').count()
    
    # Ürün tipi istatistikleri
    pet_urun_siparisleri = Siparis.objects.filter(
        kalemler__urun__urun_tipi='normal'
    ).distinct().count()
    
    qr_urun_siparisleri = Siparis.objects.filter(
        kalemler__urun__urun_tipi='etiket'
    ).distinct().count()
    
    # Aynı kullanıcıdan gelen çoklu siparişler
    coklu_siparis_kullanicilar = Siparis.objects.filter(
        kullanici__isnull=False
    ).values('kullanici').annotate(
        siparis_sayisi=Count('id')
    ).filter(siparis_sayisi__gt=1).count()
    
    # En çok sipariş veren kullanıcılar
    en_cok_siparis_veren = Siparis.objects.filter(
        kullanici__isnull=False
    ).values(
        'kullanici__username', 
        'kullanici__first_name', 
        'kullanici__last_name'
    ).annotate(
        siparis_sayisi=Count('id')
    ).order_by('-siparis_sayisi')[:5]
    
    # Günlük satış
    bugun_satis = Siparis.objects.filter(
        olusturulma_tarihi__date=timezone.now().date(),
        durum__in=['odendi', 'hazirlaniyor', 'kargoda', 'teslim_edildi']
    ).aggregate(total=Sum('toplam_fiyat'))['total'] or 0
    
    # Haftalık satış
    hafta_baslangic = timezone.now().date() - timedelta(days=7)
    haftalik_satis = Siparis.objects.filter(
        olusturulma_tarihi__date__gte=hafta_baslangic,
        durum__in=['odendi', 'hazirlaniyor', 'kargoda', 'teslim_edildi']
    ).aggregate(total=Sum('toplam_fiyat'))['total'] or 0
    
    # Durum güncelleme
    if request.method == 'POST':
        # Toplu işlem kontrolü
        bulk_action = request.POST.get('bulk_action')
        selected_orders = request.POST.get('selected_orders')
        
        if bulk_action and selected_orders:
            # Toplu işlem
            order_ids = selected_orders.split(',')
            updated_count = 0
            
            for order_id in order_ids:
                try:
                    siparis = Siparis.objects.get(id=order_id)
                    
                    # Yeni durum kaydı oluştur
                    durum_kaydi = SiparisDurum.objects.create(
                        siparis=siparis,
                        durum=bulk_action,
                        aciklama=f'Toplu işlem ile {bulk_action} olarak işaretlendi'
                    )
                    
                    # Sipariş durumunu güncelle
                    siparis.durum = bulk_action
                    siparis.save()
                    
                    # Eğer durum "ödendi" ise etiket oluştur
                    if bulk_action == 'odendi':
                        create_etiket_for_order(siparis)
                    
                    updated_count += 1
                    
                except Siparis.DoesNotExist:
                    continue
            
            messages.success(request, f'{updated_count} sipariş başarıyla güncellendi!')
            return redirect('shop:admin_siparis_yonet')
        
        # Tekil işlem
        siparis_id = request.POST.get('siparis_id')
        yeni_durum = request.POST.get('durum')
        aciklama = request.POST.get('aciklama', '')
        kargo_takip_no = request.POST.get('kargo_takip_no', '')
        kargo_firma_id = request.POST.get('kargo_firma_id', '')
        
        if siparis_id and yeni_durum:
            try:
                siparis = Siparis.objects.get(id=siparis_id)
                
                # Yeni durum kaydı oluştur
                durum_kaydi = SiparisDurum.objects.create(
                    siparis=siparis,
                    durum=yeni_durum,
                    aciklama=aciklama
                )
                
                # Kargo takip numarası ekle
                if kargo_takip_no:
                    durum_kaydi.kargo_takip_no = kargo_takip_no
                    durum_kaydi.save()
                    siparis.kargo_takip_no = kargo_takip_no
                
                # Kargo firması ekle
                if kargo_firma_id:
                    try:
                        kargo_firma = KargoFirma.objects.get(id=kargo_firma_id)
                        siparis.kargo_firma = kargo_firma
                    except KargoFirma.DoesNotExist:
                        pass
                
                # Sipariş durumunu güncelle
                siparis.durum = yeni_durum
                siparis.save()
                
                # Eğer durum "ödendi" ise etiket oluştur
                if yeni_durum == 'odendi':
                    create_etiket_for_order(siparis)
                
                # Email bildirimleri gönder
                try:
                    from .email_utils import send_shipping_notification_email, send_order_cancellation_email
                    
                    if yeni_durum == 'kargoda':
                        # Kargo gönderildi email'i
                        send_shipping_notification_email(siparis)
                    elif yeni_durum == 'iptal':
                        # Sipariş iptal email'i
                        send_order_cancellation_email(siparis, aciklama)
                except Exception as e:
                    # Email hatası sipariş güncellemesini etkilemesin
                    print(f"Email gönderme hatası: {str(e)}")
                
                messages.success(request, f'Sipariş #{siparis_id} durumu "{yeni_durum}" olarak güncellendi.')
                
            except Siparis.DoesNotExist:
                messages.error(request, 'Sipariş bulunamadı!')
    
    # Kargo firmaları
    kargo_firmalari = KargoFirma.objects.filter(aktif=True)
    
    # Kullanıcı tipi seçenekleri
    kullanici_tipi_secenekleri = [
        ('', 'Tüm Kullanıcılar'),
        ('misafir', 'Misafir Kullanıcılar'),
        ('sahip', 'QR Sahipleri'),
        ('veteriner', 'Veterinerler'),
        ('petshop', 'Petshop Sahipleri'),
        ('normal', 'Normal Kullanıcılar'),
    ]
    
    context = {
        'page_obj': page_obj,
        'siparisler': page_obj,
        'durum_secenekleri': SiparisDurum.DURUM_CHOICES,
        'kargo_firmalari': kargo_firmalari,
        'kullanici_tipi_secenekleri': kullanici_tipi_secenekleri,
        'durum_filtre': durum_filtre,
        'tarih_filtre': tarih_filtre,
        'kullanici_tipi_filtre': kullanici_tipi_filtre,
        'arama': arama,
        'siralama': siralama,
        # İstatistikler
        'toplam_siparis': toplam_siparis,
        'bekleyen_siparis': bekleyen_siparis,
        'odendi_siparis': odendi_siparis,
        'kargoda_siparis': kargoda_siparis,
        'teslim_edildi_siparis': teslim_edildi_siparis,
        'bugun_satis': bugun_satis,
        'haftalik_satis': haftalik_satis,
        # Yeni istatistikler
        'pet_urun_siparisleri': pet_urun_siparisleri,
        'qr_urun_siparisleri': qr_urun_siparisleri,
        'coklu_siparis_kullanicilar': coklu_siparis_kullanicilar,
        'en_cok_siparis_veren': en_cok_siparis_veren,
    }
    
    return render(request, 'shop/admin_siparis_yonet.html', context)


@login_required
def admin_kargo_yonet(request):
    """Admin paneli - Kargo firması yönetimi"""
    from shop.models import KargoFirma
    
    # Sadece staff kullanıcılar erişebilir
    if not request.user.is_staff:
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('shop:shop_home')
    
    if request.method == 'POST':
        if 'kargo_ekle' in request.POST:
            # Yeni kargo firması ekle
            ad = request.POST.get('ad')
            sabit_ucret = request.POST.get('sabit_ucret')
            ucretsiz_kargo_limiti = request.POST.get('ucretsiz_kargo_limiti', '')
            tahmini_sure_gun = request.POST.get('tahmini_sure_gun', 3)
            sira = request.POST.get('sira', 0)
            
            if ad and sabit_ucret:
                try:
                    KargoFirma.objects.create(
                        ad=ad,
                        sabit_ucret=sabit_ucret,
                        ucretsiz_kargo_limiti=ucretsiz_kargo_limiti if ucretsiz_kargo_limiti else None,
                        tahmini_sure_gun=tahmini_sure_gun,
                        sira=sira
                    )
                    messages.success(request, f'Kargo firması "{ad}" başarıyla eklendi.')
                except Exception as e:
                    messages.error(request, f'Hata: {str(e)}')
        
        elif 'kargo_guncelle' in request.POST:
            # Kargo firması güncelle
            firma_id = request.POST.get('firma_id')
            ad = request.POST.get('ad')
            sabit_ucret = request.POST.get('sabit_ucret')
            ucretsiz_kargo_limiti = request.POST.get('ucretsiz_kargo_limiti', '')
            tahmini_sure_gun = request.POST.get('tahmini_sure_gun', 3)
            sira = request.POST.get('sira', 0)
            aktif = request.POST.get('aktif') == 'on'
            
            if firma_id and ad and sabit_ucret:
                try:
                    firma = KargoFirma.objects.get(id=firma_id)
                    firma.ad = ad
                    firma.sabit_ucret = sabit_ucret
                    firma.ucretsiz_kargo_limiti = ucretsiz_kargo_limiti if ucretsiz_kargo_limiti else None
                    firma.tahmini_sure_gun = tahmini_sure_gun
                    firma.sira = sira
                    firma.aktif = aktif
                    firma.save()
                    messages.success(request, f'Kargo firması "{ad}" başarıyla güncellendi.')
                except KargoFirma.DoesNotExist:
                    messages.error(request, 'Kargo firması bulunamadı!')
                except Exception as e:
                    messages.error(request, f'Hata: {str(e)}')
        
        elif 'kargo_sil' in request.POST:
            # Kargo firması sil
            firma_id = request.POST.get('firma_id')
            if firma_id:
                try:
                    firma = KargoFirma.objects.get(id=firma_id)
                    firma.delete()
                    messages.success(request, f'Kargo firması "{firma.ad}" silindi.')
                except KargoFirma.DoesNotExist:
                    messages.error(request, 'Kargo firması bulunamadı!')
    
    # Kargo firmalarını getir
    kargo_firmalari = KargoFirma.objects.all().order_by('sira', 'ad')
    
    context = {
        'kargo_firmalari': kargo_firmalari,
    }
    
    return render(request, 'shop/admin_kargo_yonet.html', context)
