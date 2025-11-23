# veteriner/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q, Avg, Count
from django.utils import timezone
from datetime import date, timedelta

from .models import Veteriner, SiparisIstemi, VeterinerHizmet, VeterinerDegerlendirme, Randevu
from .forms import VeterinerDegerlendirmeForm, VeterinerProfilForm, VeterinerHesapForm
from etiket.models import Etiket, KANAL_VET
from anahtarlik.dictionaries import Ilce




@login_required
def veteriner_paneli(request):
    # Veteriner profili kontrolü - otomatik oluşturma kaldırıldı
    if not hasattr(request.user, 'veteriner_profili'):
        from django.contrib import messages
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok. Veteriner profili bulunamadı.')
        return redirect('anahtarlik:kullanici_paneli')
    
    vet = request.user.veteriner_profili


    tahsis_qs = Etiket.objects.filter(satici_veteriner=vet, kanal=KANAL_VET).order_by("-tahsis_tarihi", "-olusturulma_tarihi")
    satilan_qs = tahsis_qs.filter(aktif=True)
    siparis_qs = SiparisIstemi.objects.filter(veteriner=vet).order_by('-talep_tarihi')


    # Danışman olduğu sahipler
    danisman_oldugu_sahipler = vet.danisman_oldugu_sahipler.all().order_by('-danisman_atanma_tarihi')[:10]
    
    context = {
        "vet": vet,
        "tahsis_sayisi": tahsis_qs.count(),
        "satis_sayisi": satilan_qs.count(),
        "kalan_envanter": vet.kalan_envanter,
        "tahsis_edilenler": tahsis_qs[:5],
        "satilanlar": satilan_qs[:5],
        "siparis_istekleri": siparis_qs[:5],
        
        # Randevu verileri
        
        # Danışman olduğu sahipler
        "danisman_oldugu_sahipler": danisman_oldugu_sahipler,
        
        # Kapasite bilgileri
        "danisman_sahip_sayisi": vet.danisman_sahip_sayisi,
        "kapasite_durumu": vet.kapasite_durumu,
    }
    return render(request, "veteriner/panel.html", context)


# ==================== HİZMET YÖNETİMİ ====================





# ==================== DEĞERLENDİRME YÖNETİMİ ====================

@login_required
def degerlendirme_listesi(request):
    """Değerlendirme listesi"""
    vet = getattr(request.user, 'veteriner_profili', None)
    if vet is None:
        return redirect("veteriner:veteriner_profil_tamamla")
    
    degerlendirmeler = VeterinerDegerlendirme.objects.filter(
        veteriner=vet, aktif=True
    ).order_by('-olusturulma_tarihi')
    
    page_obj = Paginator(degerlendirmeler, 20).get_page(request.GET.get("page"))
    
    return render(request, "veteriner/degerlendirme_listesi.html", {"page_obj": page_obj})


@login_required
def degerlendirme_ekle(request):
    """Yeni değerlendirme ekle"""
    vet = getattr(request.user, 'veteriner_profili', None)
    if vet is None:
        return redirect("veteriner:veteriner_profil_tamamla")
    
    if request.method == 'POST':
        form = VeterinerDegerlendirmeForm(request.POST)
        if form.is_valid():
            degerlendirme = form.save(commit=False)
            degerlendirme.veteriner = vet
            degerlendirme.save()
            
            # Veteriner ortalama puanını güncelle
            vet.ortalama_puan = VeterinerDegerlendirme.objects.filter(
                veteriner=vet, aktif=True
            ).aggregate(Avg('puan'))['puan__avg'] or 0
            vet.degerlendirme_sayisi = VeterinerDegerlendirme.objects.filter(
                veteriner=vet, aktif=True
            ).count()
            vet.save()
            
            messages.success(request, "Değerlendirme başarıyla eklendi.")
            return redirect('veteriner:degerlendirme_listesi')
    else:
        form = VeterinerDegerlendirmeForm()
    
    return render(request, "veteriner/degerlendirme_form.html", {"form": form})


