# petshop/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse, Http404
from django.db.models import Q, Avg, Count
from django.utils import timezone
from django.urls import reverse
from datetime import date, timedelta

from .models import PetShop, SiparisIstemi
from .forms import PetShopWebForm, PetShopProfilForm, PetShopHesapForm
from etiket.models import Etiket, KANAL_SHOP
from anahtarlik.dictionaries import Ilce
from ilan.models import KrediHareketi


@login_required
def petshop_paneli(request):
    # PetShop profili kontrolü - otomatik oluşturma kaldırıldı
    if not hasattr(request.user, 'petshop_profili'):
        from django.contrib import messages
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok. PetShop profili bulunamadı.')
        return redirect('anahtarlik:kullanici_paneli')
    
    petshop = request.user.petshop_profili


    tahsis_qs = Etiket.objects.filter(satici_petshop=petshop, kanal=KANAL_SHOP).order_by("-tahsis_tarihi", "-olusturulma_tarihi")
    satilan_qs = tahsis_qs.filter(aktif=True)
    siparis_qs = SiparisIstemi.objects.filter(petshop=petshop).order_by('-talep_tarihi')

    # Kredi bakiyesi
    from django.db.models import Sum
    kredi_bakiye = KrediHareketi.objects.filter(kullanici=request.user).aggregate(
        toplam=Sum('miktar')
    )['toplam'] or 0
    
    context = {
        "petshop": petshop,
        "tahsis_sayisi": tahsis_qs.count(),
        "satis_sayisi": satilan_qs.count(),
        "kalan_envanter": petshop.kalan_envanter,
        "tahsis_edilenler": tahsis_qs[:5],
        "satilanlar": satilan_qs[:5],
        "siparis_istekleri": siparis_qs[:5],
        "kredi_bakiye": kredi_bakiye,
    }
    return render(request, "petshop/panel.html", context)


# ==================== DEĞERLENDİRME YÖNETİMİ ====================



# ==================== ETİKET LİSTELERİ ====================

@login_required
def tahsis_listesi(request):
    petshop = getattr(request.user, 'petshop_profili', None)
    if petshop is None or not petshop.il or not petshop.adres_detay:
        return redirect("petshop:petshop_profil_tamamla")
    qs = Etiket.objects.filter(satici_petshop=petshop, kanal=KANAL_SHOP).order_by("-tahsis_tarihi", "-olusturulma_tarihi")
    page_obj = Paginator(qs, 25).get_page(request.GET.get("page"))
    return render(request, "petshop/liste_tahsis.html", {"page_obj": page_obj})

@login_required
def satis_listesi(request):
    petshop = getattr(request.user, 'petshop_profili', None)
    if petshop is None or not petshop.il or not petshop.adres_detay:
        return redirect("petshop:petshop_profil_tamamla")
    qs = Etiket.objects.filter(satici_petshop=petshop, kanal=KANAL_SHOP, aktif=True).order_by("-first_activated_at", "-aktiflestirme_tarihi")
    page_obj = Paginator(qs, 25).get_page(request.GET.get("page"))
    return render(request, "petshop/liste_satis.html", {"page_obj": page_obj})

@login_required
def siparis_listesi(request):
    petshop = getattr(request.user, 'petshop_profili', None)
    if petshop is None or not petshop.il or not petshop.adres_detay:
        return redirect("petshop:petshop_profil_tamamla")
    qs = SiparisIstemi.objects.filter(petshop=petshop).order_by('-talep_tarihi')
    page_obj = Paginator(qs, 25).get_page(request.GET.get("page"))
    return render(request, "petshop/liste_siparis.html", {"page_obj": page_obj})


# ==================== KREDİ DURUMU ====================

@login_required
def kredi_durumu(request):
    """Kredi hareketleri listesi"""
    petshop = getattr(request.user, 'petshop_profili', None)
    if petshop is None:
        return redirect("petshop:petshop_profil_tamamla")
    
    # Kredi hareketleri (user bazlı)
    hareketler = KrediHareketi.objects.filter(
        kullanici=request.user
    ).order_by('-tarih')
    
    page_obj = Paginator(hareketler, 25).get_page(request.GET.get("page"))
    
    # Toplam bakiye
    from django.db.models import Sum
    kredi_bakiye = KrediHareketi.objects.filter(
        kullanici=request.user
    ).aggregate(Sum('miktar'))['miktar__sum'] or 0
    
    return render(request, "petshop/kredi_durumu.html", {
        "page_obj": page_obj,
        "kredi_bakiye": kredi_bakiye,
    })


# ==================== PROFİL TAMAMLAMA ====================

