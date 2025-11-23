# ilan/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, F, Sum, Count
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from django import forms
from django.conf import settings
import stripe

from .models import HayvanProfili, Ilan, IlanKategori, KrediHareketi, HayvanResmi, KrediPaketi
from .forms import HayvanProfiliForm, IlanForm, IlanAramaForm
from anahtarlik.dictionaries import Il, Ilce, Tur, Irk
from anahtarlik.models import SahipProAbonelik
from collections import defaultdict


def get_kullanici_kredi_bakiye(user):
    """
    Kullanıcının gerçek kredi bakiyesini hesaplar
    KrediHareketi tablosundan tüm işlemleri toplayarak hesaplanır
    """
    if not user.is_authenticated:
        return 0
    
    try:
        # Tüm kredi hareketlerini topla
        hareketler = KrediHareketi.objects.filter(kullanici=user)
        toplam = sum(hareket.miktar for hareket in hareketler)
        return max(0, toplam)  # Negatif olamaz
    except Exception:
        return 0


def ilan_listesi(request):
    """İlan listesi sayfası"""
    
    # Arama formu
    arama_form = IlanAramaForm(request.GET)
    
    # Temel queryset - aktif, onaylanmış ve süresi dolmamış ilanlar
    now = timezone.now()
    temel_ilanlar = Ilan.objects.filter(
        aktif=True,
        onaylandi=True,
        bitis_tarihi__gt=now  # Süresi dolmamış ilanlar
    )

    ilanlar = temel_ilanlar.select_related(
        'hayvan_profili',
        'hayvan_profili__kullanici'
    ).prefetch_related(
        'hayvan_profili__resimler'
    )

    tur_sayilari = {
        kayit['hayvan_profili__tur_id']: kayit['toplam']
        for kayit in temel_ilanlar.values('hayvan_profili__tur_id').annotate(toplam=Count('id'))
    }
    irk_sayilari = {
        kayit['hayvan_profili__irk_id']: kayit['toplam']
        for kayit in temel_ilanlar.values('hayvan_profili__irk_id').annotate(toplam=Count('id'))
    }

    irk_gruplari = defaultdict(list)
    for irk in Irk.objects.select_related('tur').all():
        irk.ilan_sayisi = irk_sayilari.get(irk.id, 0)
        irk_gruplari[irk.tur_id].append(irk)

    tum_turler = []
    for tur in Tur.objects.all():
        tur.ilan_sayisi = tur_sayilari.get(tur.id, 0)
        if tur.ilan_sayisi > 0:
            tur.tur_irklari = [irk for irk in irk_gruplari.get(tur.id, []) if irk.ilan_sayisi > 0]
            tum_turler.append(tur)
    
    # Filtreleme
    if arama_form.is_valid():
        arama = arama_form.cleaned_data.get('arama')
        if arama:
            ilanlar = ilanlar.filter(
                Q(baslik__icontains=arama) |
                Q(aciklama__icontains=arama) |
                Q(hayvan_profili__hayvan_adi__icontains=arama)
            )
        
        ilan_turu = arama_form.cleaned_data.get('ilan_turu')
        if ilan_turu:
            ilanlar = ilanlar.filter(ilan_turu=ilan_turu)
        
        tur = arama_form.cleaned_data.get('tur')
        if tur:
            ilanlar = ilanlar.filter(hayvan_profili__tur=tur)
        
        irk = arama_form.cleaned_data.get('irk')
        if irk:
            ilanlar = ilanlar.filter(hayvan_profili__irk=irk)
        
        il = arama_form.cleaned_data.get('il')
        if il:
            ilanlar = ilanlar.filter(hayvan_profili__il=il)
        
        ilce = arama_form.cleaned_data.get('ilce')
        if ilce:
            ilanlar = ilanlar.filter(hayvan_profili__ilce=ilce)
        
        # Debug: Filtreleme sonuçlarını kontrol et
        print(f"Filtreleme sonrası ilan sayısı: {ilanlar.count()}")
        print(f"Aktif filtreler: arama={arama}, ilan_turu={ilan_turu}, tur={tur}, irk={irk}, il={il}, ilce={ilce}")
        
        min_fiyat = arama_form.cleaned_data.get('min_fiyat')
        if min_fiyat:
            ilanlar = ilanlar.filter(fiyat__gte=min_fiyat)
        
        max_fiyat = arama_form.cleaned_data.get('max_fiyat')
        if max_fiyat:
            ilanlar = ilanlar.filter(fiyat__lte=max_fiyat)
        
        onemli_ilanlar = arama_form.cleaned_data.get('onemli_ilanlar')
        if onemli_ilanlar:
            ilanlar = ilanlar.filter(onemli_mi=True)
    
    # Vitrin ilanları (öne çıkan) - filtreleme SONRASI
    vitrin_queryset = ilanlar.filter(onemli_mi=True)
    normal_ilanlar = ilanlar.filter(onemli_mi=False)
    toplam_vitrin = vitrin_queryset.count()

    max_vitrin_goster = 16
    page_number = request.GET.get('page')
    onemli_filtresi_aktif = bool(request.GET.get('onemli_ilanlar'))

    try:
        current_page = int(page_number)
    except (TypeError, ValueError):
        current_page = 1

    vitrin_page_obj = None
    normal_paginator = None
    normal_sayisi = 0

    if onemli_filtresi_aktif:
        show_vitrin = toplam_vitrin > 0
        vitrin_paginator = Paginator(vitrin_queryset, max_vitrin_goster)
        vitrin_page_obj = vitrin_paginator.get_page(page_number)
        vitrin_ilanlar_goster = list(vitrin_page_obj.object_list)
        vitrin_kalan = max(vitrin_paginator.count - vitrin_page_obj.end_index(), 0)
        normal_sayfa_boyutu = 12
        normal_ilanlar = normal_ilanlar.none()
        page_obj = None
    else:
        show_vitrin = current_page == 1 and toplam_vitrin > 0
        if show_vitrin:
            vitrin_ilanlar_goster = list(vitrin_queryset[:max_vitrin_goster])
            vitrin_kalan = max(toplam_vitrin - len(vitrin_ilanlar_goster), 0)
            normal_sayfa_boyutu = max(12 - len(vitrin_ilanlar_goster) // 2, 6)
        else:
            vitrin_ilanlar_goster = []
            vitrin_kalan = toplam_vitrin
            normal_sayfa_boyutu = 12

        normal_paginator = Paginator(normal_ilanlar, normal_sayfa_boyutu)
        page_obj = normal_paginator.get_page(page_number)
        normal_sayisi = normal_paginator.count
    
    # Toplam ilan sayısı (vitrin + normal)
    toplam_ilan_sayisi = toplam_vitrin + normal_sayisi
    
    has_normal = page_obj.paginator.count > 0 if page_obj else False
    bos_durum = not vitrin_ilanlar_goster and not has_normal and toplam_vitrin == 0

    context = {
        'page_obj': page_obj,
        'vitrin_page_obj': vitrin_page_obj,
        'arama_form': arama_form,
        'toplam_ilan': toplam_ilan_sayisi,
        'tum_turler': tum_turler,  # Tüm türler dinamik olarak
        'show_vitrin': show_vitrin,
        'vitrin_ilanlar_goster': vitrin_ilanlar_goster,
        'vitrin_kalan_sayisi': vitrin_kalan,
        'normal_ilan_sayisi': normal_sayisi,
        'vitrin_ilan_sayisi': toplam_vitrin,
        'bos_durum': bos_durum,
        'onemli_filtresi': onemli_filtresi_aktif,
    }
    
    return render(request, 'ilan/ilan_listesi.html', context)


def ilan_detay(request, ilan_id):
    """İlan detay sayfası"""

    queryset = Ilan.objects.select_related(
        'hayvan_profili',
        'hayvan_profili__kullanici'
    ).prefetch_related(
        'hayvan_profili__resimler'
    )

    filtre = Q(id=ilan_id)
    from django.utils import timezone as tz
    now = tz.now()

    if request.user.is_authenticated:
        # Kullanıcı kendi ilanını görebilir (süresi dolmuş olsa bile)
        filtre &= (Q(aktif=True, onaylandi=True, bitis_tarihi__gt=now) | Q(hayvan_profili__kullanici=request.user))
    else:
        # Misafir kullanıcılar sadece aktif, onaylanmış ve süresi dolmamış ilanları görebilir
        filtre &= Q(aktif=True, onaylandi=True, bitis_tarihi__gt=now)

    ilan = get_object_or_404(queryset, filtre)
    
    # Görüntülenme sayısını artır
    Ilan.objects.filter(id=ilan_id).update(
        goruntulenme_sayisi=F('goruntulenme_sayisi') + 1
    )
    
    # Benzer ilanlar (aynı tür)
    benzer_ilanlar = Ilan.objects.filter(
        hayvan_profili__tur=ilan.hayvan_profili.tur,
        aktif=True,
        onaylandi=True
    ).exclude(id=ilan_id)[:4]
    
    # Satıcı istatistikleri (gerçekçi veriler)
    kullanici = ilan.hayvan_profili.kullanici
    aktif_ilan_sayisi = Ilan.objects.filter(
        hayvan_profili__kullanici=kullanici,
        aktif=True,
        onaylandi=True
    ).count()
    
    toplam_ilan_sayisi = Ilan.objects.filter(
        hayvan_profili__kullanici=kullanici
    ).count()
    
    # İletişim bilgileri (sahip → misafir önceliği)
    ilan_sahibi_tel = ''
    ilan_sahibi_whatsapp = ''
    if hasattr(kullanici, 'sahip') and kullanici.sahip.telefon:
        ilan_sahibi_tel = kullanici.sahip.telefon
    elif hasattr(kullanici, 'misafir_profili') and kullanici.misafir_profili.telefon:
        ilan_sahibi_tel = kullanici.misafir_profili.telefon

    if ilan_sahibi_tel:
        temiz_tel = ''.join(filter(str.isdigit, ilan_sahibi_tel))
        if temiz_tel.startswith('0'):
            temiz_tel = temiz_tel[1:]
        ilan_sahibi_whatsapp = temiz_tel
    
    # Üyelik süresi (yıl)
    from django.utils import timezone
    from datetime import timedelta
    uyelik_suresi = (timezone.now() - kullanici.date_joined).days // 365
    
    context = {
        'ilan': ilan,
        'benzer_ilanlar': benzer_ilanlar,
        'aktif_ilan_sayisi': aktif_ilan_sayisi,
        'toplam_ilan_sayisi': toplam_ilan_sayisi,
        'uyelik_suresi': uyelik_suresi,
        'ilan_sahibi_tel': ilan_sahibi_tel,
        'ilan_sahibi_whatsapp': ilan_sahibi_whatsapp,
    }
    
    return render(request, 'ilan/ilan_detay.html', context)


@login_required
def hayvan_profili_olustur(request):
    """Hayvan profili oluşturma sayfası - Tüm kullanıcılar için (sahip kullanıcıları da dahil)"""
    
    # Kredi kontrolü (tüm kullanıcılar için)
    kullanici_bakiye = get_kullanici_kredi_bakiye(request.user)
    ilan_ucreti = 100  # Hayvan profili + ilan ücreti
    
    if kullanici_bakiye < ilan_ucreti:
        messages.error(request, f'Yetersiz kredi! İlan vermek için en az {ilan_ucreti} kredi gereklidir. Lütfen kredi satın alın.')
        return redirect('ilan:kredi_satin_al')
    
    if request.method == 'POST':
        form = HayvanProfiliForm(request.POST, request.FILES)
        if form.is_valid():
            # Form verilerini session'da sakla
            dogum_tarihi = form.cleaned_data['dogum_tarihi']
            request.session['hayvan_profili_data'] = {
                'hayvan_adi': form.cleaned_data['hayvan_adi'],
                'tur_id': form.cleaned_data['tur'].id,
                'tur_ad': form.cleaned_data['tur'].ad,
                'irk_id': form.cleaned_data['irk'].id,
                'irk_ad': form.cleaned_data['irk'].ad,
                'dogum_tarihi': dogum_tarihi.strftime('%Y-%m-%d') if dogum_tarihi else None,
                'yas': None,  # Yaş artık hesaplanacak, session'da saklamıyoruz
                'cinsiyet': form.cleaned_data['cinsiyet'],
                'telefon': form.cleaned_data.get('telefon', ''),
                'asi_durumu': form.cleaned_data['asi_durumu'],
                'ic_parazit': form.cleaned_data['ic_parazit'],
                'dis_parazit': form.cleaned_data['dis_parazit'],
                'sehir_disi_gonderim': form.cleaned_data['sehir_disi_gonderim'],
                'il_id': form.cleaned_data['il'].id,
                'il_ad': form.cleaned_data['il'].ad,
                'ilce_id': form.cleaned_data['ilce'].id,
                'ilce_ad': form.cleaned_data['ilce'].ad,
                'mahalle_id': form.cleaned_data['mahalle'].id if form.cleaned_data['mahalle'] else None,
                'aciklama': form.cleaned_data['aciklama'],
            }
            
            # Manuel mahalle girişini ekle
            mahalle_diger = request.POST.get('mahalle_diger', '').strip()
            if mahalle_diger:
                request.session['hayvan_profili_data']['mahalle_diger'] = mahalle_diger
            
            # Resimleri session'da sakla (geçici)
            resimler = request.FILES.getlist('resimler')
            if resimler:
                # Maksimum 3 resim kontrolü
                if len(resimler) > 3:
                    messages.warning(request, 'Maksimum 3 resim yüklenebilir. İlk 3 resim seçildi.')
                    resimler = resimler[:3]
                
                # Resimleri geçici olarak kaydet
                resim_paths = []
                for i, resim in enumerate(resimler):
                    # Geçici dosya adı oluştur
                    import uuid
                    temp_name = f"temp_{uuid.uuid4()}_{resim.name}"
                    temp_path = f"temp_images/{temp_name}"
                    
                    # Geçici olarak kaydet
                    from django.core.files.storage import default_storage
                    saved_path = default_storage.save(temp_path, resim)
                    resim_paths.append(saved_path)
                
                request.session['hayvan_profili_resimler'] = resim_paths
            
            # Profil fotoğrafını da session'da sakla
            if 'profil_fotografi' in request.FILES:
                profil_foto = request.FILES['profil_fotografi']
                import uuid
                temp_name = f"temp_{uuid.uuid4()}_{profil_foto.name}"
                temp_path = f"temp_images/{temp_name}"
                
                from django.core.files.storage import default_storage
                saved_path = default_storage.save(temp_path, profil_foto)
                request.session['hayvan_profili_profil_foto'] = saved_path
            
            messages.success(request, 'Hayvan profili bilgileri kaydedildi. Şimdi ilan oluşturabilirsiniz.')
            return redirect('ilan:ilan_olustur')
        # Form validasyonu başarısız olduysa, form hatalarla birlikte geri döndürülür
        # Bu durumda form'da POST data var, form.__init__ içinde tür'e göre ırklar filtrelenecek
    else:
        form = HayvanProfiliForm()
    
    # Kullanıcı bakiyesini hesapla
    kullanici_bakiye = get_kullanici_kredi_bakiye(request.user)
    profil_olusturma_ucreti = 100  # Hayvan profili oluşturma ücreti
    
    context = {
        'form': form,
        'kullanici_bakiye': kullanici_bakiye,
        'profil_olusturma_ucreti': profil_olusturma_ucreti,
    }
    
    return render(request, 'ilan/hayvan_profili_olustur.html', context)


@login_required
def hayvan_profili_detay(request, profil_id):
    """Hayvan profili detay sayfası"""
    
    hayvan_profili = get_object_or_404(
        HayvanProfili.objects.prefetch_related('resimler'),
        id=profil_id,
        kullanici=request.user
    )
    
    # Bu profille oluşturulan ilanlar (kullanıcı kendi ilanlarını görebilir, süresi dolmuş olsa bile)
    ilanlar = hayvan_profili.ilanlar.filter(aktif=True).order_by('-olusturulma_tarihi')
    
    context = {
        'hayvan_profili': hayvan_profili,
        'ilanlar': ilanlar,
    }
    
    return render(request, 'ilan/hayvan_profili_detay.html', context)


@login_required
def ilan_olustur(request):
    """İlan oluşturma - Tüm kullanıcılar için (sahip kullanıcıları da dahil)"""
    
    # Session'da hayvan profili verisi var mı kontrol et
    if 'hayvan_profili_data' not in request.session:
        # Sahip kullanıcısı ise hayvan seçimi sayfasına yönlendir, değilse hayvan profili oluştur
        if hasattr(request.user, 'sahip'):
            messages.info(request, 'İlan vermek için mevcut hayvanlarınızdan birini seçin veya yeni hayvan profili oluşturun.')
            return redirect('ilan:sahip_hayvan_secimi')
        else:
            messages.info(request, 'İlan vermek için önce hayvan profili oluşturmalısınız.')
            return redirect('ilan:hayvan_profili_olustur')
    
    # Session'dan veri al
    profil_data = request.session['hayvan_profili_data']
    
    # Doğum tarihinden yaş hesapla (template'de kullanmak için)
    if profil_data.get('dogum_tarihi'):
        from datetime import datetime, date
        try:
            dogum_tarihi = datetime.strptime(profil_data['dogum_tarihi'], '%Y-%m-%d').date()
            today = date.today()
            age_years = today.year - dogum_tarihi.year
            age_months = today.month - dogum_tarihi.month
            if age_months < 0:
                age_years -= 1
                age_months += 12
            if age_years == 0:
                if age_months == 0:
                    profil_data['yas'] = "Yeni doğan"
                elif age_months == 1:
                    profil_data['yas'] = "1 Aylık"
                else:
                    profil_data['yas'] = f"{age_months} Aylık"
            elif age_years == 1:
                if age_months == 0:
                    profil_data['yas'] = "1 Yaşında"
                else:
                    profil_data['yas'] = f"1 Yaş {age_months} Aylık"
            else:
                if age_months == 0:
                    profil_data['yas'] = f"{age_years} Yaşında"
                else:
                    profil_data['yas'] = f"{age_years} Yaş {age_months} Aylık"
        except (ValueError, TypeError):
            profil_data['yas'] = "Bilinmiyor"
    else:
        profil_data['yas'] = "Bilinmiyor"
    
    # Kredi kontrolü - Gerçek bakiyeyi hesapla
    kullanici_bakiye = get_kullanici_kredi_bakiye(request.user)
    ilan_ucreti = 100  # Hayvan profili + ilan ücreti
    
    if kullanici_bakiye < ilan_ucreti:
        messages.error(request, f"Yetersiz kredi! İlan vermek için {ilan_ucreti} kredi gerekli. Mevcut bakiyeniz: {kullanici_bakiye}")
        return redirect('ilan:kredi_satin_al')
    
    if request.method == 'POST':
        # Hayvan profili ve ilan oluştur
        from django.db import transaction
        
        try:
            with transaction.atomic():
                # Hayvan profili oluştur
                from anahtarlik.dictionaries import Tur, Irk, Il, Ilce
                
                # Mahalle seçimi: dropdown seçim veya manuel giriş
                from anahtarlik.dictionaries import Mahalle
                
                mahalle_obj = None
                if profil_data.get('mahalle_id'):
                    mahalle_obj = Mahalle.objects.get(id=profil_data['mahalle_id'])
                
                # Doğum tarihini parse et
                dogum_tarihi = None
                if profil_data.get('dogum_tarihi'):
                    from datetime import datetime
                    try:
                        dogum_tarihi = datetime.strptime(profil_data['dogum_tarihi'], '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        dogum_tarihi = None
                
                # Telefon numarasını al (session'dan veya kullanıcı profili'nden)
                telefon = profil_data.get('telefon', '')
                if not telefon and hasattr(request.user, 'sahip'):
                    telefon = request.user.sahip.telefon or ''
                
                # Telefon zorunlu kontrolü
                if not telefon:
                    messages.error(request, 'Telefon numarası zorunludur. Lütfen telefon numaranızı girin.')
                    return redirect('ilan:hayvan_profili_olustur')
                
                # Profil fotoğrafı kontrolü
                if 'hayvan_profili_profil_foto' not in request.session:
                    messages.error(request, 'Profil fotoğrafı zorunludur. Lütfen profil fotoğrafı yükleyin.')
                    return redirect('ilan:hayvan_profili_olustur')
                
                # Geçici profil fotoğrafını oku
                from django.core.files.storage import default_storage
                from django.core.files.base import ContentFile
                import uuid
                
                temp_path = request.session['hayvan_profili_profil_foto']
                if not default_storage.exists(temp_path):
                    messages.error(request, 'Profil fotoğrafı bulunamadı. Lütfen tekrar yükleyin.')
                    return redirect('ilan:hayvan_profili_olustur')
                
                # Geçici dosyayı oku ve profil fotoğrafı için hazırla
                with default_storage.open(temp_path, 'rb') as temp_file:
                    temp_filename = temp_path.split('/')[-1]
                    safe_filename = f"profile_{uuid.uuid4().hex}_{temp_filename}"
                    profil_fotografi = ContentFile(temp_file.read())
                    profil_fotografi.name = safe_filename
                
                hayvan_profili = HayvanProfili.objects.create(
                    kullanici=request.user,
                    hayvan_adi=profil_data['hayvan_adi'],
                    tur=Tur.objects.get(id=profil_data['tur_id']),
                    irk=Irk.objects.get(id=profil_data['irk_id']),
                    dogum_tarihi=dogum_tarihi,
                    cinsiyet=profil_data['cinsiyet'],
                    telefon=telefon,  # Session'dan veya Sahip'ten
                    asi_durumu=profil_data.get('asi_durumu', False),
                    ic_parazit=profil_data.get('ic_parazit', False),
                    dis_parazit=profil_data.get('dis_parazit', False),
                    sehir_disi_gonderim=profil_data.get('sehir_disi_gonderim', False),
                    il=Il.objects.get(id=profil_data['il_id']),
                    ilce=Ilce.objects.get(id=profil_data['ilce_id']),
                    mahalle=mahalle_obj,  # Dropdown seçimi veya None
                    mahalle_diger=profil_data.get('mahalle_diger', ''),  # Manuel girilen mahalle veya boş
                    aciklama=profil_data.get('aciklama', ''),
                    profil_fotografi=profil_fotografi  # Profil fotoğrafı zorunlu
                )
                
                # Profil fotoğrafını kaydet (geçici dosyayı sil - zaten create'de kaydedildi)
                if default_storage.exists(temp_path):
                    default_storage.delete(temp_path)
                
                # Resimleri kaydet
                if 'hayvan_profili_resimler' in request.session:
                    from django.core.files.storage import default_storage
                    import uuid
                    import os
                    
                    for i, temp_path in enumerate(request.session['hayvan_profili_resimler']):
                        if default_storage.exists(temp_path):
                            # Dosya adını güvenli hale getir
                            temp_filename = temp_path.split('/')[-1]
                            safe_filename = f"{hayvan_profili.id}_{i+1}_{uuid.uuid4().hex}_{temp_filename}"
                            final_path = f"hayvan_resimleri/{safe_filename}"
                            
                            try:
                                # Dosyayı oku
                                with default_storage.open(temp_path, 'rb') as temp_file:
                                    # Kalıcı konuma kaydet - doğrudan FileField'a kaydet
                                    hayvan_resmi = HayvanResmi.objects.create(
                                        hayvan_profili=hayvan_profili,
                                        sira=i + 1
                                    )
                                    
                                    # Resim kaydetme işleminin başarılı olduğundan emin ol
                                    hayvan_resmi.resim.save(safe_filename, temp_file, save=True)
                                    
                                # Geçici dosyayı sil  
                                if default_storage.exists(temp_path):
                                    default_storage.delete(temp_path)
                            except Exception as e:
                                # Eğer kaydetme başarısız olursa HayvanResmi objesini de sil
                                try:
                                    if 'hayvan_resmi' in locals():
                                        hayvan_resmi.delete()
                                except:
                                    pass
                                continue
                
                # İlan oluştur
                baslik = request.POST.get('baslik', f"Sevimli {hayvan_profili.hayvan_adi} Sahiplendirme İlanı")
                aciklama = request.POST.get('aciklama', f"{hayvan_profili.hayvan_adi} için yeni bir yuva arıyoruz. {hayvan_profili.tur.ad} cinsi, {hayvan_profili.irk.ad} ırkı. {hayvan_profili.get_cinsiyet_display()} cinsiyet. Sevgi dolu bir aile arıyoruz!")
                onemli_mi = request.POST.get('onemli_mi') == 'on'
                
                toplam_ucret = ilan_ucreti
                if onemli_mi:
                    toplam_ucret += 50  # Öne çıkarma ücreti
                
                if kullanici_bakiye < toplam_ucret:
                    messages.error(request, f"Yetersiz bakiye! İlan vermek için {toplam_ucret} kredi gerekli.")
                    return redirect('ilan:kredi_durumu')
                
                ilan = Ilan.objects.create(
                    hayvan_profili=hayvan_profili,
                    baslik=baslik,
                    ilan_turu='SAHIPLENDIRME',
                    aciklama=aciklama,
                    onemli_mi=onemli_mi,
                    onaylandi=False  # Admin onayı gerekli
                )
                
                # Kredi harcama kaydı
                KrediHareketi.objects.create(
                    kullanici=request.user,
                    hareket_turu=KrediHareketi.HAREKET_ILAN_VERME,
                    miktar=-ilan_ucreti,
                    aciklama=f"İlan oluşturma: {ilan.baslik}",
                    ilan=ilan
                )
                
                if onemli_mi:
                    KrediHareketi.objects.create(
                        kullanici=request.user,
                        hareket_turu=KrediHareketi.HAREKET_ONEMLI_ILAN,
                        miktar=-50,
                        aciklama=f"Öne çıkarma: {ilan.baslik}",
                        ilan=ilan
                    )
                
                # Boş resimleri temizle (Dosya kaydedilmemiş HayvanResmi objelerini sil)
                hayvan_profili.resimler.filter(Q(resim__isnull=True) | Q(resim='')).delete()
                
                # Session'ı temizle
                request.session.pop('hayvan_profili_data', None)
                request.session.pop('hayvan_profili_resimler', None)
                request.session.pop('hayvan_profili_profil_foto', None)
                
                messages.success(request, f'İlan başarıyla oluşturuldu! Admin onayı bekleniyor. {toplam_ucret} kredi harcandı.')
                return redirect('ilan:kullanici_ilanlari')
        except Exception as e:
            import traceback
            print(f"İlan oluşturma hatası: {e}")
            print(traceback.format_exc())
            messages.error(request, f'İlan oluşturulurken bir hata oluştu: {str(e)}')
            return redirect('ilan:hayvan_profili_olustur')
    
    context = {
        'kullanici_bakiye': kullanici_bakiye,
        'ilan_ucreti': ilan_ucreti,
        'profil_data': profil_data,
    }
    
    return render(request, 'ilan/ilan_olustur.html', context)


@login_required
def ilan_olustur_profil(request, hayvan_profili_id):
    """Belirli hayvan profili için ilan oluşturma"""
    
    hayvan_profili = get_object_or_404(
        HayvanProfili,
        id=hayvan_profili_id,
        kullanici=request.user,
        aktif=True
    )
    
    # Bu hayvan profili için zaten aktif ilan var mı kontrol et
    mevcut_ilan = Ilan.objects.filter(
        hayvan_profili=hayvan_profili,
        aktif=True
    ).first()
    
    if mevcut_ilan:
        messages.warning(request, f'Bu hayvan profili için zaten aktif bir ilan bulunmaktadır: "{mevcut_ilan.baslik}"')
        return redirect('ilan:ilan_detay', ilan_id=mevcut_ilan.id)
    
    # Kredi kontrolü
    kullanici_bakiye = get_kullanici_kredi_bakiye(request.user)
    ilan_ucreti = 100  # İlan ücreti
    onemli_ilan_ucreti = 50  # Öne çıkarma ücreti
    
    # Kredi yetersizse engelle
    if kullanici_bakiye < ilan_ucreti:
        messages.error(request, f'Yetersiz kredi! İlan vermek için en az {ilan_ucreti} kredi gereklidir. Mevcut bakiyeniz: {kullanici_bakiye}')
        return redirect('ilan:kredi_satin_al')
    
    if request.method == 'POST':
        form = IlanForm(request.POST, user=request.user)
        form.fields['hayvan_profili'].initial = hayvan_profili
        form.fields['hayvan_profili'].widget = forms.HiddenInput()
        if form.is_valid():
            with transaction.atomic():
                # Toplam ücret hesapla
                toplam_ucret = ilan_ucreti
                if form.cleaned_data.get('onemli_mi'):
                    toplam_ucret += onemli_ilan_ucreti
                
                # Bakiye kontrolü
                kullanici_bakiye = get_kullanici_kredi_bakiye(request.user)
                if kullanici_bakiye < toplam_ucret:
                    messages.error(request, f"Yetersiz kredi! İlan vermek için {toplam_ucret} kredi gerekli. Mevcut bakiyeniz: {kullanici_bakiye}")
                    return redirect('ilan:kredi_satin_al')
                
                # İlan oluştur
                ilan = form.save(commit=False)
                ilan.hayvan_profili = hayvan_profili
                ilan.onaylandi = False  # Admin onayı gerekli
                ilan.save()
                
                # Kredi harcama kayıtları
                KrediHareketi.objects.create(
                    kullanici=request.user,
                    hareket_turu=KrediHareketi.HAREKET_ILAN_VERME,
                    miktar=-ilan_ucreti,
                    aciklama=f"İlan oluşturuldu: {ilan.baslik}",
                    ilan=ilan
                )
                
                if ilan.onemli_mi:
                    KrediHareketi.objects.create(
                        kullanici=request.user,
                        hareket_turu=KrediHareketi.HAREKET_ONEMLI_ILAN,
                        miktar=-onemli_ilan_ucreti,
                        aciklama=f"Öne çıkarma: {ilan.baslik}",
                        ilan=ilan
                    )
                
                messages.success(request, f'İlan başarıyla oluşturuldu! Admin onayı bekleniyor. {toplam_ucret} kredi harcandı.')
                return redirect('ilan:kullanici_ilanlari')
        else:
            # Form validation hatalarını göster
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = IlanForm(user=request.user)
        form.fields['hayvan_profili'].initial = hayvan_profili
        form.fields['hayvan_profili'].widget = forms.HiddenInput()
    
    context = {
        'form': form,
        'hayvan_profili': hayvan_profili,
        'ilan_ucreti': ilan_ucreti,
        'onemli_ilan_ucreti': onemli_ilan_ucreti,
        'kullanici_bakiye': kullanici_bakiye,
    }
    
    return render(request, 'ilan/ilan_olustur_profil.html', context)


@login_required
def kullanici_ilanlari(request):
    """Kullanıcının ilanları"""
    
    ilanlar = Ilan.objects.filter(
        hayvan_profili__kullanici=request.user
    ).select_related(
        'hayvan_profili'
    ).order_by('-olusturulma_tarihi')
    
    context = {
        'ilanlar': ilanlar,
    }
    
    return render(request, 'ilan/kullanici_ilanlari.html', context)


@login_required
def kredi_durumu(request):
    """Kullanıcı kredi durumu"""
    
    # Kullanıcının kredi hareketleri
    hareketler = KrediHareketi.objects.filter(
        kullanici=request.user
    ).order_by('-tarih')[:20]  # Son 20 hareket
    
    # Mevcut bakiyeyi hesapla
    mevcut_bakiye = get_kullanici_kredi_bakiye(request.user)
    
    # Toplam harcama ve gelir istatistikleri
    toplam_harcama = KrediHareketi.objects.filter(
        kullanici=request.user,
        miktar__lt=0
    ).aggregate(total=Sum('miktar'))['total'] or 0
    
    toplam_gelir = KrediHareketi.objects.filter(
        kullanici=request.user,
        miktar__gt=0
    ).aggregate(total=Sum('miktar'))['total'] or 0
    
    context = {
        'hareketler': hareketler,
        'mevcut_bakiye': mevcut_bakiye,
        'toplam_harcama': abs(toplam_harcama),
        'toplam_gelir': toplam_gelir,
    }
    
    return render(request, 'ilan/kredi_durumu.html', context)


# AJAX endpoints
def ilce_listesi(request):
    """İlçe listesi AJAX endpoint"""
    il_id = request.GET.get('il_id')
    if il_id:
        from anahtarlik.dictionaries import Ilce
        ilceler = Ilce.objects.filter(il_id=il_id).order_by('ad')
        data = [{'id': ilce.id, 'ad': ilce.ad} for ilce in ilceler]
        return JsonResponse(data, safe=False)
    return JsonResponse([], safe=False)


def mahalle_listesi(request):
    """Mahalle listesi AJAX endpoint"""
    ilce_id = request.GET.get('ilce_id')
    if ilce_id:
        from anahtarlik.dictionaries import Mahalle
        mahalleler = Mahalle.objects.filter(ilce_id=ilce_id).order_by('ad')
        data = [{'id': mahalle.id, 'ad': mahalle.ad} for mahalle in mahalleler]
        return JsonResponse(data, safe=False)
    return JsonResponse([], safe=False)


def kredi_kontrol(request):
    """Kredi kontrolü AJAX endpoint"""
    if request.user.is_authenticated:
        kullanici_bakiye = get_kullanici_kredi_bakiye(request.user)
        return JsonResponse({'bakiye': kullanici_bakiye})
    return JsonResponse({'bakiye': 0})


@login_required
def kredi_satin_al(request):
    """Kredi satın alma sayfası"""
    
    # Stripe API key'ini ayarla
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    # Kredi paketlerini veritabanından çek
    kredi_paketleri = KrediPaketi.objects.filter(aktif=True).order_by('sira', 'fiyat')
    
    if request.method == 'POST':
        paket_id = request.POST.get('paket')
        try:
            paket = KrediPaketi.objects.get(id=paket_id, aktif=True)
            
            # Test modu kontrolü
            if getattr(settings, 'STRIPE_TEST_MODE', True):
                # TEST MODU: Direkt kredi ekle
                with transaction.atomic():
                    KrediHareketi.objects.create(
                        kullanici=request.user,
                        hareket_turu=KrediHareketi.HAREKET_SATIN_ALMA,
                        miktar=paket.kredi_adet,
                        aciklama=f"Kredi paketi satın alındı: {paket.ad} (TEST MODU)"
                    )
                
                return JsonResponse({
                    'success': True,
                    'test_mode': True,
                    'message': 'Kredi başarıyla eklendi! (Test Modu)',
                    'paket': {
                        'id': paket.id,
                        'ad': paket.ad,
                        'adet': paket.kredi_adet,
                        'fiyat': float(paket.fiyat)
                    }
                })
            
            # Gerçek Stripe ödeme işlemi
            try:
                payment_intent = stripe.PaymentIntent.create(
                    amount=int(paket.fiyat * 100),  # TL to kuruş
                    currency='try',
                    metadata={
                        'kullanici_id': request.user.id,
                        'kredi_adet': paket.kredi_adet,
                        'paket_id': paket.id,
                        'paket_adi': paket.ad
                    }
                )
                
                return JsonResponse({
                    'success': True,
                    'test_mode': False,
                    'client_secret': payment_intent.client_secret,
                    'paket': {
                        'id': paket.id,
                        'ad': paket.ad,
                        'adet': paket.kredi_adet,
                        'fiyat': float(paket.fiyat)
                    }
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Ödeme işlemi başlatılamadı: {str(e)}'
                })
        except KrediPaketi.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Geçersiz paket seçimi'
            })
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'Geçersiz paket ID'
            })
    
    context = {
        'kredi_paketleri': kredi_paketleri,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    }
    
    return render(request, 'ilan/kredi_satin_al.html', context)