# ==================== MEVCUT FONKSİYONLAR ====================

@login_required
def tahsis_listesi(request):
    vet = getattr(request.user, 'veteriner_profili', None)
    if vet is None or not vet.il or not vet.adres_detay:
        return redirect("veteriner:veteriner_profil_tamamla")
    qs = Etiket.objects.filter(satici_veteriner=vet, kanal=KANAL_VET).order_by("-tahsis_tarihi", "-olusturulma_tarihi")
    page_obj = Paginator(qs, 25).get_page(request.GET.get("page"))
    return render(request, "veteriner/liste_tahsis.html", {"page_obj": page_obj})

@login_required
def satis_listesi(request):
    vet = getattr(request.user, 'veteriner_profili', None)
    if vet is None or not vet.il or not vet.adres_detay:
        return redirect("veteriner:veteriner_profil_tamamla")
    qs = Etiket.objects.filter(satici_veteriner=vet, kanal=KANAL_VET, aktif=True).order_by("-first_activated_at", "-aktiflestirme_tarihi")
    page_obj = Paginator(qs, 25).get_page(request.GET.get("page"))
    return render(request, "veteriner/liste_satis.html", {"page_obj": page_obj})

@login_required
def siparis_listesi(request):
    vet = getattr(request.user, 'veteriner_profili', None)
    if vet is None or not vet.il or not vet.adres_detay:
        return redirect("veteriner:veteriner_profil_tamamla")
    qs = SiparisIstemi.objects.filter(veteriner=vet).order_by('-talep_tarihi')
    page_obj = Paginator(qs, 25).get_page(request.GET.get("page"))
    return render(request, "veteriner/liste_siparis.html", {"page_obj": page_obj})


# ==================== PROFİL TAMAMLAMA ====================

@login_required
def veteriner_profilim(request):
    """Veteriner profil görüntüleme sayfası"""
    from .models import VeterinerHizmet, Randevu, VeterinerDegerlendirme, SiparisIstemi
    
    vet = getattr(request.user, 'veteriner_profili', None)
    if vet is None:
        messages.error(request, "Veteriner profiliniz bulunamadı.")
        return redirect('anahtarlik:ev')
    
    # İstatistikler
    bekleyen_siparis = SiparisIstemi.objects.filter(veteriner=vet, onaylandi=False).count()
    
    # Son değerlendirmeler (3 adet)
    son_degerlendirmeler = VeterinerDegerlendirme.objects.filter(veteriner=vet).order_by('-olusturulma_tarihi')[:3]
    
    # Kapasite bilgileri
    danisman_sahip_sayisi = vet.danisman_sahip_sayisi
    dinamik_kapasite = vet.dinamik_kapasite
    kapasite_yuzdesi = vet.kapasite_yuzdesi
    kapasite_durumu = vet.kapasite_durumu
    
    context = {
        'vet': vet,
        'bekleyen_siparis': bekleyen_siparis,
        'son_degerlendirmeler': son_degerlendirmeler,
        'danisman_sahip_sayisi': danisman_sahip_sayisi,
        'dinamik_kapasite': dinamik_kapasite,
        'kapasite_yuzdesi': kapasite_yuzdesi,
        'kapasite_durumu': kapasite_durumu,
    }
    
    return render(request, 'veteriner/veteriner_profilim.html', context)


