# anahtarlik/views.py

import logging
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import transaction
from .models import Sahip, EvcilHayvan, SaglikKaydi, BeslenmeKaydi, Alerji, AsiTakvimi, IlacKaydi, AmeliyatKaydi, KiloKaydi, SahipProPaket, SahipProAbonelik, Bildirim
from etiket.models import Etiket
from .forms import EtiketForm, EvcilHayvanForm, HesapAyarlariForm
from .dictionaries import Il, Ilce

from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

from django.urls import reverse  # <-- eklendi

logger = logging.getLogger(__name__)


# Bildirim Sistemi Views
@login_required
def bildirimler(request):
    """Kullanıcının bildirimlerini listeler - SÜPER OPTİMİZE EDİLDİ"""
    sahip = request.user.sahip
    
    # SÜPER OPTİMİZASYON: Son 7 gün + select_related (maksimum performans)
    from datetime import timedelta
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    bildirimler_list = Bildirim.objects.filter(
        sahip=sahip,
        olusturma_zamani__gte=seven_days_ago
    ).select_related('sahip', 'sahip__kullanici', 'tarama')\
     .order_by('-olusturma_zamani')
    
    # Sayfa başına 10 bildirim (mobil uyumlu)
    paginator = Paginator(bildirimler_list, 10)
    page_number = request.GET.get('page')
    bildirimler = paginator.get_page(page_number)
    
    # Tek sorguda okunmamış sayısını al
    okunmamis_sayi = Bildirim.objects.filter(sahip=sahip, okundu=False).count()
    
    # AJAX isteği ise sadece okunmamışları okundu yap
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        Bildirim.objects.filter(sahip=sahip, okundu=False).update(okundu=True)
        okunmamis_sayi = 0
    
    context = {
        'bildirimler': bildirimler,
        'okunmamis_sayi': okunmamis_sayi,
        'paginator': paginator,
    }
    return render(request, 'anahtarlik/bildirimler.html', context)


@login_required
def bildirim_oku(request, bildirim_id):
    """Bildirimi okundu olarak işaretle ve URL'ye yönlendir"""
    bildirim = get_object_or_404(Bildirim, id=bildirim_id, sahip=request.user.sahip)
    bildirim.okundu = True
    bildirim.save()
    
    if bildirim.url and not bildirim.url.startswith('/admin/'):
        return redirect(bildirim.url)
    else:
        # Tarama detayına yönlendir (normal kullanıcılar için)
        if bildirim.tarama:
            # Normal kullanıcılar için tarama detay sayfasına yönlendir
            return redirect('etiket:tarama_detay', tarama_id=bildirim.tarama.id)
        else:
            return redirect('anahtarlik:bildirimler')


@login_required
def tum_bildirimleri_oku(request):
    """Tüm bildirimleri okundu olarak işaretle"""
    Bildirim.objects.filter(sahip=request.user.sahip, okundu=False).update(okundu=True)
    return redirect('anahtarlik:bildirimler')


@login_required
def profil_duzenle(request):
    """Sahip profil düzenleme sayfası (form-based)"""
    from .dictionaries import Il, Ilce
    from .forms import SahipProfilForm
    from django.contrib import messages
    
    sahip = getattr(request.user, 'sahip', None)
    if sahip is None:
        messages.error(request, "Sahip profiliniz bulunamadı.")
        return redirect('anahtarlik:ev')
    
    # Eski il/ilçe bilgilerini sakla (danışman veteriner atama için)
    eski_il = sahip.il
    eski_ilce = sahip.ilce
    
    if request.method == 'POST':
        form = SahipProfilForm(request.POST, request.FILES, instance=sahip)
        if form.is_valid():
            form.save()
            
            # Veritabanından güncel veriyi al (refresh)
            sahip.refresh_from_db()
            
            # User modelini de güncelle
            request.user.first_name = form.cleaned_data.get('ad', '')
            request.user.last_name = form.cleaned_data.get('soyad', '')
            request.user.save()
            
            # İl/ilçe değiştiyse danışman veteriner güncelle
            if (eski_il != sahip.il or eski_ilce != sahip.ilce) and sahip.danisman_veteriner:
                if sahip.danisman_veteriner.ilce != sahip.ilce:
                    yeni_danisman = sahip.danisman_veteriner_ata(force_update=True)
                    if yeni_danisman:
                        messages.info(request, f"İl/ilçe değişikliği nedeniyle yeni danışman veterineriniz: {yeni_danisman.ad}")
                    else:
                        messages.warning(request, "Yeni ilçenizde aktif veteriner bulunamadı.")
            
            messages.success(request, "Profiliniz başarıyla güncellendi!")
            return redirect('anahtarlik:profil_duzenle')
        else:
            messages.error(request, "Lütfen form hatalarını düzeltin.")
    else:
        form = SahipProfilForm(instance=sahip)
    
    # İl listesi
    iller = Il.objects.all().order_by('ad')
    
    # İlçe listesi (eğer il seçiliyse)
    ilceler = []
    if sahip.il:
        ilceler = Ilce.objects.filter(il=sahip.il).order_by('ad')
    
    return render(request, 'anahtarlik/sahip_profil_duzenle.html', {
        'form': form,
        'sahip': sahip,
        'iller': iller,
        'ilceler': ilceler,
    })