def kredi_odeme_webhook(request):
    """Stripe webhook - ödeme başarılı olduğunda kredi ekleme"""
    import json
    
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
    
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    
    # Ödeme başarılı olduğunda
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        metadata = payment_intent.get('metadata', {})
        
        try:
            kullanici_id = int(metadata.get('kullanici_id'))
            kredi_adet = int(metadata.get('kredi_adet'))
            
            from django.contrib.auth.models import User
            user = User.objects.get(id=kullanici_id)
            
            # Kredi hareketi oluştur
            KrediHareketi.objects.create(
                kullanici=user,
                hareket_turu=KrediHareketi.HAREKET_BAKIYE_EKLEME,
                miktar=kredi_adet,
                aciklama=f"Kredi satın alma: {metadata.get('paket_adi', '')} - {payment_intent['id']}"
            )
            
            print(f"Kredi eklendi: {user.username} - {kredi_adet} kredi")
            
        except Exception as e:
            print(f"Webhook hatası: {e}")
    
    return HttpResponse(status=200)


def irk_listesi(request):
    """Irk listesi AJAX endpoint"""
    tur_id = request.GET.get('tur_id')
    if tur_id:
        irklar = Irk.objects.filter(tur_id=tur_id).order_by('ad')
        data = [{'id': irk.id, 'ad': irk.ad} for irk in irklar]
        return JsonResponse(data, safe=False)
    return JsonResponse([], safe=False)