@login_required
def hesap_ayarlari(request):
    """Veteriner hesap ayarları - şifre değiştirme ve kullanıcı bilgileri"""
    vet = getattr(request.user, 'veteriner_profili', None)
    if vet is None:
        messages.error(request, "Veteriner profiliniz bulunamadı.")
        return redirect('anahtarlik:ev')
    
    if request.method == 'POST':
        form = VeterinerHesapForm(request.POST, instance=request.user)
        if form.is_valid():
            # Şifre değiştirildi mi kontrol et
            new_password = form.cleaned_data.get('new_password1')
            if new_password:
                # Şifre değiştirildi, flag'i güncelle
                vet.ilk_giris_sifre_degistirildi = True
                vet.save()
            form.save()
            if new_password:
                messages.success(request, "Şifreniz başarıyla değiştirildi! Artık paneline erişebilirsiniz.")
                return redirect('veteriner:veteriner_paneli')
            messages.success(request, "Hesap bilgileriniz başarıyla güncellendi!")
            return redirect('veteriner:hesap_ayarlari')
        else:
            messages.error(request, "Lütfen form hatalarını düzeltin.")
    else:
        form = VeterinerHesapForm(instance=request.user)
    
    return render(request, 'veteriner/hesap_ayarlari.html', {
        'form': form,
        'vet': vet
    })


@login_required
def profil_duzenle(request):
    """Veteriner temel profil bilgilerini düzenle"""
    from anahtarlik.dictionaries import Il, Ilce
    
    vet = getattr(request.user, 'veteriner_profili', None)
    if vet is None:
        messages.error(request, "Veteriner profiliniz bulunamadı.")
        return redirect('anahtarlik:ev')
    
    if request.method == 'POST':
        form = VeterinerProfilForm(request.POST, instance=vet)
        if form.is_valid():
            form.save()
            messages.success(request, "Profiliniz başarıyla güncellendi!")
            return redirect('veteriner:profil_duzenle')
        else:
            messages.error(request, "Lütfen form hatalarını düzeltin.")
    else:
        form = VeterinerProfilForm(instance=vet)
    
    # İl listesi
    iller = Il.objects.all().order_by('ad')
    
    # İlçe listesi (eğer il seçiliyse)
    ilceler = []
    if vet.il:
        ilceler = Ilce.objects.filter(il=vet.il).order_by('ad')
    
    return render(request, 'veteriner/profil_duzenle.html', {
        'form': form,
        'veteriner': vet,
        'iller': iller,
        'ilceler': ilceler,
    })


@login_required
def veteriner_profil_tamamla(request):
    """
    Veteriner profil tamamlama sayfası.
    İl, ilçe ve adres bilgilerinin girilmesi zorunlu.
    """
    # Veteriner profili var mı kontrol et
    try:
        vet = request.user.veteriner_profili
    except:
        messages.error(request, "Veteriner profiliniz bulunamadı.")
        return redirect('anahtarlik:ev')
    
    # Profil zaten tamam mı?
    if vet.il and vet.ilce and vet.adres_detay:
        messages.info(request, "Profiliniz zaten tamamlanmış.")
        return redirect('veteriner:veteriner_paneli')
    
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
                
                vet.ad = ad
                if telefon:
                    vet.telefon = telefon
                vet.il = Il.objects.get(id=il_id)
                vet.ilce = Ilce.objects.get(id=ilce_id)
                vet.adres_detay = adres_detay
                vet.save()
                
                messages.success(request, "Profiliniz başarıyla tamamlandı!")
                return redirect('veteriner:veteriner_paneli')
            except Exception as e:
                messages.error(request, f"Profil kaydedilirken hata oluştu: {str(e)}")
    
    # İl ve İlçe listelerini context'e ekle
    from anahtarlik.dictionaries import Il, Ilce
    iller = Il.objects.all().order_by('ad')
    
    # Eğer mevcut il varsa o ile ait ilçeleri getir
    if vet.il:
        ilceler = Ilce.objects.filter(il=vet.il).order_by('ad')
    else:
        ilceler = Ilce.objects.none()
    
    context = {
        'vet': vet,
        'iller': iller,
        'ilceler': ilceler,
    }
    
    return render(request, 'veteriner/profil_tamamla.html', context)


# AJAX endpoints for dynamic form loading
from django.views.decorators.http import require_http_methods  # Ek import