@login_required
def profil_duzenle_eski(request):
    """ESKİ VERSİYON - Geriye dönük uyumluluk için saklandı"""
    if request.method == 'POST':
        try:
            # Kullanıcı tipine göre profil güncelleme
            if hasattr(request.user, 'sahip'):
                # Sahip kullanıcı
                sahip = request.user.sahip
                
                # Eski il/ilçe bilgilerini sakla
                eski_il = sahip.il
                eski_ilce = sahip.ilce
                
                sahip.ad = request.POST.get('ad')
                sahip.soyad = request.POST.get('soyad')
                sahip.telefon = request.POST.get('telefon')
                sahip.yedek_telefon = request.POST.get('yedek_telefon')
                sahip.acil_durum_kontagi = request.POST.get('acil_durum_kontagi')
                
                # İl/ilçe güncelleme
                yeni_il_id = request.POST.get('il')
                yeni_ilce_id = request.POST.get('ilce')
                
                if yeni_il_id:
                    from anahtarlik.dictionaries import Il, Ilce
                    sahip.il = Il.objects.get(id=yeni_il_id)
                if yeni_ilce_id:
                    sahip.ilce = Ilce.objects.get(id=yeni_ilce_id)
                
                sahip.save()
                
                # İl/ilçe değiştiyse danışman veteriner güncelle
                if (eski_il != sahip.il or eski_ilce != sahip.ilce) and sahip.danisman_veteriner:
                    # Eski danışman veteriner farklı ilçedeyse yeni danışman ata
                    if sahip.danisman_veteriner.ilce != sahip.ilce:
                        yeni_danisman = sahip.danisman_veteriner_ata(force_update=True)
                        if yeni_danisman:
                            messages.info(request, f"İl/ilçe değişikliği nedeniyle yeni danışman veterineriniz: {yeni_danisman.ad}")
                        else:
                            messages.warning(request, "Yeni ilçenizde aktif veteriner bulunamadı.")
                
                # User modelini de güncelle
                request.user.first_name = request.POST.get('ad')
                request.user.last_name = request.POST.get('soyad')
                request.user.save()
                
                messages.success(request, "Profil bilgileri güncellendi.")
                return redirect('anahtarlik:sahip_profilim')
                
            elif hasattr(request.user, 'veteriner_profili'):
                # Veteriner kullanıcı
                veteriner = request.user.veteriner_profili
                
                # Eski il/ilçe bilgilerini sakla
                eski_il = veteriner.il
                eski_ilce = veteriner.ilce
                
                veteriner.ad = request.POST.get('ad')
                veteriner.soyad = request.POST.get('soyad')
                veteriner.telefon = request.POST.get('telefon')
                veteriner.uzmanlik_alanlari = request.POST.get('uzmanlik_alanlari')
                veteriner.deneyim_yili = request.POST.get('deneyim_yili') or 0
                veteriner.ozgecmis = request.POST.get('ozgecmis')
                
                # İl/ilçe güncelleme
                yeni_il_id = request.POST.get('il')
                yeni_ilce_id = request.POST.get('ilce')
                
                if yeni_il_id:
                    from anahtarlik.dictionaries import Il, Ilce
                    veteriner.il = Il.objects.get(id=yeni_il_id)
                if yeni_ilce_id:
                    veteriner.ilce = Ilce.objects.get(id=yeni_ilce_id)
                
                veteriner.save()
                
                # İl/ilçe değiştiyse danışman olduğu sahipleri güncelle
                if (eski_il != veteriner.il or eski_ilce != veteriner.ilce):
                    # Eski ilçedeki sahipleri yeni danışman ata
                    for sahip in veteriner.danisman_oldugu_sahipler.all():
                        if sahip.ilce != veteriner.ilce:
                            yeni_danisman = sahip.danisman_veteriner_ata(force_update=True)
                            if yeni_danisman:
                                messages.info(request, f"Sahip {sahip.ad} {sahip.soyad} için yeni danışman veteriner atandı.")
                
                # User modelini de güncelle
                request.user.first_name = request.POST.get('ad')
                request.user.last_name = request.POST.get('soyad')
                request.user.email = request.POST.get('email')
                request.user.save()
                
                messages.success(request, "Profil bilgileri güncellendi.")
                return redirect('anahtarlik:kullanici_paneli')
                
            elif hasattr(request.user, 'petshop_profili'):
                # Petshop kullanıcı
                petshop = request.user.petshop_profili
                petshop.isletme_adi = request.POST.get('isletme_adi')
                petshop.yetkili_kisi = request.POST.get('yetkili_kisi')
                petshop.telefon = request.POST.get('telefon')
                petshop.vergi_no = request.POST.get('vergi_no')
                petshop.ticaret_sicil_no = request.POST.get('ticaret_sicil_no')
                petshop.isletme_aciklamasi = request.POST.get('isletme_aciklamasi')
                petshop.save()
                
                # User modelini de güncelle
                request.user.email = request.POST.get('email')
                request.user.save()
                
                messages.success(request, "Profil bilgileri güncellendi.")
                return redirect('anahtarlik:kullanici_paneli')
                
            else:
                # Misafir kullanıcı
                request.user.first_name = request.POST.get('ad')
                request.user.last_name = request.POST.get('soyad')
                request.user.email = request.POST.get('email')
                request.user.save()
                
                # Misafir profil varsa güncelle
                if hasattr(request.user, 'misafir_profili'):
                    misafir = request.user.misafir_profili
                    misafir.telefon = request.POST.get('telefon')
                    misafir.save()
                
                messages.success(request, "Profil bilgileri güncellendi.")
                return redirect('guest_dashboard')
            
            # Şifre değiştirme kontrolü
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')
            current_password = request.POST.get('current_password')
            
            if new_password1 and new_password2:
                if new_password1 == new_password2:
                    if request.user.check_password(current_password):
                        request.user.set_password(new_password1)
                        request.user.save()
                        messages.success(request, "Şifre başarıyla değiştirildi.")
                    else:
                        messages.error(request, "Mevcut şifre yanlış.")
                else:
                    messages.error(request, "Yeni şifreler eşleşmiyor.")
                    
        except Exception as e:
            messages.error(request, f"Profil güncellenirken hata oluştu: {str(e)}")
    
    # GET request için context hazırla
    context = {}
    
    if hasattr(request.user, 'sahip'):
        context['sahip'] = request.user.sahip
    elif hasattr(request.user, 'veteriner_profili'):
        context['veteriner'] = request.user.veteriner_profili
    elif hasattr(request.user, 'petshop_profili'):
        context['petshop'] = request.user.petshop_profili
    elif hasattr(request.user, 'misafir_profili'):
        context['misafir'] = request.user.misafir_profili
    
    return render(request, 'anahtarlik/profil_duzenle.html', context)