@login_required
def sahip_hayvan_secimi(request):
    """Sahip kullanıcıları için hayvan seçimi sayfası"""
    
    # Sahip kullanıcısı değilse yönlendir
    if not hasattr(request.user, 'sahip'):
        return redirect('ilan:ilan_olustur')
    
    # Sahibin evcil hayvanları (EvcilHayvan modeli)
    from anahtarlik.models import EvcilHayvan
    from django.db.models import Q
    
    aktif_profiller = HayvanProfili.objects.filter(
        kullanici=request.user,
        ilanlar__aktif=True
    ).distinct()

    ilan_verilmis_hayvan_ids = list(
        aktif_profiller.filter(evcil_hayvan__isnull=False).values_list('evcil_hayvan_id', flat=True)
    )
    ilan_verilmis_hayvan_adlari = list(
        aktif_profiller.filter(evcil_hayvan__isnull=True).values_list('hayvan_adi', flat=True)
    )
    
    evcil_hayvanlar = EvcilHayvan.objects.filter(
        sahip=request.user.sahip
    ).exclude(
        Q(id__in=ilan_verilmis_hayvan_ids) | Q(ad__in=ilan_verilmis_hayvan_adlari)
    ).select_related(
        'tur', 'irk'
    ).order_by('-id')
    
    context = {
        'evcil_hayvanlar': evcil_hayvanlar,
        'ilan_verilmis_hayvan_sayisi': len(ilan_verilmis_hayvan_ids),
    }

    return render(request, 'ilan/sahip_hayvan_secimi.html', context)