# DEPRECATED: Artık core/views.py'deki districts_for_province kullanılıyor
# Bu fonksiyon geriye dönük uyumluluk için tutuldu
def districts_for_city(request):
    """İlçe listesi AJAX endpoint - DEPRECATED: districts_for_province kullanın"""
    from core.views import districts_for_province
    return districts_for_province(request)

# Web sayfası (geri eklendi)
from django.http import Http404
from django.urls import reverse

def web_sayfasi_gorunum(request, slug):
    veteriner = get_object_or_404(Veteriner, web_slug=slug, web_aktif=True)
    resimler = []
    if veteriner.web_resim1: resimler.append(veteriner.web_resim1)
    if veteriner.web_resim2: resimler.append(veteriner.web_resim2)
    if veteriner.web_resim3: resimler.append(veteriner.web_resim3)
    
    # Sosyal medya URL'lerini hazırla
    instagram_url = None
    if veteriner.instagram:
        if 'http' in veteriner.instagram:
            instagram_url = veteriner.instagram
        else:
            instagram_url = f"https://instagram.com/{veteriner.instagram.replace('@', '')}"
    
    facebook_url = None
    if veteriner.facebook:
        if 'http' in veteriner.facebook:
            facebook_url = veteriner.facebook
        else:
            facebook_url = f"https://facebook.com/{veteriner.facebook}"
    
    # Session'dan başarı mesajını al
    randevu_basarili = request.session.pop('randevu_basarili', None)
    
    return render(request, 'veteriner/web_public.html', {
        "veteriner": veteriner, 
        "resimler": resimler,
        "instagram_url": instagram_url,
        "facebook_url": facebook_url,
        "randevu_basarili": randevu_basarili,
    })

def web_sayfasi_gorunum_legacy(request, veteriner_id):
    veteriner = get_object_or_404(Veteriner, id=veteriner_id, web_aktif=True)
    if veteriner.web_slug:
        from django.shortcuts import redirect
        return redirect('veteriner:web_sayfasi_gorunum', slug=veteriner.web_slug, permanent=True)
    raise Http404()

@login_required
def web_sayfasi_duzenle(request):
    from .forms import VeterinerWebForm
    veteriner = getattr(request.user, 'veteriner_profili', None)
    if not veteriner:
        messages.error(request, "Veteriner profili bulunamadı.")
        return redirect('veteriner:veteriner_paneli')
    
    if request.method == 'POST':
        form = VeterinerWebForm(request.POST, request.FILES, instance=veteriner)
        if form.is_valid():
            form.save()
            messages.success(request, "Web sayfanız başarıyla güncellendi!")
            return redirect('veteriner:web_sayfasi_duzenle')
        else:
            messages.error(request, "Lütfen form hatalarını düzeltin.")
    else:
        form = VeterinerWebForm(instance=veteriner)
    
    gunler = [
        ('pazartesi', 'Pazartesi'),
        ('sali', 'Salı'),
        ('carsamba', 'Çarşamba'),
        ('persembe', 'Perşembe'),
        ('cuma', 'Cuma'),
        ('cumartesi', 'Cumartesi'),
        ('pazar', 'Pazar'),
    ]
    
    return render(request, 'veteriner/web_form.html', {
        "veteriner": veteriner, 
        "form": form,
        "gunler": gunler
    })


# ==================== RANDEVU YÖNETİMİ ====================