@login_required
def petshop_profilim(request):
    """PetShop profil görüntüleme sayfası"""
    from .models import SiparisIstemi
    
    petshop = getattr(request.user, 'petshop_profili', None)
    if petshop is None:
        messages.error(request, "PetShop profiliniz bulunamadı.")
        return redirect('anahtarlik:ev')
    
    # İstatistikler
    bekleyen_siparis = SiparisIstemi.objects.filter(petshop=petshop, onaylandi=False).count()
    tamamlanan_siparis = SiparisIstemi.objects.filter(petshop=petshop, onaylandi=True).count()
    
    # Hizmetler listesi
    hizmetler = []
    if petshop.pet_kuafor:
        hizmetler.append('Pet Kuaför')
    if petshop.pet_hotel:
        hizmetler.append('Pet Otel')
    if petshop.pet_taksi:
        hizmetler.append('Pet Taksi')
    if petshop.pet_egitim:
        hizmetler.append('Eğitim')
    if petshop.pet_bakim:
        hizmetler.append('Bakım')
    
    context = {
        'petshop': petshop,
        'bekleyen_siparis': bekleyen_siparis,
        'tamamlanan_siparis': tamamlanan_siparis,
        'hizmetler': hizmetler,
    }
    
    return render(request, 'petshop/petshop_profilim.html', context)


@login_required
def hesap_ayarlari(request):
    """PetShop hesap ayarları - şifre değiştirme ve kullanıcı bilgileri"""
    petshop = getattr(request.user, 'petshop_profili', None)
    if petshop is None:
        messages.error(request, "PetShop profiliniz bulunamadı.")
        return redirect('anahtarlik:ev')
    
    if request.method == 'POST':
        form = PetShopHesapForm(request.POST, instance=request.user)
        if form.is_valid():
            # Şifre değiştirildi mi kontrol et
            new_password = form.cleaned_data.get('new_password1')
            if new_password:
                # Şifre değiştirildi, flag'i güncelle
                petshop.ilk_giris_sifre_degistirildi = True
                petshop.save()
            form.save()
            if new_password:
                messages.success(request, "Şifreniz başarıyla değiştirildi! Artık paneline erişebilirsiniz.")
                return redirect('petshop:petshop_paneli')
            messages.success(request, "Hesap bilgileriniz başarıyla güncellendi!")
            return redirect('petshop:hesap_ayarlari')
        else:
            messages.error(request, "Lütfen form hatalarını düzeltin.")
    else:
        form = PetShopHesapForm(instance=request.user)
    
    return render(request, 'petshop/hesap_ayarlari.html', {
        'form': form,
        'petshop': petshop
    })


@login_required
def profil_duzenle(request):
    """PetShop temel profil bilgilerini düzenle"""
    from anahtarlik.dictionaries import Il, Ilce
    
    petshop = getattr(request.user, 'petshop_profili', None)
    if petshop is None:
        messages.error(request, "PetShop profiliniz bulunamadı.")
        return redirect('anahtarlik:ev')
    
    if request.method == 'POST':
        form = PetShopProfilForm(request.POST, instance=petshop)
        if form.is_valid():
            form.save()
            messages.success(request, "Profiliniz başarıyla güncellendi!")
            return redirect('petshop:profil_duzenle')
        else:
            messages.error(request, "Lütfen form hatalarını düzeltin.")
    else:
        form = PetShopProfilForm(instance=petshop)
    
    # İl listesi
    iller = Il.objects.all().order_by('ad')
    
    # İlçe listesi (eğer il seçiliyse)
    ilceler = []
    if petshop.il:
        ilceler = Ilce.objects.filter(il=petshop.il).order_by('ad')
    
    return render(request, 'petshop/profil_duzenle.html', {
        'form': form,
        'petshop': petshop,
        'iller': iller,
        'ilceler': ilceler,
    })


@login_required
def petshop_profil_tamamla(request):
    """
    PetShop profil tamamlama sayfası.
    İl, ilçe ve adres bilgilerinin girilmesi zorunlu.
    """
    # PetShop profili var mı kontrol et
    try:
        petshop = request.user.petshop_profili
    except:
        messages.error(request, "PetShop profiliniz bulunamadı.")
        return redirect('anahtarlik:ev')
    
    # Profil zaten tamam mı?
    if petshop.il and petshop.ilce and petshop.adres_detay:
        messages.info(request, "Profiliniz zaten tamamlanmış.")
        return redirect('petshop:petshop_paneli')
    
    if request.method == 'POST':
        # Form verilerini al
        ad = request.POST.get('ad', '').strip()
        telefon = request.POST.get('telefon', '').strip()
        il_id = request.POST.get('il')
        ilce_id = request.POST.get('ilce')
        adres_detay = request.POST.get('adres_detay', '').strip()
        
        # Validasyon
        errors = []
        if not ad:
            errors.append("Ad alanı zorunludur.")
        if not il_id:
            errors.append("İl seçimi zorunludur.")
        if not ilce_id:
            errors.append("İlçe seçimi zorunludur.")
        if not adres_detay:
            errors.append("Adres detayı zorunludur.")
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Güncelleme yap
            try:
                from anahtarlik.dictionaries import Il, Ilce
                
                petshop.ad = ad
                if telefon:
                    petshop.telefon = telefon
                petshop.il = Il.objects.get(id=il_id)
                petshop.ilce = Ilce.objects.get(id=ilce_id)
                petshop.adres_detay = adres_detay
                petshop.save()
                
                messages.success(request, "Profiliniz başarıyla tamamlandı!")
                return redirect('petshop:petshop_paneli')
            except Exception as e:
                messages.error(request, f"Profil kaydedilirken hata oluştu: {str(e)}")
    
    # İl ve İlçe listelerini context'e ekle
    from anahtarlik.dictionaries import Il, Ilce
    iller = Il.objects.all().order_by('ad')
    
    # Eğer mevcut il varsa o ile ait ilçeleri getir
    if petshop.il:
        ilceler = Ilce.objects.filter(il=petshop.il).order_by('ad')
    else:
        ilceler = Ilce.objects.none()
    
    context = {
        'petshop': petshop,
        'iller': iller,
        'ilceler': ilceler,
    }
    
    return render(request, 'petshop/profil_tamamla.html', context)