@login_required
def hesap_ayarlari(request):
    """Genel kullanıcı hesap ayarları - şifre değiştirme ve kullanıcı bilgileri"""
    if request.method == 'POST':
        form = HesapAyarlariForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Hesap bilgileriniz başarıyla güncellendi!")
            return redirect('anahtarlik:hesap_ayarlari')
        else:
            messages.error(request, "Lütfen form hatalarını düzeltin.")
    else:
        form = HesapAyarlariForm(instance=request.user)
    
    return render(request, 'anahtarlik/hesap_ayarlari.html', {
        'form': form,
        'user': request.user
    })


@login_required
def hayvan_pdf_indir(request, pet_id):
    evcil_hayvan = get_object_or_404(EvcilHayvan, id=pet_id, sahip__kullanici=request.user)
    template = get_template("anahtarlik/pdf_template.html")
    html = template.render({"hayvan": evcil_hayvan})

    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename="{evcil_hayvan.ad}_rapor.pdf"'
    pisa.CreatePDF(html, dest=response)
    return response


import json
from django.core.serializers.json import DjangoJSONEncoder

@login_required
def pet_detail(request, pet_id):
    evcil_hayvan = get_object_or_404(EvcilHayvan, id=pet_id, sahip__kullanici=request.user)

    asi_takvimi = evcil_hayvan.asi_takvimi.all().order_by('-planlanan_tarih')
    saglik_kayitlari = evcil_hayvan.saglik_kayitlari.all().order_by('-asi_tarihi')
    ilac_kayitlari = evcil_hayvan.ilac_kayitlari.all().order_by('-baslangic_tarihi')
    ameliyat_kayitlari = evcil_hayvan.ameliyat_kayitlari.all().order_by('-tarih')
    alerjiler = evcil_hayvan.alerjiler.all().order_by('-kaydedilme_tarihi')
    beslenme_kayitlari = evcil_hayvan.beslenme_kayitlari.all().order_by('-tarih')
    kilo_kayitlari = evcil_hayvan.kilo_kayitlari.all().order_by('tarih')

    # ✅ JSON’a çevir
    kilo_data = list(kilo_kayitlari.values("tarih", "kilo"))
    kilo_data_json = json.dumps(kilo_data, cls=DjangoJSONEncoder)

    context = {
        'hayvan': evcil_hayvan,
        'asi_takvimi': asi_takvimi,
        'saglik_kayitlari': saglik_kayitlari,
        'ilac_kayitlari': ilac_kayitlari,
        'ameliyat_kayitlari': ameliyat_kayitlari,
        'alerjiler': alerjiler,
        'beslenme_kayitlari': beslenme_kayitlari,
        'kilo_kayitlari': kilo_kayitlari,
        'kilo_data_json': kilo_data_json,   # ✅ Template’e JSON gönderiyoruz
    }
    return render(request, 'anahtarlik/pet_detail.html', context)


def ev(request):
    """Ana sayfa view'ı - Dinamik içerik ile"""
    from .models import HeroSlide, HizmetKarti, AnaSayfaAyar, EvcilHayvan
    from shop.models import Urun
    from ilan.models import Ilan

    # Aktif hero slide'ları al
    hero_slides = HeroSlide.objects.filter(aktif=True).order_by('sira')

    # Aktif hizmet kartlarını al
    hizmet_kartlari = HizmetKarti.objects.filter(aktif=True).order_by('sira')

    # Ana sayfa ayarlarını al (singleton)
    ayarlar = AnaSayfaAyar.load()

    # Tüm etiket ürünleri - Horizontal scroll için
    one_cikan_etiketler = Urun.objects.filter(
        urun_tipi='etiket',
        aktif=True
    ).select_related('etiket_kategori').prefetch_related('resimler').order_by('-olusturulma_tarihi')
    
    for urun in one_cikan_etiketler:
        urun.kullanici_fiyati = urun.get_kullanici_fiyati(request.user if request.user.is_authenticated else None)

    one_cikan_petshop = Urun.objects.filter(
        urun_tipi='normal',
        aktif=True,
        one_cikan=True
    ).prefetch_related('kategoriler', 'resimler')[:6]
    
    for urun in one_cikan_petshop:
        urun.kullanici_fiyati = urun.get_kullanici_fiyati(request.user if request.user.is_authenticated else None)

    # Öne çıkan ilanlar
    vitrin_ilanlar = Ilan.objects.filter(
        aktif=True,
        onaylandi=True,
        onemli_mi=True
    ).select_related(
        'hayvan_profili',
        'hayvan_profili__kullanici'
    ).prefetch_related(
        'hayvan_profili__resimler'
    )[:6]

    # İstatistikler
    toplam_evcil_hayvan = EvcilHayvan.objects.count()
    toplam_urun = Urun.objects.filter(aktif=True).count()
    toplam_ilan = Ilan.objects.filter(aktif=True, onaylandi=True).count()
    toplam_veteriner = None  # Veteriner sayısı varsa buraya eklenebilir

    context = {
        'hero_slides': hero_slides,
        'hizmet_kartlari': hizmet_kartlari,
        'ayarlar': ayarlar,
        'one_cikan_etiketler': one_cikan_etiketler,
        'one_cikan_petshop': one_cikan_petshop,
        'vitrin_ilanlar': vitrin_ilanlar,
        'toplam_evcil_hayvan': toplam_evcil_hayvan,
        'toplam_urun': toplam_urun,
        'toplam_ilan': toplam_ilan,
    }

    return render(request, 'anahtarlik/ev.html', context)