@login_required
def randevu_yonetimi(request):
    """Randevu yönetim ana sayfası"""
    vet = getattr(request.user, 'veteriner_profili', None)
    if vet is None:
        return redirect("veteriner:veteriner_profil_tamamla")
    
    # Filtreleme parametreleri
    durum = request.GET.get('durum', '')
    tarih_baslangic = request.GET.get('tarih_baslangic', '')
    tarih_bitis = request.GET.get('tarih_bitis', '')
    arama = request.GET.get('arama', '')
    
    # Randevu sorgusu
    randevular = Randevu.objects.filter(veteriner=vet).order_by('-tarih', '-saat')
    
    # Filtreleme
    if durum:
        randevular = randevular.filter(durum=durum)
    if tarih_baslangic:
        randevular = randevular.filter(tarih__gte=tarih_baslangic)
    if tarih_bitis:
        randevular = randevular.filter(tarih__lte=tarih_bitis)
    if arama:
        randevular = randevular.filter(
            Q(musteri_adi__icontains=arama) | 
            Q(hayvan_adi__icontains=arama) |
            Q(musteri_telefon__icontains=arama)
        )
    
    # Sayfalama
    from django.core.paginator import Paginator
    paginator = Paginator(randevular, 20)  # Sayfa başına 20 randevu
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # İstatistikler
    toplam_randevu = randevular.count()
    bekleyen_randevu = randevular.filter(durum='BEKLIYOR').count()
    onaylanan_randevu = randevular.filter(durum='ONAYLANDI').count()
    tamamlanan_randevu = randevular.filter(durum='TAMAMLANDI').count()
    iptal_randevu = randevular.filter(durum='IPTAL').count()
    
    context = {
        'page_obj': page_obj,
        'durum': durum,
        'tarih_baslangic': tarih_baslangic,
        'tarih_bitis': tarih_bitis,
        'arama': arama,
        'toplam_randevu': toplam_randevu,
        'bekleyen_randevu': bekleyen_randevu,
        'onaylanan_randevu': onaylanan_randevu,
        'tamamlanan_randevu': tamamlanan_randevu,
        'iptal_randevu': iptal_randevu,
    }
    
    return render(request, 'veteriner/randevu_yonetimi.html', context)


@login_required
def randevu_detay(request, randevu_id):
    """Randevu detay sayfası"""
    vet = getattr(request.user, 'veteriner_profili', None)
    if vet is None:
        return redirect("veteriner:veteriner_profil_tamamla")
    
    randevu = get_object_or_404(Randevu, id=randevu_id, veteriner=vet)
    
    # Durum güncelleme
    if request.method == 'POST':
        yeni_durum = request.POST.get('durum')
        notlar = request.POST.get('notlar', '')
        fiyat = request.POST.get('fiyat', '')
        
        if yeni_durum:
            randevu.durum = yeni_durum
        if notlar:
            randevu.notlar = notlar
        if fiyat:
            try:
                randevu.fiyat = float(fiyat)
            except ValueError:
                pass
        
        randevu.save()
        messages.success(request, "Randevu güncellendi.")
        return redirect('veteriner:randevu_detay', randevu_id=randevu_id)
    
    return render(request, 'veteriner/randevu_detay.html', {'randevu': randevu})


@login_required
def randevu_durum_guncelle(request, randevu_id):
    """Randevu durumu hızlı güncelleme"""
    vet = getattr(request.user, 'veteriner_profili', None)
    if vet is None:
        return redirect("veteriner:veteriner_profil_tamamla")
    
    randevu = get_object_or_404(Randevu, id=randevu_id, veteriner=vet)
    
    if request.method == 'POST':
        yeni_durum = request.POST.get('durum')
        if yeni_durum:
            randevu.durum = yeni_durum
            randevu.save()
            messages.success(request, f"Randevu durumu '{yeni_durum}' olarak güncellendi.")
    
    return redirect('veteriner:randevu_yonetimi')


# ==================== PUBLIC RANDEVU SİSTEMİ ====================

