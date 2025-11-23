# shop/cart_utils.py - Session tabanlı sepet yardımcı fonksiyonları
from shop.models import Urun, Sepet, SepetKalemi, KargoFirma
from django.contrib import messages
from decimal import Decimal

def get_guest_cart(request):
    """Misafir kullanıcının session sepetini al"""
    if 'guest_cart' not in request.session:
        request.session['guest_cart'] = {}
    return request.session['guest_cart']

def add_to_guest_cart(request, urun_id, miktar=1):
    """Misafir kullanıcının sepetine ürün ekle"""
    guest_cart = get_guest_cart(request)
    
    urun_id = str(urun_id)
    if urun_id in guest_cart:
        guest_cart[urun_id] += miktar
    else:
        guest_cart[urun_id] = miktar
    
    request.session.modified = True
    return True

def remove_from_guest_cart(request, urun_id):
    """Misafir kullanıcının sepetinden ürün çıkar"""
    guest_cart = get_guest_cart(request)
    urun_id = str(urun_id)
    
    if urun_id in guest_cart:
        del guest_cart[urun_id]
        request.session.modified = True
        return True
    return False

def update_guest_cart_item(request, urun_id, miktar):
    """Misafir kullanıcının sepetindeki ürün miktarını güncelle"""
    guest_cart = get_guest_cart(request)
    urun_id = str(urun_id)
    
    if miktar <= 0:
        return remove_from_guest_cart(request, urun_id)
    
    if urun_id in guest_cart:
        guest_cart[urun_id] = miktar
        request.session.modified = True
        return True
    return False

def get_guest_cart_items(request):
    """Misafir kullanıcının sepet öğelerini al - Template ile uyumlu format"""
    guest_cart = get_guest_cart(request)
    cart_items = []

    # Tüm ürün ID'lerini topla
    urun_ids = list(guest_cart.keys())

    if urun_ids:
        # Etiket kategorilerini prefetch et
        urunler = Urun.objects.filter(
            id__in=urun_ids,
            aktif=True
        ).select_related('etiket_kategori').prefetch_related(
            'resimler',
            'etiket_kategori__fotograflar'
        )

        # Ürünleri dict'e çevir
        urun_dict = {str(urun.id): urun for urun in urunler}

        for urun_id, miktar in guest_cart.items():
            if urun_id in urun_dict:
                urun = urun_dict[urun_id]

                # Misafir kullanıcılar için fiyat hesapla (her zaman normal fiyat, bayi olamazlar)
                # İndirimli fiyat varsa onu kullan, yoksa normal fiyat
                birim_fiyat = float(urun.indirimli_fiyat) if urun.indirimli_fiyat else float(urun.fiyat)

                cart_items.append({
                    'id': int(urun_id),  # Template'de item.id olarak kullanılıyor
                    'urun': urun,
                    'miktar': miktar,
                    'birim_fiyat': birim_fiyat,  # SepetKalemi ile uyumlu
                    'subtotal': birim_fiyat * miktar,  # SepetKalemi ile uyumlu
                    'toplam_fiyat': birim_fiyat * miktar,  # Geriye uyumluluk için
                })
            else:
                # Ürün artık yoksa sepetten çıkar
                remove_from_guest_cart(request, urun_id)

    return cart_items

def get_guest_cart_total(request):
    """Misafir kullanıcının sepet toplamını hesapla"""
    cart_items = get_guest_cart_items(request)
    return sum(item['subtotal'] for item in cart_items)

def get_guest_cart_count(request):
    """Misafir kullanıcının sepet ürün sayısını hesapla"""
    cart_items = get_guest_cart_items(request)
    return sum(item['miktar'] for item in cart_items)

def merge_guest_cart_to_user(request, user):
    """Login olduğunda session sepetini kullanıcının DB sepetine aktar"""
    guest_cart_items = get_guest_cart_items(request)
    
    if not guest_cart_items:
        return
    
    # Kullanıcının sepetini al veya oluştur
    sepet, created = Sepet.objects.get_or_create(kullanici=user)
    
    # Session sepetindeki ürünleri DB sepetine aktar
    for item in guest_cart_items:
        sepet_kalemi, created = SepetKalemi.objects.get_or_create(
            sepet=sepet,
            urun=item['urun'],
            defaults={'miktar': item['miktar'], 'birim_fiyat': Decimal(str(item['birim_fiyat']))}
        )
        
        if not created:
            # Aynı ürün varsa miktarı artır
            sepet_kalemi.miktar += item['miktar']
        # Kullanıcı tipine göre fiyatı yeniden hesapla
        yeni_fiyat = Decimal(str(sepet_kalemi.calculate_birim_fiyat()))
        if sepet_kalemi.birim_fiyat != yeni_fiyat:
            sepet_kalemi.birim_fiyat = yeni_fiyat
        sepet_kalemi.save(update_fields=['miktar', 'birim_fiyat'])
    
    # Session sepetini temizle
    request.session['guest_cart'] = {}
    request.session.modified = True


# ============= KARGO HESAPLAMA FONKSİYONLARI =============

def get_available_cargo_companies():
    """Aktif kargo firmalarını getir"""
    return KargoFirma.objects.filter(aktif=True).order_by('sira', 'ad')

def calculate_cargo_cost(cargo_company_id, order_total):
    """Kargo ücretini hesapla"""
    try:
        cargo_company = KargoFirma.objects.get(id=cargo_company_id, aktif=True)
        return float(cargo_company.kargo_ucreti_hesapla(order_total))
    except KargoFirma.DoesNotExist:
        return 0.0

def get_default_cargo_company():
    """Varsayılan kargo firmasını getir (en üstteki aktif firma)"""
    return get_available_cargo_companies().first()

def get_cargo_options(order_total):
    """Kargo seçeneklerini getir (fiyat hesaplamalı)"""
    cargo_companies = get_available_cargo_companies()
    options = []
    
    for company in cargo_companies:
        cost = float(company.kargo_ucreti_hesapla(order_total))
        options.append({
            'company': company,
            'cost': cost,
            'is_free': cost == 0,
            'display_cost': 'Ücretsiz' if cost == 0 else f'₺{cost:.2f}'
        })
    
    return options

def calculate_order_total_with_cargo(cart_total, cargo_company_id=None):
    """Sepet toplamı + kargo ücreti hesapla"""
    # Tip dönüşümü - Decimal'i float'a çevir
    cart_total = float(cart_total)
    
    if cargo_company_id:
        cargo_cost = calculate_cargo_cost(cargo_company_id, cart_total)
    else:
        # Varsayılan kargo firması kullan
        default_company = get_default_cargo_company()
        if default_company:
            cargo_cost = default_company.kargo_ucreti_hesapla(cart_total)
        else:
            cargo_cost = 0
    
    # Kargo ücretini de float'a çevir
    cargo_cost = float(cargo_cost)
    
    return {
        'cart_total': cart_total,
        'cargo_cost': cargo_cost,
        'total': cart_total + cargo_cost
    }