def qr_kunye_nasil_calisir(request):
    """QR Künye Sisteminin nasıl çalıştığını açıklayan interaktif sayfa"""
    return render(request, 'anahtarlik/qr_kunye_nasil_calisir.html')

@login_required
def kullanici_paneli(request):
    # Rol bazlı yönlendirme: veteriner/petshop kullanıcıları kendi panellerine gitsin
    user = request.user
    vet = getattr(user, 'veteriner_profili', None)
    if vet is not None:
        if not vet.il or not vet.adres_detay:
            return redirect('veteriner:veteriner_profil_tamamla')
        return redirect('veteriner:veteriner_paneli')

    shop = getattr(user, 'petshop_profili', None)
    if shop is not None:
        try:
            return redirect('petshop:petshop_paneli')
        except Exception:
            return redirect('petshop:petshop_profil_tamamla')

    sahip = get_object_or_404(Sahip, kullanici=user)
    
    # Query optimization
    evcil_hayvanlar = sahip.evcil_hayvanlar.select_related('tur', 'irk').prefetch_related('etiket').all()
    
    # Künye tarihi geçmiş olanları filtrele (görünmesin)
    now = timezone.now()
    from datetime import timedelta
    gecerli_hayvanlar = []
    kayip_hayvanlar = []
    kunye_suresi_dolmak_uzere = []
    
    for hayvan in evcil_hayvanlar:
        # Kayıp hayvan kontrolü
        if hayvan.kayip_durumu:
            kayip_hayvanlar.append(hayvan)
        
        # Etiket yoksa göster
        if not hayvan.etiket:
            gecerli_hayvanlar.append(hayvan)
        # Etiket varsa ve son kullanma tarihi geçmemişse göster
        elif hayvan.etiket.son_kullanma_tarihi is None or hayvan.etiket.son_kullanma_tarihi > now:
            gecerli_hayvanlar.append(hayvan)
            
            # Künye süresi dolmak üzere kontrolü (30 gün içinde)
            if hayvan.etiket.son_kullanma_tarihi:
                kalan_gun = (hayvan.etiket.son_kullanma_tarihi - now).days
                if 0 < kalan_gun <= 30:
                    kunye_suresi_dolmak_uzere.append({
                        'hayvan': hayvan,
                        'kalan_gun': kalan_gun
                    })
        # Etiket varsa ama son kullanma tarihi geçmişse gösterme
    
    # Liste sıralaması
    gecerli_hayvanlar.sort(key=lambda x: x.id, reverse=True)
    
    paginator = Paginator(gecerli_hayvanlar, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Künye sayısını hesapla (sadece geçerli künyeler)
    kunye_sayisi = len([h for h in gecerli_hayvanlar if h.etiket])
    
    # İlan sayısını hesapla
    from ilan.models import Ilan
    sahip_ilan_sayisi = Ilan.objects.filter(hayvan_profili__kullanici=user, aktif=True).count()
    
    # Kayıp hayvan sayısı
    kayip_hayvan_sayisi = len(kayip_hayvanlar)
    
    # Toplam evcil hayvan sayısı (tüm hayvanlar - kayıp dahil)
    toplam_evcil_hayvan_sayisi = len(gecerli_hayvanlar)
    
    # Son bildirimler (5 adet)
    son_bildirimler = Bildirim.objects.filter(
        sahip=sahip
    ).select_related('tarama').order_by('-olusturma_zamani')[:5]
    
    # Okunmamış bildirim sayısı
    okunmamis_bildirim_sayisi = Bildirim.objects.filter(sahip=sahip, okundu=False).count()
    
    # Yaklaşan aşılar (30 gün içinde, tamamlanmamış)
    yakin_tarih = now.date() + timedelta(days=30)
    yaklasan_asilar = AsiTakvimi.objects.filter(
        evcil_hayvan__sahip=sahip,
        planlanan_tarih__lte=yakin_tarih,
        planlanan_tarih__gte=now.date(),
        tamamlandi=False
    ).select_related('evcil_hayvan').order_by('planlanan_tarih')[:5]
    
    # Danışman veteriner bilgileri
    danisman_veteriner = sahip.danisman_veteriner
    
    return render(request, 'anahtarlik/kullanici_paneli.html', {
        'evcil_hayvanlar': page_obj,
        'danisman_veteriner': danisman_veteriner,
        'sahip': sahip,
        'kunye_sayisi': kunye_sayisi,
        'sahip_ilan_sayisi': sahip_ilan_sayisi,
        'kayip_hayvan_sayisi': kayip_hayvan_sayisi,
        'toplam_evcil_hayvan_sayisi': toplam_evcil_hayvan_sayisi,
        'kayip_hayvanlar': kayip_hayvanlar,
        'kunye_suresi_dolmak_uzere': kunye_suresi_dolmak_uzere,
        'son_bildirimler': son_bildirimler,
        'okunmamis_bildirim_sayisi': okunmamis_bildirim_sayisi,
        'yaklasan_asilar': yaklasan_asilar,
    })

@login_required
def evcil_hayvanlarim(request):
    """Sahip kullanıcıları için evcil hayvanları listele"""
    from django.utils import timezone
    sahip = get_object_or_404(Sahip, kullanici=request.user)
    
    # Query optimization: N+1 query problemini önlemek için select_related ve prefetch_related kullan
    evcil_hayvanlar = sahip.evcil_hayvanlar.select_related('tur', 'irk').prefetch_related('etiket').all()
    
    # Künye tarihi geçmiş olanları filtrele (görünmesin)
    now = timezone.now()
    gecerli_hayvanlar = []
    for hayvan in evcil_hayvanlar:
        # Etiket yoksa göster
        if not hayvan.etiket:
            gecerli_hayvanlar.append(hayvan)
        # Etiket varsa ve son kullanma tarihi geçmemişse göster
        elif hayvan.etiket.son_kullanma_tarihi is None or hayvan.etiket.son_kullanma_tarihi > now:
            gecerli_hayvanlar.append(hayvan)
        # Etiket varsa ama son kullanma tarihi geçmişse gösterme
    
    # Liste sıralaması
    gecerli_hayvanlar.sort(key=lambda x: x.id, reverse=True)
    
    paginator = Paginator(gecerli_hayvanlar, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # İstatistikler
    from ilan.models import Ilan
    from datetime import timedelta
    
    # Künye sayısı (aktif künyeler)
    kunye_sayisi = len([h for h in gecerli_hayvanlar if h.etiket and h.etiket.aktif])
    
    # İlan sayısı
    sahip_ilan_sayisi = Ilan.objects.filter(hayvan_profili__kullanici=request.user, aktif=True).count()
    
    # Kayıp hayvan sayısı
    kayip_hayvanlar = [h for h in gecerli_hayvanlar if h.kayip_durumu]
    kayip_hayvan_sayisi = len(kayip_hayvanlar)
    
    # Toplam evcil hayvan sayısı (tüm hayvanlar - kayıp dahil)
    toplam_evcil_hayvan_sayisi = len(gecerli_hayvanlar)
    
    return render(request, 'anahtarlik/kullanici_paneli.html', {
        'evcil_hayvanlar': page_obj,
        'is_pets_page': True,
        'sahip': sahip,
        'toplam_evcil_hayvan_sayisi': toplam_evcil_hayvan_sayisi,
        'kunye_sayisi': kunye_sayisi,
        'sahip_ilan_sayisi': sahip_ilan_sayisi,
        'kayip_hayvan_sayisi': kayip_hayvan_sayisi,
    })

@login_required
def kunyelerim(request):
    """Sahip kullanıcıları için künyelerini listele"""
    sahip = get_object_or_404(Sahip, kullanici=request.user)
    # Evcil hayvanlarının künyelerini al
    etiketler = Etiket.objects.filter(evcil_hayvan__sahip=sahip).order_by('-olusturulma_tarihi')
    return render(request, 'anahtarlik/kunyelerim.html', {
        'etiketler': etiketler,
        'now': timezone.now()
    })

@login_required
def sahip_profilim(request):
    """Sahip kullanıcıları için profil sayfası"""
    sahip = get_object_or_404(Sahip, kullanici=request.user)
    
    # İstatistikler
    evcil_hayvan_sayisi = sahip.evcil_hayvanlar.count()
    aktif_etiket_sayisi = Etiket.objects.filter(evcil_hayvan__sahip=sahip, aktif=True).count()
    
    # Pro abonelik bilgileri
    aktif_pro_abonelik = sahip.aktif_pro_abonelik
    
    # Son eklenen evcil hayvanlar (3 adet)
    son_evcil_hayvanlar = sahip.evcil_hayvanlar.all().order_by('-id')[:3]
    
    # Danışman veteriner bilgileri
    danisman_veteriner = sahip.danisman_veteriner
    
    context = {
        'sahip': sahip,
        'evcil_hayvan_sayisi': evcil_hayvan_sayisi,
        'aktif_etiket_sayisi': aktif_etiket_sayisi,
        'aktif_pro_abonelik': aktif_pro_abonelik,
        'son_evcil_hayvanlar': son_evcil_hayvanlar,
        'danisman_veteriner': danisman_veteriner,
    }
    
    return render(request, 'anahtarlik/sahip_profilim.html', context)

@login_required
def add_pet(request):
    # Eğer session'da etiket_id varsa ve step 1 ise, direkt step 2'ye geç
    etiket_id = request.session.get('etiket_id')
    if etiket_id and request.session.get('add_pet_step', 1) == 1:
        try:
            etiket = Etiket.objects.get(id=etiket_id)
            if not etiket.aktif:
                # Etiket geçerli ve aktif değil, step 2'ye geç
                request.session['add_pet_step'] = 2
            else:
                # Etiket zaten aktif, session'ı temizle ve hata göster
                del request.session['etiket_id']
                messages.error(request, "Bu etiket zaten aktif!")
        except Etiket.DoesNotExist:
            # Etiket bulunamadı, session'ı temizle
            del request.session['etiket_id']
            messages.error(request, "Etiket bulunamadı. Lütfen tekrar deneyin.")
    
    step = request.session.get('add_pet_step', 1)

    if step == 1:
        if request.method == 'POST':
            form = EtiketForm(request.POST)
            if form.is_valid():
                seri = form.cleaned_data['seri_numarasi']
                try:
                    etiket = Etiket.objects.get(seri_numarasi=seri)
                    if etiket.aktif:
                        messages.error(request, "Bu etiket zaten aktif!")
                    else:
                        request.session['etiket_id'] = etiket.id
                        request.session['add_pet_step'] = 2
                        return redirect('anahtarlik:add_pet')
                except Etiket.DoesNotExist:
                    messages.error(request, "Bu seri numarası sistemde bulunamadı.")
        else:
            form = EtiketForm()
        return render(request, 'anahtarlik/add_pet.html', {'form': form, 'step': 1})

    elif step == 2:
        if 'etiket_id' not in request.session:
            return redirect('anahtarlik:add_pet')

        if request.method == 'POST':
            form = EvcilHayvanForm(request.POST, request.FILES)
            if form.is_valid():
                with transaction.atomic():
                    sahip = get_object_or_404(Sahip, kullanici=request.user)
                    
                    # Race condition önleme: select_for_update ile etiketi kilitle
                    # Etiket sahiplik kontrolü: sadece aktif olmayan etiketler kullanılabilir
                    try:
                        etiket = Etiket.objects.select_for_update().get(
                            id=request.session['etiket_id'],
                            aktif=False  # Sadece aktif olmayan etiketler
                        )
                    except Etiket.DoesNotExist:
                        messages.error(request, "Etiket bulunamadı veya zaten aktif. Lütfen tekrar deneyin.")
                        del request.session['add_pet_step']
                        del request.session['etiket_id']
                        return redirect('anahtarlik:add_pet')
                    
                    # Etiket zaten bir evcil hayvana atanmışsa kontrol et
                    if etiket.evcil_hayvan:
                        messages.error(request, "Bu etiket zaten başka bir evcil hayvana atanmış!")
                        del request.session['add_pet_step']
                        del request.session['etiket_id']
                        return redirect('anahtarlik:add_pet')
                    
                    evcil = form.save(commit=False)
                    evcil.sahip = sahip
                    evcil.save()

                    etiket.evcil_hayvan = evcil
                    # ✅ QR URL'i reverse ile doğru üret
                    etiket.qr_kod_url = f"{settings.SITE_URL}{reverse('etiket:qr_landing', kwargs={'tag_id': etiket.etiket_id})}"
                    etiket.save()
                    
                    # ✅ Etiketi aktifleştir (son kullanma tarihi otomatik set edilir)
                    etiket.aktiflestir(request.user)

                    del request.session['add_pet_step']
                    del request.session['etiket_id']

                    messages.success(request, 'Yeni evcil hayvan eklendi!')
                    return redirect('anahtarlik:kullanici_paneli')
            else:
                logger.warning(f"Form geçersiz: {form.errors}")
        else:
            form = EvcilHayvanForm()
        return render(request, 'anahtarlik/add_pet.html', {'form': form, 'step': 2})

    request.session['add_pet_step'] = 1
    return redirect('anahtarlik:add_pet')


@login_required
def kayip_bildir(request, evcil_hayvan_id):
    evcil_hayvan = get_object_or_404(EvcilHayvan, id=evcil_hayvan_id, sahip__kullanici=request.user)
    if request.method == 'POST':
        evcil_hayvan.kayip_durumu = True
        evcil_hayvan.odul_miktari = request.POST.get('odul_miktari')
        evcil_hayvan.kayip_bildirim_tarihi = timezone.now()
        evcil_hayvan.save()
        messages.success(request, 'Kayıp bildirimi yapıldı!')
        return redirect('anahtarlik:kullanici_paneli')
    return render(request, 'anahtarlik/kayip_bildir.html', {'evcil_hayvan': evcil_hayvan})

def hayvan_bulundu(request, evcil_hayvan_id):
    hayvan = get_object_or_404(EvcilHayvan, id=evcil_hayvan_id)
    
    if hayvan.kayip_durumu:
        hayvan.kayip_durumu = False
        hayvan.kayip_bildirim_tarihi = None
        hayvan.save()
        messages.success(request, f"{hayvan.ad} artık güvende olarak işaretlendi.")
    else:
        messages.info(request, f"{hayvan.ad} zaten kayıp değil.")
    
    return redirect("anahtarlik:pet_detail", pet_id=hayvan.id)




# Evcil hayvan silme işlemi devre dışı - Künye tarihi geçince otomatik gizlenir
@login_required
def delete_pet(request, pet_id):
    """Evcil hayvan silme işlemi devre dışı bırakıldı. Künye tarihi geçince otomatik olarak listeden gizlenir."""
    messages.info(request, 'Evcil hayvan silme işlemi devre dışı bırakıldı. Künye tarihi geçince otomatik olarak listeden gizlenir.')
    return redirect('anahtarlik:kullanici_paneli')


@login_required
def sahip_pro_paketler(request):
    """Sahip kullanıcıları için pro paketleri listele"""
    if not hasattr(request.user, 'sahip'):
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('anahtarlik:ev')
    
    sahip = request.user.sahip
    pro_paketler = SahipProPaket.objects.filter(aktif=True).order_by('siralama', 'fiyat')
    
    # Mevcut aktif abonelik
    aktif_abonelik = sahip.aktif_pro_abonelik
    
    context = {
        'pro_paketler': pro_paketler,
        'aktif_abonelik': aktif_abonelik,
        'sahip': sahip,
    }
    
    return render(request, 'anahtarlik/sahip_pro_paketler.html', context)


@login_required
def sahip_pro_abonelik_al(request, paket_id):
    """Sahip kullanıcısı pro abonelik alır (şimdilik geçici)"""
    if not hasattr(request.user, 'sahip'):
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('anahtarlik:ev')
    
    sahip = request.user.sahip
    paket = get_object_or_404(SahipProPaket, id=paket_id, aktif=True)
    
    # Zaten aktif abonelik var mı kontrol et
    if sahip.aktif_pro_abonelik:
        messages.warning(request, f'Zaten aktif bir pro aboneliğiniz var: {sahip.aktif_pro_abonelik.paket.paket_adi}')
        return redirect('anahtarlik:sahip_pro_paketler')
    
    try:
        with transaction.atomic():
            # Pro abonelik oluştur
            baslangic = timezone.now()
            bitis = baslangic + timezone.timedelta(days=paket.sure_gun)
            
            abonelik = SahipProAbonelik.objects.create(
                sahip=sahip,
                paket=paket,
                baslangic_tarihi=baslangic,
                bitis_tarihi=bitis,
                aktif=True
            )
            
            messages.success(request, f'{paket.paket_adi} paketi başarıyla alındı!')
            
    except Exception as e:
        messages.error(request, f'Abonelik alınırken hata oluştu: {str(e)}')
    
    return redirect('anahtarlik:sahip_pro_paketler')


@login_required
def sahip_pro_panel(request):
    """Sahip pro panel ana sayfası"""
    if not hasattr(request.user, 'sahip'):
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('anahtarlik:ev')
    
    sahip = request.user.sahip
    aktif_abonelik = sahip.aktif_pro_abonelik
    
    # Pro özellikler kontrolü
    pro_ozellikler = {
        'asi_hatirlatma': aktif_abonelik and aktif_abonelik.paket.asi_hatirlatma,
        'veteriner_randevu': aktif_abonelik and aktif_abonelik.paket.veteriner_randevu,
        'ilac_takibi': aktif_abonelik and aktif_abonelik.paket.ilac_takibi,
        'beslenme_programi': aktif_abonelik and aktif_abonelik.paket.beslenme_programi,
        'finansal_takip': aktif_abonelik and aktif_abonelik.paket.finansal_takip,
        'egitim_programi': aktif_abonelik and aktif_abonelik.paket.egitim_programi,
    }
    
    context = {
        'sahip': sahip,
        'aktif_abonelik': aktif_abonelik,
        'pro_ozellikler': pro_ozellikler,
    }
    
    return render(request, 'anahtarlik/sahip_pro_panel.html', context)


def ilce_api(request):
    """İl ID'sine göre ilçeleri döndüren API endpoint - DEPRECATED: districts_for_province kullanın"""
    from core.views import districts_for_province
    return districts_for_province(request)


# === AJAX Endpoints: İl/İlçe/Mahalle Cascade ===

def get_ilceler(request):
    """AJAX: İl seçildiğinde ilçeleri JSON olarak döndür"""
    from .dictionaries import Ilce
    il_id = request.GET.get('il_id')
    if il_id:
        ilceler = Ilce.objects.filter(il_id=il_id).order_by('ad').values('id', 'ad')
        return JsonResponse(list(ilceler), safe=False)
    return JsonResponse([], safe=False)


def get_mahalleler(request):
    """AJAX: İlçe seçildiğinde mahalleleri JSON olarak döndür"""
    from .dictionaries import Mahalle
    ilce_id = request.GET.get('ilce_id')
    if ilce_id:
        mahalleler = Mahalle.objects.filter(ilce_id=ilce_id).order_by('ad').values('id', 'ad')
        return JsonResponse(list(mahalleler), safe=False)
    return JsonResponse([], safe=False)


# ============================================================
# İÇERİK YÖNETİM SİSTEMİ (CMS) - Kullanıcı Dostu Arayüz
# ============================================================

@login_required
def cms_dashboard(request):
    """CMS ana kontrol paneli - basit ve kullanıcı dostu"""
    from .models import HeroSlide, HizmetKarti, AnaSayfaAyar

    # Sadece staff kullanıcılar erişebilir
    if not request.user.is_staff:
        messages.error(request, "Bu sayfaya erişim yetkiniz yok.")
        return redirect('anahtarlik:ev')

    hero_slides = HeroSlide.objects.all().order_by('sira')
    hizmet_kartlari = HizmetKarti.objects.all().order_by('sira')
    ayarlar = AnaSayfaAyar.load()

    context = {
        'hero_slides': hero_slides,
        'hizmet_kartlari': hizmet_kartlari,
        'ayarlar': ayarlar,
        'hero_count': hero_slides.count(),
        'hizmet_count': hizmet_kartlari.count(),
    }

    return render(request, 'anahtarlik/cms/dashboard.html', context)


@login_required
def cms_slide_create(request):
    """Yeni hero slide oluştur"""
    from .models import HeroSlide
    from .forms import HeroSlideForm

    if not request.user.is_staff:
        messages.error(request, "Bu sayfaya erişim yetkiniz yok.")
        return redirect('anahtarlik:ev')

    if request.method == 'POST':
        form = HeroSlideForm(request.POST, request.FILES)
        if form.is_valid():
            slide = form.save()
            messages.success(request, f'✓ "{slide.baslik}" slide\'ı başarıyla oluşturuldu!')
            return redirect('anahtarlik:cms_dashboard')
    else:
        # Yeni slide için varsayılan sıra numarası
        next_sira = HeroSlide.objects.count() + 1
        form = HeroSlideForm(initial={'sira': next_sira, 'aktif': True})

    context = {
        'form': form,
        'title': 'Yeni Hero Slide Oluştur',
        'submit_text': 'Slide Oluştur',
    }

    return render(request, 'anahtarlik/cms/slide_form.html', context)


@login_required
def cms_slide_edit(request, slide_id):
    """Hero slide düzenle"""
    from .models import HeroSlide
    from .forms import HeroSlideForm

    if not request.user.is_staff:
        messages.error(request, "Bu sayfaya erişim yetkiniz yok.")
        return redirect('anahtarlik:ev')

    slide = get_object_or_404(HeroSlide, id=slide_id)

    if request.method == 'POST':
        form = HeroSlideForm(request.POST, request.FILES, instance=slide)
        if form.is_valid():
            slide = form.save()
            messages.success(request, f'✓ "{slide.baslik}" slide\'ı güncellendi!')
            return redirect('anahtarlik:cms_dashboard')
    else:
        form = HeroSlideForm(instance=slide)

    context = {
        'form': form,
        'slide': slide,
        'title': f'Slide Düzenle: {slide.baslik}',
        'submit_text': 'Değişiklikleri Kaydet',
    }

    return render(request, 'anahtarlik/cms/slide_form.html', context)


@login_required
def cms_slide_delete(request, slide_id):
    """Hero slide sil"""
    from .models import HeroSlide

    if not request.user.is_staff:
        messages.error(request, "Bu sayfaya erişim yetkiniz yok.")
        return redirect('anahtarlik:ev')

    slide = get_object_or_404(HeroSlide, id=slide_id)

    if request.method == 'POST':
        baslik = slide.baslik
        slide.delete()
        messages.success(request, f'✓ "{baslik}" slide\'ı silindi.')
        return redirect('anahtarlik:cms_dashboard')

    context = {
        'slide': slide,
    }

    return render(request, 'anahtarlik/cms/slide_confirm_delete.html', context)


@login_required
def cms_slide_toggle(request, slide_id):
    """Hero slide aktif/pasif durumunu değiştir (AJAX)"""
    from .models import HeroSlide

    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Yetkiniz yok'})

    slide = get_object_or_404(HeroSlide, id=slide_id)
    slide.aktif = not slide.aktif
    slide.save()

    return JsonResponse({
        'success': True,
        'aktif': slide.aktif,
        'message': f'"{slide.baslik}" {"aktif" if slide.aktif else "pasif"} edildi.'
    })


@login_required
def cms_hizmet_create(request):
    """Yeni hizmet kartı oluştur"""
    from .models import HizmetKarti
    from .forms import HizmetKartiForm

    if not request.user.is_staff:
        messages.error(request, "Bu sayfaya erişim yetkiniz yok.")
        return redirect('anahtarlik:ev')

    if request.method == 'POST':
        form = HizmetKartiForm(request.POST)
        if form.is_valid():
            hizmet = form.save()
            messages.success(request, f'✓ "{hizmet.baslik}" hizmeti oluşturuldu!')
            return redirect('anahtarlik:cms_dashboard')
    else:
        # Yeni hizmet için varsayılan sıra numarası
        next_sira = HizmetKarti.objects.count() + 1
        form = HizmetKartiForm(initial={'sira': next_sira, 'aktif': True})

    context = {
        'form': form,
        'title': 'Yeni Hizmet Kartı Oluştur',
        'submit_text': 'Hizmet Oluştur',
    }

    return render(request, 'anahtarlik/cms/hizmet_form.html', context)


@login_required
def cms_hizmet_edit(request, hizmet_id):
    """Hizmet kartı düzenle"""
    from .models import HizmetKarti
    from .forms import HizmetKartiForm

    if not request.user.is_staff:
        messages.error(request, "Bu sayfaya erişim yetkiniz yok.")
        return redirect('anahtarlik:ev')

    hizmet = get_object_or_404(HizmetKarti, id=hizmet_id)

    if request.method == 'POST':
        form = HizmetKartiForm(request.POST, instance=hizmet)
        if form.is_valid():
            hizmet = form.save()
            messages.success(request, f'✓ "{hizmet.baslik}" hizmeti güncellendi!')
            return redirect('anahtarlik:cms_dashboard')
    else:
        form = HizmetKartiForm(instance=hizmet)

    context = {
        'form': form,
        'hizmet': hizmet,
        'title': f'Hizmet Düzenle: {hizmet.baslik}',
        'submit_text': 'Değişiklikleri Kaydet',
    }

    return render(request, 'anahtarlik/cms/hizmet_form.html', context)


@login_required
def cms_hizmet_delete(request, hizmet_id):
    """Hizmet kartı sil"""
    from .models import HizmetKarti

    if not request.user.is_staff:
        messages.error(request, "Bu sayfaya erişim yetkiniz yok.")
        return redirect('anahtarlik:ev')

    hizmet = get_object_or_404(HizmetKarti, id=hizmet_id)

    if request.method == 'POST':
        baslik = hizmet.baslik
        hizmet.delete()
        messages.success(request, f'✓ "{baslik}" hizmeti silindi.')
        return redirect('anahtarlik:cms_dashboard')

    context = {
        'hizmet': hizmet,
    }

    return render(request, 'anahtarlik/cms/hizmet_confirm_delete.html', context)


@login_required
def cms_hizmet_toggle(request, hizmet_id):
    """Hizmet kartı aktif/pasif durumunu değiştir (AJAX)"""
    from .models import HizmetKarti

    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Yetkiniz yok'})

    hizmet = get_object_or_404(HizmetKarti, id=hizmet_id)
    hizmet.aktif = not hizmet.aktif
    hizmet.save()

    return JsonResponse({
        'success': True,
        'aktif': hizmet.aktif,
        'message': f'"{hizmet.baslik}" {"aktif" if hizmet.aktif else "pasif"} edildi.'
    })


@login_required
def cms_ayarlar(request):
    """Ana sayfa genel ayarları düzenle"""
    from .models import AnaSayfaAyar
    from .forms import AnaSayfaAyarForm

    if not request.user.is_staff:
        messages.error(request, "Bu sayfaya erişim yetkiniz yok.")
        return redirect('anahtarlik:ev')

    ayarlar = AnaSayfaAyar.load()

    if request.method == 'POST':
        form = AnaSayfaAyarForm(request.POST, instance=ayarlar)
        if form.is_valid():
            form.save()
            messages.success(request, '✓ Ana sayfa ayarları güncellendi!')
            return redirect('anahtarlik:cms_dashboard')
    else:
        form = AnaSayfaAyarForm(instance=ayarlar)

    context = {
        'form': form,
        'ayarlar': ayarlar,
    }

    return render(request, 'anahtarlik/cms/ayarlar.html', context)