def public_randevu_olustur(request, slug):
    """Public randevu oluşturma - Herkese açık"""
    from datetime import datetime, time
    from django.contrib import messages
    
    veteriner = get_object_or_404(Veteriner, web_slug=slug, web_aktif=True)
    
    if request.method == 'POST':
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
        # Form verilerini al
        musteri_adi = request.POST.get('musteri_adi', '').strip()
        musteri_telefon = request.POST.get('musteri_telefon', '').strip()
        musteri_email = request.POST.get('musteri_email', '').strip()
        tarih_str = request.POST.get('tarih', '')
        saat_str = request.POST.get('saat', '')
        hayvan_adi = request.POST.get('hayvan_adi', '').strip()
        hayvan_turu = request.POST.get('hayvan_turu', '').strip()
        sorun_aciklamasi = request.POST.get('sorun_aciklamasi', '').strip()
        notlar = request.POST.get('notlar', '').strip()
        
        # Validasyon
        errors = []
        if not musteri_adi:
            errors.append("Ad Soyad alanı zorunludur.")
        if not musteri_telefon:
            errors.append("Telefon alanı zorunludur.")
        if not tarih_str:
            errors.append("Randevu tarihi seçimi zorunludur.")
        if not saat_str:
            errors.append("Saat seçimi zorunludur.")
        if not hayvan_adi:
            errors.append("Evcil hayvan adı zorunludur.")
        if not hayvan_turu:
            errors.append("Evcil hayvan türü seçimi zorunludur.")
        if not sorun_aciklamasi:
            errors.append("Sorun açıklaması zorunludur.")
        
        if errors:
            if is_ajax:
                return JsonResponse({"ok": False, "errors": errors}, status=400)
            for error in errors:
                messages.error(request, error)
        else:
            try:
                # Tarih ve saat kontrolü
                randevu_tarihi = datetime.strptime(tarih_str, '%Y-%m-%d').date()
                randevu_saati = datetime.strptime(saat_str, '%H:%M').time()
                
                # Geçmiş tarih kontrolü
                if randevu_tarihi < date.today():
                    if is_ajax:
                        return JsonResponse({"ok": False, "errors": ["Geçmiş tarih seçilemez."]}, status=400)
                    messages.error(request, "Geçmiş tarih seçilemez.")
                else:
                    # Çalışma saatleri kontrolü
                    if not veteriner_working_hours_check(veteriner, randevu_tarihi, randevu_saati):
                        if is_ajax:
                            return JsonResponse({"ok": False, "errors": ["Seçilen tarih ve saatte veteriner çalışmıyor. Lütfen çalışma saatleri içinde bir randevu seçin."]}, status=400)
                        messages.error(request, "Seçilen tarih ve saatte veteriner çalışmıyor. Lütfen çalışma saatleri içinde bir randevu seçin.")
                    else:
                        # Aynı tarih ve saatte randevu var mı kontrol et
                        existing_randevu = Randevu.objects.filter(
                            veteriner=veteriner,
                            tarih=randevu_tarihi,
                            saat=randevu_saati,
                            durum__in=['BEKLIYOR', 'ONAYLANDI']
                        ).exists()
                        
                        if existing_randevu:
                            if is_ajax:
                                return JsonResponse({"ok": False, "errors": ["Bu tarih ve saatte zaten bir randevu bulunmaktadır. Lütfen farklı bir saat seçin."]}, status=400)
                            messages.error(request, "Bu tarih ve saatte zaten bir randevu bulunmaktadır. Lütfen farklı bir saat seçin.")
                        else:
                            # Varsayılan hizmet oluştur veya mevcut olanı kullan
                            varsayilan_hizmet, created = VeterinerHizmet.objects.get_or_create(
                                veteriner=veteriner,
                                hizmet_adi="Genel Muayene",
                                defaults={
                                    'hizmet_turu': 'GENEL',
                                    'aciklama': 'Genel veteriner muayenesi',
                                    'fiyat': 0,
                                    'sure_dakika': 30,
                                    'aktif': True
                                }
                            )
                            
                            # Randevu oluştur
                            randevu = Randevu.objects.create(
                                veteriner=veteriner,
                                hizmet=varsayilan_hizmet,
                                musteri_adi=musteri_adi,
                                musteri_telefon=musteri_telefon,
                                musteri_email=musteri_email or '',
                                hayvan_adi=hayvan_adi,
                                hayvan_turu=hayvan_turu,
                                sorun_aciklamasi=sorun_aciklamasi,
                                notlar=notlar or '',
                                tarih=randevu_tarihi,
                                saat=randevu_saati,
                                durum='BEKLIYOR'
                            )
                            
                            # Başarı mesajını hazırla
                            basari_mesaji = (
                                f"Randevu talebiniz başarıyla oluşturuldu! Randevu numaranız: #{randevu.id}. "
                                "Veterinerimiz en kısa sürede sizinle iletişime geçecektir."
                            )
                            if is_ajax:
                                return JsonResponse({"ok": True, "id": randevu.id, "message": basari_mesaji})
                            # Ajax değilse önceki davranışı koru
                            request.session['randevu_basarili'] = basari_mesaji
                            return redirect('veteriner:web_sayfasi_gorunum', slug=slug)
                            
            except ValueError as e:
                if is_ajax:
                    return JsonResponse({"ok": False, "errors": ["Tarih veya saat formatı hatalı."]}, status=400)
                messages.error(request, "Tarih veya saat formatı hatalı.")
            except Exception as e:
                if is_ajax:
                    return JsonResponse({"ok": False, "errors": [f"Randevu oluşturulurken hata oluştu: {str(e)}"]}, status=400)
                messages.error(request, f"Randevu oluşturulurken hata oluştu: {str(e)}")
    
    # GET isteği için web sayfasını göster
    return redirect('veteriner:web_sayfasi_gorunum', slug=slug)