@login_required
def sahip_ilan_olustur(request, evcil_hayvan_id):
    """Sahip kullanıcıları için EvcilHayvan'dan ilan oluşturma"""
    
    # Sahip kullanıcısı değilse yönlendir
    if not hasattr(request.user, 'sahip'):
        return redirect('ilan:ilan_olustur')
    
    # EvcilHayvan'ı al
    from anahtarlik.models import EvcilHayvan
    evcil_hayvan = get_object_or_404(
        EvcilHayvan,
        id=evcil_hayvan_id,
        sahip=request.user.sahip
    )
    
    # Kredi kontrolü
    kullanici_bakiye = get_kullanici_kredi_bakiye(request.user)
    ilan_ucreti = 100  # İlan ücreti
    onemli_ilan_ucreti = 50  # Öne çıkarma ücreti
    
    # Kredi yetersizse engelle
    if kullanici_bakiye < ilan_ucreti:
        messages.error(request, f'Yetersiz kredi! İlan vermek için en az {ilan_ucreti} kredi gereklidir. Mevcut bakiyeniz: {kullanici_bakiye}. Lütfen kredi satın alın.')
        return redirect('ilan:kredi_satin_al')
    
    if request.method == 'POST':
        # EvcilHayvan'dan HayvanProfili oluştur - SNAPSHOT MEKANİZMASI
        from django.db import transaction
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        import uuid
        import os

        try:
            with transaction.atomic():
                # Aktif ilan kontrolü - aynı EvcilHayvan için aktif ilan varsa engelle
                # NOT: Artık evcil_hayvan=None olduğu için, hayvan_adi ve sahip bilgisiyle kontrol ediyoruz
                aktif_ilanlar = Ilan.objects.filter(
                    hayvan_profili__kullanici=request.user,
                    hayvan_profili__hayvan_adi=evcil_hayvan.ad,
                    hayvan_profili__tur=evcil_hayvan.tur,
                    hayvan_profili__irk=evcil_hayvan.irk,
                    aktif=True
                ).exists()
                
                if aktif_ilanlar:
                    messages.warning(request, 'Bu evcil hayvan için zaten aktif bir ilanınız bulunuyor.')
                    return redirect('ilan:sahip_hayvan_secimi')

                # İlan oluşturulduğu anda SNAPSHOT al - tüm verileri kopyala
                # Her ilan için yeni HayvanProfili oluştur (mevcut profil kontrolü yok)
                
                # Fotoğraf işleme - önce yeni yüklenen fotoğrafı kontrol et, yoksa snapshot al
                profil_fotografi = None
                
                # Yeni fotoğraf yüklendi mi kontrol et
                if 'profil_fotografi' in request.FILES:
                    # Kullanıcı yeni fotoğraf yükledi
                    yeni_foto = request.FILES['profil_fotografi']
                    try:
                        # Yeni dosya adı oluştur
                        file_extension = os.path.splitext(yeni_foto.name)[1] or '.jpg'
                        new_filename = f"hayvan_profilleri/snapshot_{uuid.uuid4().hex}{file_extension}"
                        
                        # Yeni fotoğrafı kaydet
                        profil_fotografi = default_storage.save(
                            new_filename,
                            ContentFile(yeni_foto.read())
                        )
                    except Exception as e:
                        messages.error(request, f'Fotoğraf yüklenirken hata oluştu: {str(e)}')
                        return redirect('ilan:sahip_hayvan_secimi')
                elif evcil_hayvan.resim:
                    # Yeni fotoğraf yok, EvcilHayvan'dan snapshot al
                    try:
                        # Orijinal fotoğrafı oku
                        with evcil_hayvan.resim.open('rb') as source_file:
                            # Yeni dosya adı oluştur
                            original_name = evcil_hayvan.resim.name
                            file_extension = os.path.splitext(original_name)[1] or '.jpg'
                            new_filename = f"hayvan_profilleri/snapshot_{uuid.uuid4().hex}{file_extension}"
                            
                            # Fotoğrafı yeni konuma kopyala (fiziksel kopya)
                            file_content = source_file.read()
                            profil_fotografi = default_storage.save(
                                new_filename,
                                ContentFile(file_content)
                            )
                    except Exception as e:
                        # Fotoğraf kopyalanamazsa hata ver
                        messages.error(request, f'Fotoğraf kopyalanırken hata oluştu: {str(e)}')
                        return redirect('ilan:sahip_hayvan_secimi')
                
                # Fotoğraf zorunlu kontrolü
                if not profil_fotografi:
                    messages.error(request, 'İlan oluşturmak için evcil hayvanınızın fotoğrafı olmalıdır.')
                    return redirect('ilan:sahip_hayvan_secimi')
                
                # Ek resimleri işle (maksimum 3)
                ek_resimler = request.FILES.getlist('resimler')
                if len(ek_resimler) > 3:
                    messages.warning(request, 'Maksimum 3 ek resim yüklenebilir. İlk 3 resim seçildi.')
                    ek_resimler = ek_resimler[:3]
                
                # POST'tan sağlık bilgilerini al
                asi_durumu = request.POST.get('asi_durumu') == 'on'
                ic_parazit = request.POST.get('ic_parazit') == 'on'
                dis_parazit = request.POST.get('dis_parazit') == 'on'
                sehir_disi_gonderim = request.POST.get('sehir_disi_gonderim') == 'on'
                
                # POST'tan konum bilgilerini al
                from anahtarlik.dictionaries import Il, Ilce, Mahalle
                il_id = request.POST.get('il')
                ilce_id = request.POST.get('ilce')
                mahalle_id = request.POST.get('mahalle')
                mahalle_diger = request.POST.get('mahalle_diger', '').strip()
                
                # Konum objelerini al
                il_obj = Il.objects.get(id=il_id) if il_id else request.user.sahip.il
                ilce_obj = Ilce.objects.get(id=ilce_id) if ilce_id else request.user.sahip.ilce
                mahalle_obj = Mahalle.objects.get(id=mahalle_id) if mahalle_id else request.user.sahip.mahalle
                
                # Cinsiyet formatını dönüştür (EvcilHayvan: 'erkek' -> HayvanProfili: 'ERKEK')
                cinsiyet_mapping = {
                    'erkek': 'ERKEK',
                    'disi': 'DISI',
                    'bilinmiyor': 'BILINMIYOR'
                }
                cinsiyet = cinsiyet_mapping.get(evcil_hayvan.cinsiyet, 'BILINMIYOR')
                
                # Telefon numarasını al (POST'tan veya Sahip'ten snapshot)
                telefon = request.POST.get('telefon', '').strip()
                if not telefon:
                    telefon = request.user.sahip.telefon or ''
                
                # Telefon zorunlu kontrolü
                if not telefon:
                    messages.error(request, 'Telefon numarası zorunludur. Lütfen telefon numaranızı girin.')
                    return redirect('ilan:sahip_ilan_olustur', evcil_hayvan_id=evcil_hayvan_id)
                
                # Hayvan profili açıklamasını al (POST'tan veya EvcilHayvan'dan)
                hayvan_profili_aciklama = request.POST.get('hayvan_profili_aciklama', '').strip()
                if not hayvan_profili_aciklama:
                    hayvan_profili_aciklama = evcil_hayvan.genel_not or f"{evcil_hayvan.ad} için sahiplendirme ilanı"
                
                # HayvanProfili oluştur - SNAPSHOT (evcil_hayvan=None yaparak bağlantıyı hemen kaldır)
                hayvan_profili = HayvanProfili.objects.create(
                    kullanici=request.user,
                    evcil_hayvan=None,  # Bağlantıyı hemen kaldır - snapshot korunur
                    hayvan_adi=evcil_hayvan.ad,  # Snapshot: EvcilHayvan'dan kopyala
                    tur=evcil_hayvan.tur,  # Snapshot
                    irk=evcil_hayvan.irk,  # Snapshot
                    dogum_tarihi=evcil_hayvan.dogum_tarihi,  # Snapshot
                    cinsiyet=cinsiyet,  # Snapshot: format dönüşümü yapıldı
                    # Sağlık bilgileri - POST'tan al (kullanıcı girişi)
                    asi_durumu=asi_durumu,
                    ic_parazit=ic_parazit,
                    dis_parazit=dis_parazit,
                    sehir_disi_gonderim=sehir_disi_gonderim,
                    # Konum bilgileri - POST'tan al (kullanıcı girişi)
                    il=il_obj,
                    ilce=ilce_obj,
                    mahalle=mahalle_obj,
                    mahalle_diger=mahalle_diger,
                    # İletişim bilgileri - POST'tan al (kullanıcı girişi) veya Sahip'ten snapshot
                    telefon=telefon,  # Snapshot: POST'tan veya Sahip'ten
                    # Açıklama - POST'tan al veya EvcilHayvan'dan snapshot
                    aciklama=hayvan_profili_aciklama,
                    profil_fotografi=profil_fotografi  # Fiziksel kopya
                )
                
                # Ek resimleri kaydet (maksimum 3)
                if ek_resimler:
                    for i, resim in enumerate(ek_resimler):
                        try:
                            # Dosya adını güvenli hale getir
                            file_extension = os.path.splitext(resim.name)[1] or '.jpg'
                            safe_filename = f"{hayvan_profili.id}_{i+1}_{uuid.uuid4().hex}{file_extension}"
                            
                            # HayvanResmi oluştur
                            hayvan_resmi = HayvanResmi.objects.create(
                                hayvan_profili=hayvan_profili,
                                sira=i + 1
                            )
                            
                            # Resim kaydet
                            hayvan_resmi.resim.save(safe_filename, ContentFile(resim.read()), save=True)
                        except Exception as e:
                            # Resim kaydedilemezse devam et
                            print(f"Ek resim kaydetme hatası: {e}")
                            try:
                                if 'hayvan_resmi' in locals():
                                    hayvan_resmi.delete()
                            except:
                                pass
                            continue
                
                # İlan oluştur
                baslik = request.POST.get('baslik', f"Sevimli {evcil_hayvan.ad} Sahiplendirme İlanı")
                aciklama = request.POST.get('aciklama', f"{evcil_hayvan.ad} için yeni bir yuva arıyoruz. {evcil_hayvan.tur.ad} cinsi, {evcil_hayvan.irk.ad} ırkı. {evcil_hayvan.get_cinsiyet_display()} cinsiyet. Sevgi dolu bir aile arıyoruz!")
                onemli_mi = request.POST.get('onemli_mi') == 'on'
                
                # Toplam ücret hesapla
                toplam_ucret = ilan_ucreti
                if onemli_mi:
                    toplam_ucret += onemli_ilan_ucreti
                
                # Bakiye kontrolü
                kullanici_bakiye = get_kullanici_kredi_bakiye(request.user)
                if kullanici_bakiye < toplam_ucret:
                    messages.error(request, f"Yetersiz kredi! İlan vermek için {toplam_ucret} kredi gerekli. Mevcut bakiyeniz: {kullanici_bakiye}")
                    return redirect('ilan:kredi_satin_al')
                
                # İlan oluştur
                ilan = Ilan.objects.create(
                    hayvan_profili=hayvan_profili,
                    baslik=baslik,
                    ilan_turu='SAHIPLENDIRME',
                    aciklama=aciklama,
                    onemli_mi=onemli_mi,
                    onaylandi=False  # Admin onayı gerekli
                )
                
                # Kredi hareketi kaydet
                KrediHareketi.objects.create(
                    kullanici=request.user,
                    hareket_turu=KrediHareketi.HAREKET_ILAN_VERME,
                    miktar=-ilan_ucreti,
                    aciklama=f"İlan oluşturma: {ilan.baslik}",
                    ilan=ilan
                )
                
                # Öne çıkarma ücreti
                if onemli_mi:
                    KrediHareketi.objects.create(
                        kullanici=request.user,
                        hareket_turu=KrediHareketi.HAREKET_ONEMLI_ILAN,
                        miktar=-onemli_ilan_ucreti,
                        aciklama=f"Öne çıkarma: {ilan.baslik}",
                        ilan=ilan
                    )
                
                messages.success(request, f'İlan başarıyla oluşturuldu! Admin onayı bekleniyor. {toplam_ucret} kredi harcandı.')
                return redirect('ilan:kullanici_ilanlari')
        except Exception as e:
            import traceback
            print(f"İlan oluşturma hatası: {e}")
            print(traceback.format_exc())
            messages.error(request, f'İlan oluşturulurken bir hata oluştu: {str(e)}')
            return redirect('ilan:sahip_hayvan_secimi')
    
    # GET request - form göster
    # Konum bilgileri için verileri hazırla
    from anahtarlik.dictionaries import Il, Ilce, Mahalle
    iller = Il.objects.all().order_by('ad')
    
    # Sahip'in il ve ilçesine göre ilçe ve mahalle listesi
    ilceler = Ilce.objects.none()
    mahalleler = Mahalle.objects.none()
    
    if request.user.sahip.il:
        ilceler = Ilce.objects.filter(il=request.user.sahip.il).order_by('ad')
        if request.user.sahip.ilce:
            mahalleler = Mahalle.objects.filter(ilce=request.user.sahip.ilce).order_by('ad')
    
    context = {
        'evcil_hayvan': evcil_hayvan,
        'ilan_ucreti': ilan_ucreti,
        'onemli_ilan_ucreti': onemli_ilan_ucreti,
        'kullanici_bakiye': kullanici_bakiye,
        'iller': iller,
        'ilceler': ilceler,
        'mahalleler': mahalleler,
    }
    
    return render(request, 'ilan/sahip_ilan_olustur.html', context)