# AJAX endpoints for dynamic form loading
def districts_for_city(request):
    """İlçe listesi AJAX endpoint"""
    from core.views import districts_for_province
    return districts_for_province(request)


# ==================== WEB SAYFASI ====================

def web_sayfasi_gorunum(request, slug):
    petshop = get_object_or_404(PetShop, web_slug=slug, web_aktif=True)
    resimler = []
    if petshop.web_resim1: resimler.append(petshop.web_resim1)
    if petshop.web_resim2: resimler.append(petshop.web_resim2)
    if petshop.web_resim3: resimler.append(petshop.web_resim3)
    
    # Sosyal medya URL'lerini hazırla
    instagram_url = None
    if petshop.instagram:
        if 'http' in petshop.instagram:
            instagram_url = petshop.instagram
        else:
            instagram_url = f"https://instagram.com/{petshop.instagram.replace('@', '')}"
    
    facebook_url = None
    if petshop.facebook:
        if 'http' in petshop.facebook:
            facebook_url = petshop.facebook
        else:
            facebook_url = f"https://facebook.com/{petshop.facebook}"
    
    return render(request, 'petshop/web_public.html', {
        "petshop": petshop, 
        "resimler": resimler,
        "instagram_url": instagram_url,
        "facebook_url": facebook_url,
    })

def web_sayfasi_gorunum_legacy(request, petshop_id):
    petshop = get_object_or_404(PetShop, id=petshop_id, web_aktif=True)
    if petshop.web_slug:
        return redirect('petshop:web_sayfasi_gorunum', slug=petshop.web_slug, permanent=True)
    raise Http404()

@login_required
def web_sayfasi_duzenle(request):
    from .forms import PetShopWebForm
    petshop = getattr(request.user, 'petshop_profili', None)
    if not petshop:
        messages.error(request, "PetShop profili bulunamadı.")
        return redirect('petshop:petshop_paneli')
    
    # Web slug yoksa bilgilendirme mesajı hazırla
    slug_yok_mesaji = None
    if not petshop.web_slug:
        slug_yok_mesaji = (
            "Web sayfanız için bir URL adresi oluşturmanız gerekiyor. "
            "Aşağıdaki 'Web Sayfası URL Adresi' alanına istediğiniz adresi girebilirsiniz. "
            "Boş bırakırsanız, başlığınızdan otomatik oluşturulacaktır."
        )
    
    if request.method == 'POST':
        form = PetShopWebForm(request.POST, request.FILES, instance=petshop)
        if form.is_valid():
            petshop = form.save()
            messages.success(request, "Web sayfanız başarıyla güncellendi!")
            
            # Slug oluşturulduysa bilgilendir
            if petshop.web_slug:
                from django.urls import reverse
                web_url = request.build_absolute_uri(
                    reverse('petshop:web_sayfasi_gorunum', kwargs={'slug': petshop.web_slug})
                )
                messages.info(
                    request, 
                    f"Web sayfanızın URL adresi: {petshop.web_slug}. "
                    f"Sayfanızı görüntülemek için: {web_url}"
                )
            
            return redirect('petshop:web_sayfasi_duzenle')
        else:
            # Form hatalarını kullanıcı dostu şekilde göster
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{form.fields[field].label if field in form.fields else field}: {error}")
            
            if error_messages:
                messages.error(request, "Lütfen form hatalarını düzeltin:")
                for msg in error_messages[:3]:  # İlk 3 hatayı göster
                    messages.error(request, f"  • {msg}")
            else:
                messages.error(request, "Lütfen form hatalarını düzeltin.")
    else:
        form = PetShopWebForm(instance=petshop)
    
    gunler = [
        ('pazartesi', 'Pazartesi'),
        ('sali', 'Salı'),
        ('carsamba', 'Çarşamba'),
        ('persembe', 'Perşembe'),
        ('cuma', 'Cuma'),
        ('cumartesi', 'Cumartesi'),
        ('pazar', 'Pazar'),
    ]
    
    return render(request, 'petshop/web_form.html', {
        "petshop": petshop, 
        "form": form,
        "gunler": gunler,
        "slug_yok_mesaji": slug_yok_mesaji
    })