def veteriner_working_hours_check(veteriner, randevu_tarihi, randevu_saati):
    """Veteriner çalışma saatleri kontrolü"""
    from datetime import datetime
    
    # Haftanın gününü al (0=Pazartesi, 6=Pazar)
    weekday = randevu_tarihi.weekday()
    
    # Çalışma saatleri kontrolü
    if weekday == 0:  # Pazartesi
        if veteriner.pazartesi_kapali:
            return False
        if veteriner.pazartesi_baslangic and veteriner.pazartesi_bitis:
            return veteriner.pazartesi_baslangic <= randevu_saati <= veteriner.pazartesi_bitis
    elif weekday == 1:  # Salı
        if veteriner.sali_kapali:
            return False
        if veteriner.sali_baslangic and veteriner.sali_bitis:
            return veteriner.sali_baslangic <= randevu_saati <= veteriner.sali_bitis
    elif weekday == 2:  # Çarşamba
        if veteriner.carsamba_kapali:
            return False
        if veteriner.carsamba_baslangic and veteriner.carsamba_bitis:
            return veteriner.carsamba_baslangic <= randevu_saati <= veteriner.carsamba_bitis
    elif weekday == 3:  # Perşembe
        if veteriner.persembe_kapali:
            return False
        if veteriner.persembe_baslangic and veteriner.persembe_bitis:
            return veteriner.persembe_baslangic <= randevu_saati <= veteriner.persembe_bitis
    elif weekday == 4:  # Cuma
        if veteriner.cuma_kapali:
            return False
        if veteriner.cuma_baslangic and veteriner.cuma_bitis:
            return veteriner.cuma_baslangic <= randevu_saati <= veteriner.cuma_bitis
    elif weekday == 5:  # Cumartesi
        if veteriner.cumartesi_kapali:
            return False
        if veteriner.cumartesi_baslangic and veteriner.cumartesi_bitis:
            return veteriner.cumartesi_baslangic <= randevu_saati <= veteriner.cumartesi_bitis
    elif weekday == 6:  # Pazar
        if veteriner.pazar_kapali:
            return False
        if veteriner.pazar_baslangic and veteriner.pazar_bitis:
            return veteriner.pazar_baslangic <= randevu_saati <= veteriner.pazar_bitis
    
    # Eğer çalışma saatleri tanımlanmamışsa varsayılan olarak 09:00-18:00
    from datetime import time
    return time(9, 0) <= randevu_saati <= time(18, 0)