@login_required
def kullanici_ilanlari(request):
    """Kullanıcının aktif ilanları"""
    
    # Kullanıcının aktif ilanları (kullanıcı kendi ilanlarını görebilir, süresi dolmuş olsa bile)
    ilanlar = Ilan.objects.filter(
        hayvan_profili__kullanici=request.user,
        aktif=True
    ).select_related(
        'hayvan_profili'
    ).prefetch_related(
        'hayvan_profili__resimler'
    ).order_by('-olusturulma_tarihi')
    
    # Sayfalama
    paginator = Paginator(ilanlar, 12)
    page_number = request.GET.get('page')
    ilanlar = paginator.get_page(page_number)
    
    context = {
        'ilanlar': ilanlar,
    }
    
    return render(request, 'ilan/kullanici_ilanlari.html', context)


@login_required
def hayvan_profili_duzenle(request, profil_id):
    """Hayvan profili düzenleme"""
    hayvan_profili = get_object_or_404(
        HayvanProfili,
        id=profil_id,
        kullanici=request.user
    )
    
    if request.method == 'POST':
        form = HayvanProfiliForm(request.POST, request.FILES, instance=hayvan_profili)
        if form.is_valid():
            form.save()
            messages.success(request, 'Hayvan profili başarıyla güncellendi!')
            return redirect('ilan:hayvan_profili_detay', profil_id=hayvan_profili.id)
    else:
        form = HayvanProfiliForm(instance=hayvan_profili)
    
    context = {
        'form': form,
        'hayvan_profili': hayvan_profili,
    }
    
    return render(request, 'ilan/hayvan_profili_duzenle.html', context)


@login_required
def hayvan_profili_sil(request, profil_id):
    """Hayvan profili silme"""
    hayvan_profili = get_object_or_404(
        HayvanProfili,
        id=profil_id,
        kullanici=request.user
    )
    
    if request.method == 'POST':
        hayvan_profili.delete()
        messages.success(request, 'Hayvan profili başarıyla silindi!')
        return redirect('ilan:ilan_listesi')
    
    context = {
        'hayvan_profili': hayvan_profili,
    }
    
    return render(request, 'ilan/hayvan_profili_sil.html', context)


@login_required
def ilan_duzenle(request, ilan_id):
    """İlan düzenleme - Düzenleme sonrası tekrar admin onayı gerekir"""
    ilan = get_object_or_404(
        Ilan,
        id=ilan_id,
        hayvan_profili__kullanici=request.user
    )
    
    if request.method == 'POST':
        form = IlanForm(request.POST, instance=ilan, user=request.user)
        if form.is_valid():
            # Düzenleme yapıldığında tekrar admin onayı gerekir
            ilan = form.save(commit=False)
            ilan.onaylandi = False  # Tekrar admin onayı gerekli
            ilan.aktif = True  # Aktif kalır ama onay bekler
            ilan.save()
            
            messages.warning(
                request, 
                'İlan başarıyla güncellendi! Değişikliklerin yayına alınması için admin onayı gereklidir. Onaylandıktan sonra ilanınız tekrar yayında olacaktır.'
            )
            return redirect('ilan:kullanici_ilanlari')
    else:
        form = IlanForm(instance=ilan, user=request.user)
    
    context = {
        'form': form,
        'ilan': ilan,
    }
    
    return render(request, 'ilan/ilan_duzenle.html', context)


@login_required
def ilan_sil(request, ilan_id):
    """İlan silme - Tüm ilgili verileri siler"""
    ilan = get_object_or_404(
        Ilan,
        id=ilan_id,
        hayvan_profili__kullanici=request.user
    )
    
    if request.method == 'POST':
        # Hayvan profili ve resimlerini al
        hayvan_profili = ilan.hayvan_profili
        hayvan_resimleri = hayvan_profili.resimler.all()
        
        # Fiziksel dosyaları sil
        import os
        from django.conf import settings
        
        # Hayvan profili ana fotoğrafını sil
        if hayvan_profili.profil_fotografi:
            try:
                foto_path = os.path.join(settings.MEDIA_ROOT, str(hayvan_profili.profil_fotografi))
                if os.path.exists(foto_path):
                    os.remove(foto_path)
            except Exception as e:
                print(f"Ana fotoğraf silinirken hata: {e}")
        
        # Hayvan resimlerini sil
        for resim in hayvan_resimleri:
            try:
                if resim.resim:
                    resim_path = os.path.join(settings.MEDIA_ROOT, str(resim.resim))
                    if os.path.exists(resim_path):
                        os.remove(resim_path)
            except Exception as e:
                print(f"Resim silinirken hata: {e}")
        
        # Veritabanından sil
        ilan.delete()  # Bu hayvan_profili'yi de silecek (CASCADE)
        
        messages.success(request, 'İlan ve tüm ilgili veriler başarıyla silindi!')
        return redirect('ilan:kullanici_ilanlari')
    
    context = {
        'ilan': ilan,
    }
    
    return render(request, 'ilan/ilan_sil.html', context)


@login_required
def sahip_ilan_verme_kontrol(request):
    """Sahip kullanıcıları için ilan verme durumu kontrolü"""
    if not hasattr(request.user, 'sahip'):
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('ev')
    
    sahip = request.user.sahip
    
    # Kredi kontrolü
    kullanici_bakiye = get_kullanici_kredi_bakiye(request.user)
    ilan_ucreti = 100
    onemli_ilan_ucreti = 50
    
    # İlan sayısı
    kullanilan_ilan_sayisi = Ilan.objects.filter(
        hayvan_profili__kullanici=sahip.kullanici,
        aktif=True
    ).count()
    
    # Kredi ile kaç ilan verilebilir
    kredi_ile_verilebilir_ilan = kullanici_bakiye // ilan_ucreti
    
    context = {
        'sahip': sahip,
        'kullanici_bakiye': kullanici_bakiye,
        'ilan_ucreti': ilan_ucreti,
        'onemli_ilan_ucreti': onemli_ilan_ucreti,
        'kullanilan_ilan_sayisi': kullanilan_ilan_sayisi,
        'kredi_ile_verilebilir_ilan': kredi_ile_verilebilir_ilan,
    }
    
    return render(request, 'ilan/sahip_ilan_verme_kontrol.html', context)