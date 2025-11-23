# accaunt/views.py
# (role-aware login + mevcut 4 adımlı kayıt akışı)

import logging
from datetime import date
import secrets
import os

from django.conf import settings
from django.contrib import messages
from django.core.files.storage import default_storage
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from anahtarlik.models import Sahip, EvcilHayvan
from etiket.models import Etiket
from accaunt.forms import EtiketForm, MisafirKayitForm, MisafirProfilForm, EvcilHayvanForm
from accaunt.register_forms import EvcilHayvanKayitForm, KullaniciAdresForm, GuestOwnerInfoForm
from accaunt.models import MisafirProfil
# Veteriner ve petshop modellerini de import edelim ki kontrol edebilelim
from veteriner.models import Veteriner
from petshop.models import PetShop

logger = logging.getLogger(__name__)

GUEST_ACTIVATION_ETIKET_KEY = 'guest_activation_etiket_id'
GUEST_ACTIVATION_PET_KEY = 'guest_activation_pet_data'


def _clear_guest_activation_session(request):
    pet_data = request.session.pop(GUEST_ACTIVATION_PET_KEY, None)
    if pet_data:
        temp_path = pet_data.get('resim_temp_path')
        if temp_path and default_storage.exists(temp_path):
            try:
                default_storage.delete(temp_path)
            except Exception as exc:  # pragma: no cover - sadece loglama
                logger.warning("Geçici görsel silinemedi: %s", exc)
    request.session.pop(GUEST_ACTIVATION_ETIKET_KEY, None)

# --- 1. Adım: Etiket kontrolü ---
def step_1_check_tag(request):
    # Eğer session'da etiket_id varsa (künye aktivasyonundan geliyorsa), direkt step 2'ye git
    if request.session.get('etiket_id'):
        try:
            etiket = Etiket.objects.get(id=request.session['etiket_id'])
            if not etiket.aktif:
                return redirect('step_2_pet_info')
            else:
                # Etiket zaten aktif, session'ı temizle
                del request.session['etiket_id']
                messages.error(request, "Bu etiket zaten aktif!")
        except Etiket.DoesNotExist:
            # Etiket bulunamadı, session'ı temizle
            del request.session['etiket_id']
            messages.error(request, "Etiket bulunamadı. Lütfen tekrar deneyin.")
    
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
                    return redirect('step_2_pet_info')
            except Etiket.DoesNotExist:
                messages.error(request, "Bu seri numarası sistemde bulunamadı.")
    else:
        form = EtiketForm()
    return render(request, 'accaunt/register.html', {'form': form, 'step': 1})


# --- 2. Adım: Pet bilgileri ---
def step_2_pet_info(request):
    if 'etiket_id' not in request.session:
        return redirect('step_1_check_tag')

    if request.method == 'POST':
        form = EvcilHayvanKayitForm(request.POST, request.FILES)
        if form.is_valid():
            cd = form.cleaned_data
            evcil_data = {
                'ad': cd.get('ad'),
                'tur_id': cd.get('tur').id if cd.get('tur') else None,
                'irk_id': cd.get('irk').id if cd.get('irk') else None,
                'cinsiyet': cd.get('cinsiyet'),
                'dogum_tarihi': cd.get('dogum_tarihi').isoformat() if cd.get('dogum_tarihi') else None,
            }
            
            # Fotoğraf işleme
            if 'resim' in request.FILES:
                import uuid
                resim = request.FILES['resim']
                
                temp_name = f"temp_{uuid.uuid4()}_{resim.name}"
                temp_path = f"temp_images/{temp_name}"
                
                # Geçici dosyayı kaydet
                saved_path = default_storage.save(temp_path, resim)
                evcil_data['resim_temp_path'] = saved_path
            
            request.session['evcil_data'] = evcil_data
            return redirect('step_3_owner_info')
    else:
        form = EvcilHayvanKayitForm()
    return render(request, 'accaunt/register.html', {'form': form, 'step': 2})


# --- 3. Adım: Kullanıcı/Sahip bilgileri ---
def step_3_owner_info(request):
    if 'etiket_id' not in request.session or 'evcil_data' not in request.session:
        return redirect('step_1_check_tag')

    if request.method == 'POST':
        form = KullaniciAdresForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            telefon = form.cleaned_data['telefon']

            if User.objects.filter(username=username).exists():
                messages.error(request, "Kullanıcı adı zaten kullanılıyor.")
            elif User.objects.filter(email=email).exists():
                messages.error(request, "Bu e-posta zaten kayıtlı.")
            elif Sahip.objects.filter(telefon=telefon).exists():
                messages.error(request, "Telefon numarası zaten kayıtlı.")
            else:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=form.cleaned_data['sifre']
                    )
                    sahip = Sahip.objects.create(
                        kullanici=user,
                        telefon=telefon,
                        ad=form.cleaned_data['ad'],
                        soyad=form.cleaned_data['soyad'],
                        yedek_telefon=form.cleaned_data['yedek_telefon'],
                        adres=form.cleaned_data['adres'],
                        il=form.cleaned_data['il'],
                        ilce=form.cleaned_data['ilce'],
                    )
                    
                    # Danışman veteriner atama
                    danisman_veteriner = sahip.danisman_veteriner_ata()
                    if danisman_veteriner:
                        messages.info(request, f"Danışman veterineriniz: {danisman_veteriner.ad}")
                    evcil_data = request.session['evcil_data']
                    if evcil_data.get('dogum_tarihi'):
                        evcil_data['dogum_tarihi'] = date.fromisoformat(evcil_data['dogum_tarihi'])
                    
                    # ID'leri model objelerine çevir
                    if evcil_data.get('tur_id'):
                        from anahtarlik.dictionaries import Tur
                        evcil_data['tur'] = Tur.objects.get(id=evcil_data['tur_id'])
                        del evcil_data['tur_id']
                    
                    if evcil_data.get('irk_id'):
                        from anahtarlik.dictionaries import Irk
                        evcil_data['irk'] = Irk.objects.get(id=evcil_data['irk_id'])
                        del evcil_data['irk_id']

                    # Fotoğraf temp path'ini çıkar
                    resim_temp_path = evcil_data.pop('resim_temp_path', None)
                    
                    evcil = EvcilHayvan.objects.create(sahip=sahip, **evcil_data)
                    
                    # Fotoğraf işleme
                    if resim_temp_path and default_storage.exists(resim_temp_path):
                        # Geçici dosyayı kalıcı konuma taşı
                        with default_storage.open(resim_temp_path, 'rb') as temp_file:
                            evcil.resim.save(
                                os.path.basename(resim_temp_path),
                                temp_file,
                                save=True
                            )
                        # Geçici dosyayı sil
                        default_storage.delete(resim_temp_path)

                    etiket = Etiket.objects.get(id=request.session['etiket_id'])
                    etiket.evcil_hayvan = evcil
                    etiket.kilitli = False
                    etiket.aktif = True
                    etiket.aktiflestiren = user
                    etiket.aktiflestirme_tarihi = timezone.now()
                    etiket.save()
                    
                    # Etiket aktivasyonunda veteriner/petshop'a kredi ver
                    try:
                        from ilan.models import KrediHareketi
                        
                        if etiket.satici_veteriner and etiket.satici_veteriner.kullanici:
                            KrediHareketi.objects.create(
                                kullanici=etiket.satici_veteriner.kullanici,
                                hareket_turu=KrediHareketi.HAREKET_ETIKET_AKTIVASYON,
                                miktar=150,
                                aciklama=f"Etiket aktivasyonu: {etiket.seri_numarasi}",
                                etiket=etiket
                            )
                        elif etiket.satici_petshop and etiket.satici_petshop.kullanici:
                            KrediHareketi.objects.create(
                                kullanici=etiket.satici_petshop.kullanici,
                                hareket_turu=KrediHareketi.HAREKET_ETIKET_AKTIVASYON,
                                miktar=150,
                                aciklama=f"Etiket aktivasyonu: {etiket.seri_numarasi}",
                                etiket=etiket
                            )
                    except Exception as e:
                        logger.error(f"Etiket aktivasyon kredisi verme hatası: {e}", exc_info=True)

                    request.session.flush()
                    return redirect('step_4_complete')
    else:
        form = KullaniciAdresForm()
    return render(request, 'accaunt/register.html', {'form': form, 'step': 3})




def step_4_complete(request):
    return render(request, 'accaunt/register_success.html')


# --- KÜNYE AKTİVASYON (Login olmayan kullanıcılar için) ---
def künye_aktivasyon_adim1(request):
    """Login olmayan kullanıcılar için künye aktivasyon - Adım 1: Künye kontrolü"""
    
    # Zaten login olmuşsa panel'e yönlendir
    if request.user.is_authenticated:
        return redirect('kullanici_paneli')
    
    if request.method == 'POST':
        # Seçenek kontrolü (yeni kayıt vs mevcut hesap)
        kayit_tipi = request.POST.get('kayit_tipi')
        
        if kayit_tipi == 'yeni_kayit':
            # Yeni kayıt için user_register sürecine yönlendir
            # Etiket ID zaten session'da (künye_etiket_id olarak), onu etiket_id'ye kopyala
            etiket_id = request.session.get('künye_etiket_id')
            if etiket_id:
                try:
                    etiket = Etiket.objects.get(id=etiket_id)
                    if etiket.aktif:
                        messages.error(request, "Bu künye zaten aktif!")
                        del request.session['künye_etiket_id']
                        form = EtiketForm()
                        return render(request, 'accaunt/künye_aktivasyon.html', {
                            'form': form, 
                            'step': 1,
                            'title': 'Künye Aktivasyonu',
                            'show_choice': False
                        })
                    else:
                        # Etiket ID'yi user_register için session'a ekle
                        request.session['etiket_id'] = etiket_id
                        del request.session['künye_etiket_id']  # Künye aktivasyon session'ını temizle
                        return redirect('user_register')
                except Etiket.DoesNotExist:
                    messages.error(request, "Etiket bulunamadı. Lütfen tekrar deneyin.")
                    del request.session['künye_etiket_id']
                    form = EtiketForm()
                    return render(request, 'accaunt/künye_aktivasyon.html', {
                        'form': form, 
                        'step': 1,
                        'title': 'Künye Aktivasyonu',
                        'show_choice': False
                    })
            else:
                messages.error(request, "Etiket bilgisi bulunamadı. Lütfen tekrar deneyin.")
                form = EtiketForm()
                return render(request, 'accaunt/künye_aktivasyon.html', {
                    'form': form, 
                    'step': 1,
                    'title': 'Künye Aktivasyonu',
                    'show_choice': False
                })
        
        elif kayit_tipi == 'mevcut_hesap':
            # Mevcut hesap için giriş sayfasına yönlendir
            # Etiket ID zaten session'da
            etiket_id = request.session.get('künye_etiket_id')
            if etiket_id:
                try:
                    etiket = Etiket.objects.get(id=etiket_id)
                    if etiket.aktif:
                        messages.error(request, "Bu künye zaten aktif!")
                        del request.session['künye_etiket_id']
                        form = EtiketForm()
                        return render(request, 'accaunt/künye_aktivasyon.html', {
                            'form': form, 
                            'step': 1,
                            'title': 'Künye Aktivasyonu',
                            'show_choice': False
                        })
                    else:
                        # Künye bulundu, bilgi mesajı göster ve giriş sayfasına yönlendir
                        request.session['künye_aktivasyon_redirect'] = True
                        messages.info(request, "Giriş yaparak künyenizi mevcut hesabınıza ekleyebilirsiniz.")
                        return redirect('user_login')
                except Etiket.DoesNotExist:
                    messages.error(request, "Etiket bulunamadı. Lütfen tekrar deneyin.")
                    del request.session['künye_etiket_id']
                    form = EtiketForm()
                    return render(request, 'accaunt/künye_aktivasyon.html', {
                        'form': form, 
                        'step': 1,
                        'title': 'Künye Aktivasyonu',
                        'show_choice': False
                    })
            else:
                messages.error(request, "Etiket bilgisi bulunamadı. Lütfen tekrar deneyin.")
                form = EtiketForm()
                return render(request, 'accaunt/künye_aktivasyon.html', {
                    'form': form, 
                    'step': 1,
                    'title': 'Künye Aktivasyonu',
                    'show_choice': False
                })
        
        # Normal form gönderimi (ilk etiket kontrolü)
        form = EtiketForm(request.POST)
        if form.is_valid():
            seri = form.cleaned_data['seri_numarasi']
            try:
                etiket = Etiket.objects.get(seri_numarasi=seri)
                if etiket.aktif:
                    messages.error(request, "Bu künye zaten aktif!")
                else:
                    # Künye geçerli, seçenek göster
                    request.session['künye_etiket_id'] = etiket.id
                    # Form'u seri numarası ile başlat (seçenek ekranında gösterilmek için)
                    form_with_seri = EtiketForm(initial={'seri_numarasi': seri})
                    return render(request, 'accaunt/künye_aktivasyon.html', {
                        'form': form_with_seri,
                        'step': 1,
                        'title': 'Künye Aktivasyonu',
                        'show_choice': True,  # Seçenek göster
                        'etiket_id': etiket.id,
                        'seri_numarasi': seri  # Template'de kullanmak için
                    })
            except Etiket.DoesNotExist:
                messages.error(request, "Bu künye numarası sistemde bulunamadı.")
    else:
        form = EtiketForm()
    
    return render(request, 'accaunt/künye_aktivasyon.html', {
        'form': form, 
        'step': 1,
        'title': 'Künye Aktivasyonu',
        'show_choice': False
    })


def künye_aktivasyon_adim2(request):
    """Künye aktivasyon - Adım 2: Telefon kontrolü ve sahip bulma"""
    
    # Zaten login olmuşsa panel'e yönlendir
    if request.user.is_authenticated:
        return redirect('kullanici_paneli')
    
    # Künye ID yoksa başa dön
    if 'künye_etiket_id' not in request.session:
        return redirect('künye_aktivasyon')
    
    if request.method == 'POST':
        telefon = request.POST.get('telefon', '').strip()
        if telefon:
            # Telefon numarasını temizle
            telefon = ''.join(filter(str.isdigit, telefon))
            if telefon.startswith('0'):
                telefon = telefon[1:]
            
            # Bu telefon numarasına sahip sahip var mı?
            try:
                sahip = Sahip.objects.get(telefon=telefon)
                request.session['künye_sahip_id'] = sahip.id
                return redirect('künye_aktivasyon_adim3')
            except Sahip.DoesNotExist:
                messages.error(request, "Bu telefon numarası ile kayıtlı kullanıcı bulunamadı.")
                messages.warning(request, "Eğer bu telefon numarası zaten kayıtlı ise, lütfen giriş yapıp 'Yeni Evcil Hayvan Ekle' seçeneğini kullanın.")
                messages.info(request, "İlk kez kayıt oluyorsanız lütfen 'İlk Kez Kayıt Ol' seçeneğini kullanın.")
        else:
            messages.error(request, "Telefon numarası gerekli.")
    
    return render(request, 'accaunt/künye_aktivasyon.html', {
        'step': 2,
        'title': 'Telefon Kontrolü'
    })


def künye_aktivasyon_adim3(request):
    """Künye aktivasyon - Adım 3: Hayvan bilgileri"""
    
    # Zaten login olmuşsa panel'e yönlendir
    if request.user.is_authenticated:
        return redirect('kullanici_paneli')
    
    # Gerekli session verileri yoksa başa dön
    if 'künye_etiket_id' not in request.session or 'künye_sahip_id' not in request.session:
        return redirect('künye_aktivasyon')
    
    if request.method == 'POST':
        form = EvcilHayvanForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                # Sahip'i al
                sahip = get_object_or_404(Sahip, id=request.session['künye_sahip_id'])
                
                # Hayvan'ı oluştur
                evcil = form.save(commit=False)
                evcil.sahip = sahip
                evcil.save()
                
                # Etiket'i aktif et
                etiket = Etiket.objects.get(id=request.session['künye_etiket_id'])
                etiket.evcil_hayvan = evcil
                etiket.aktif = True
                etiket.aktiflestiren = sahip.kullanici
                etiket.aktiflestirme_tarihi = timezone.now()
                etiket.qr_kod_url = f"{settings.SITE_URL}{reverse('etiket:qr_landing', kwargs={'tag_id': etiket.etiket_id})}"
                etiket.save()
                
                # Etiket aktivasyonunda veteriner/petshop'a kredi ver
                try:
                    from ilan.models import KrediHareketi
                    
                    if etiket.satici_veteriner and etiket.satici_veteriner.kullanici:
                        KrediHareketi.objects.create(
                            kullanici=etiket.satici_veteriner.kullanici,
                            hareket_turu=KrediHareketi.HAREKET_ETIKET_AKTIVASYON,
                            miktar=150,
                            aciklama=f"Etiket aktivasyonu: {etiket.seri_numarasi}",
                            etiket=etiket
                        )
                    elif etiket.satici_petshop and etiket.satici_petshop.kullanici:
                        KrediHareketi.objects.create(
                            kullanici=etiket.satici_petshop.kullanici,
                            hareket_turu=KrediHareketi.HAREKET_ETIKET_AKTIVASYON,
                            miktar=150,
                            aciklama=f"Etiket aktivasyonu: {etiket.seri_numarasi}",
                            etiket=etiket
                        )
                except Exception as e:
                    logger.error(f"Etiket aktivasyon kredisi verme hatası: {e}", exc_info=True)
                
                # Danışman veteriner atama (künye aktivasyonu sonrası)
                danisman_veteriner = sahip.danisman_veteriner_ata()
                if danisman_veteriner:
                    messages.info(request, f"Danışman veterineriniz: {danisman_veteriner.ad}")
                
                # Session'ı temizle
                del request.session['künye_etiket_id']
                del request.session['künye_sahip_id']
                
                messages.success(request, f'Künye başarıyla aktif edildi! {evcil.ad} adlı hayvanınız profilinize eklendi.')
                messages.info(request, 'Giriş yaparak hayvanınızı görüntüleyebilirsiniz.')
                return redirect('user_login')
    else:
        form = EvcilHayvanForm()
    
    return render(request, 'accaunt/künye_aktivasyon.html', {
        'form': form,
        'step': 3,
        'title': 'Hayvan Bilgileri'
    })


# --- Misafir kullanıcılar için etiket aktivasyonu ---
@login_required
def guest_activate_tag(request):
    user = request.user

    if hasattr(user, 'sahip'):
        messages.info(request, "Zaten sahip profiliniz bulunuyor.")
        return redirect('anahtarlik:kullanici_paneli')

    if not hasattr(user, 'misafir_profili'):
        messages.error(request, "Bu işlem yalnızca misafir kullanıcılar içindir.")
        return redirect('anahtarlik:kullanici_paneli')

    if request.method == 'GET':
        _clear_guest_activation_session(request)

    form = EtiketForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        seri = form.cleaned_data['seri_numarasi']
        try:
            etiket = Etiket.objects.get(seri_numarasi=seri)
            if etiket.aktif:
                messages.error(request, "Bu etiket zaten aktif!")
            else:
                request.session[GUEST_ACTIVATION_ETIKET_KEY] = etiket.id
                request.session.modified = True
                messages.success(request, "Etiket doğrulandı. Şimdi evcil hayvan bilgilerini girin.")
                return redirect('guest_activate_pet')
        except Etiket.DoesNotExist:
            messages.error(request, "Bu seri numarası sistemde bulunamadı.")

    return render(request, 'accaunt/guest_activate_tag.html', {
        'form': form,
    })


@login_required
def guest_activate_pet(request):
    user = request.user
    if hasattr(user, 'sahip'):
        return redirect('anahtarlik:kullanici_paneli')
    if not hasattr(user, 'misafir_profili'):
        return redirect('anahtarlik:ev')

    etiket_id = request.session.get(GUEST_ACTIVATION_ETIKET_KEY)
    if not etiket_id:
        messages.warning(request, "Önce etiket seri numarasını doğrulayın.")
        return redirect('guest_activate_tag')

    pet_data = request.session.get(GUEST_ACTIVATION_PET_KEY, {})
    initial = {}
    if pet_data:
        initial = {
            'ad': pet_data.get('ad'),
            'tur': pet_data.get('tur_id'),
            'irk': pet_data.get('irk_id'),
            'cinsiyet': pet_data.get('cinsiyet'),
        }
        if pet_data.get('dogum_tarihi'):
            try:
                initial['dogum_tarihi'] = date.fromisoformat(pet_data['dogum_tarihi'])
            except ValueError:
                pass

    form = EvcilHayvanKayitForm(request.POST or None, request.FILES or None, initial=initial)

    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data
        evcil_data = {
            'ad': cd.get('ad'),
            'tur_id': cd.get('tur').id if cd.get('tur') else None,
            'irk_id': cd.get('irk').id if cd.get('irk') else None,
            'cinsiyet': cd.get('cinsiyet'),
            'dogum_tarihi': cd.get('dogum_tarihi').isoformat() if cd.get('dogum_tarihi') else None,
        }

        existing = request.session.get(GUEST_ACTIVATION_PET_KEY)
        if existing:
            temp_path = existing.get('resim_temp_path')
            if temp_path and default_storage.exists(temp_path):
                default_storage.delete(temp_path)

        if 'resim' in request.FILES:
            import uuid
            resim = request.FILES['resim']
            temp_name = f"temp_{uuid.uuid4()}_{resim.name}"
            temp_path = f"temp_images/{temp_name}"
            saved_path = default_storage.save(temp_path, resim)
            evcil_data['resim_temp_path'] = saved_path

        request.session[GUEST_ACTIVATION_PET_KEY] = evcil_data
        request.session.modified = True
        messages.success(request, "Evcil hayvan bilgileri kaydedildi. Şimdi adres bilgilerini tamamlayın.")
        return redirect('guest_activate_owner')

    return render(request, 'accaunt/guest_activate_pet.html', {
        'form': form,
    })


@login_required
def guest_activate_owner(request):
    user = request.user
    if hasattr(user, 'sahip'):
        return redirect('anahtarlik:kullanici_paneli')
    if not hasattr(user, 'misafir_profili'):
        return redirect('anahtarlik:ev')

    etiket_id = request.session.get(GUEST_ACTIVATION_ETIKET_KEY)
    pet_data = request.session.get(GUEST_ACTIVATION_PET_KEY)
    if not etiket_id or not pet_data:
        messages.warning(request, "Etiket ve hayvan bilgilerini tamamlamadan ilerleyemezsiniz.")
        return redirect('guest_activate_tag')

    misafir = user.misafir_profili
    ad, soyad = misafir.ad_soyad, ''
    if misafir.ad_soyad:
        pieces = misafir.ad_soyad.split()
        if pieces:
            ad = pieces[0]
            soyad = ' '.join(pieces[1:]) if len(pieces) > 1 else ''

    initial = {
        'ad': user.first_name or ad,
        'soyad': user.last_name or soyad,
        'telefon': misafir.telefon,
    }

    form = GuestOwnerInfoForm(request.POST or None, user=user, initial=initial)

    if request.method == 'POST' and form.is_valid():
        try:
            etiket = Etiket.objects.get(id=etiket_id)
        except Etiket.DoesNotExist:
            messages.error(request, "Etiket bulunamadı. Lütfen süreci yeniden başlatın.")
            _clear_guest_activation_session(request)
            return redirect('guest_activate_tag')

        if etiket.aktif:
            messages.error(request, "Bu etiket zaten aktif durumda.")
            _clear_guest_activation_session(request)
            return redirect('guest_activate_tag')

        cd = form.cleaned_data
        telefon = cd['telefon']
        yedek_telefon = cd.get('yedek_telefon') or ''
        il = cd['il']
        ilce = cd['ilce']
        mahalle = cd.get('mahalle')
        mahalle_diger = cd.get('mahalle_diger', '')
        adres = cd['adres']

        with transaction.atomic():
            user.first_name = cd['ad']
            user.last_name = cd['soyad']
            user.save(update_fields=['first_name', 'last_name'])

            sahip, created = Sahip.objects.get_or_create(
                kullanici=user,
                defaults={
                    'telefon': telefon,
                    'yedek_telefon': yedek_telefon,
                    'ad': cd['ad'],
                    'soyad': cd['soyad'],
                    'adres': adres,
                    'il': il,
                    'ilce': ilce,
                    'mahalle': mahalle,
                    'mahalle_diger': mahalle_diger,
                }
            )

            if not created:
                sahip.telefon = telefon
                sahip.yedek_telefon = yedek_telefon
                sahip.ad = cd['ad']
                sahip.soyad = cd['soyad']
                sahip.adres = adres
                sahip.il = il
                sahip.ilce = ilce
                sahip.mahalle = mahalle
                sahip.mahalle_diger = mahalle_diger
                sahip.save()

            evcil_kwargs = {
                'ad': pet_data.get('ad'),
                'cinsiyet': pet_data.get('cinsiyet'),
                'sahip': sahip,
            }

            if pet_data.get('dogum_tarihi'):
                try:
                    evcil_kwargs['dogum_tarihi'] = date.fromisoformat(pet_data['dogum_tarihi'])
                except ValueError:
                    pass

            if pet_data.get('tur_id'):
                from anahtarlik.dictionaries import Tur
                evcil_kwargs['tur'] = Tur.objects.get(id=pet_data['tur_id'])
            if pet_data.get('irk_id'):
                from anahtarlik.dictionaries import Irk
                evcil_kwargs['irk'] = Irk.objects.get(id=pet_data['irk_id'])

            evcil = EvcilHayvan.objects.create(**evcil_kwargs)

            temp_path = pet_data.get('resim_temp_path')
            if temp_path and default_storage.exists(temp_path):
                with default_storage.open(temp_path, 'rb') as temp_file:
                    evcil.resim.save(os.path.basename(temp_path), temp_file, save=True)
                default_storage.delete(temp_path)

            etiket.evcil_hayvan = evcil
            etiket.aktif = True
            etiket.kilitli = False
            etiket.aktiflestiren = user
            etiket.aktiflestirme_tarihi = timezone.now()
            etiket.save()

            try:
                sahip.danisman_veteriner_ata()
            except Exception as exc:
                logger.warning("Danışman veteriner ataması başarısız: %s", exc)

            MisafirProfil.objects.filter(kullanici=user).delete()

        _clear_guest_activation_session(request)
        messages.success(request, "Etiket aktivasyonu tamamlandı. Sahip paneline yönlendiriliyorsunuz.")
        return redirect('anahtarlik:kullanici_paneli')

    return render(request, 'accaunt/guest_activate_owner.html', {
        'form': form,
    })


# --- AJAX: Seçilen il için ilçeleri getir ---
from django.http import JsonResponse
from anahtarlik.dictionaries import Ilce, Irk


def districts_for_city(request):
    """İlçe listesi AJAX endpoint - DEPRECATED: districts_for_province kullanın"""
    from core.views import districts_for_province
    return districts_for_province(request)


def breeds_for_species(request):
    tur_id = request.GET.get('tur_id')
    if tur_id:
        breeds = list(Irk.objects.filter(tur_id=tur_id).order_by('ad').values('id', 'ad'))
        return JsonResponse({'breeds': breeds})
    return JsonResponse({'breeds': []})


# --- Giriş (ROL'E GÖRE YÖNLENDİRME) ---
def user_login(request):
    """
    Girişten sonra kullanıcı rolüne göre yönlendirir.
    TEK PROFİL SİSTEMİ: Bir kullanıcı sadece bir tür profil olabilir.
    """
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Session sepetini DB sepetine aktar
            from shop.cart_utils import merge_guest_cart_to_user
            merge_guest_cart_to_user(request, user)

            # Künye aktivasyon sürecinden geliyorsa kontrol et
            etiket_id = request.session.get('künye_etiket_id')
            if etiket_id:
                try:
                    etiket = Etiket.objects.get(id=etiket_id)
                    if not etiket.aktif:
                        # Etiket geçerli ve aktif değil, add_pet step 2'ye yönlendir
                        request.session['etiket_id'] = etiket_id
                        request.session['add_pet_step'] = 2
                        del request.session['künye_etiket_id']
                        if request.session.get('künye_aktivasyon_redirect'):
                            del request.session['künye_aktivasyon_redirect']
                        
                        # Sadece Sahip kullanıcıları için add_pet'e yönlendir
                        Sahip.objects.get_or_create(kullanici=user)
                        return redirect('anahtarlik:add_pet')
                    else:
                        # Etiket zaten aktif
                        del request.session['künye_etiket_id']
                        if request.session.get('künye_aktivasyon_redirect'):
                            del request.session['künye_aktivasyon_redirect']
                        messages.error(request, "Bu künye zaten aktif!")
                except Etiket.DoesNotExist:
                    # Etiket bulunamadı
                    del request.session['künye_etiket_id']
                    if request.session.get('künye_aktivasyon_redirect'):
                        del request.session['künye_aktivasyon_redirect']

            # 0) Sahip mi?
            if hasattr(user, "sahip"):
                return redirect('anahtarlik:kullanici_paneli')

            # 1) Misafir mi?
            if hasattr(user, "misafir_profili"):
                return redirect('guest_dashboard')

            # 2) Veteriner mi? (Öncelik veteriner)
            if hasattr(user, "veteriner_profili"):
                v = user.veteriner_profili
                if not v.il or not v.adres_detay:
                    return redirect('veteriner:veteriner_profil_tamamla')
                # İlk giriş şifre değiştirme kontrolü
                if not v.ilk_giris_sifre_degistirildi:
                    messages.warning(
                        request, 
                        'Güvenliğiniz için lütfen şifrenizi değiştirin. Admin tarafından oluşturulan şifreler güvenlik nedeniyle değiştirilmelidir.'
                    )
                    return redirect('veteriner:hesap_ayarlari')
                return redirect('veteriner:veteriner_paneli')

            # 3) Petshop mu? (Veteriner değilse petshop)
            if hasattr(user, "petshop_profili"):
                s = user.petshop_profili
                if not s.il or not s.adres_detay:
                    return redirect('petshop:petshop_profil_tamamla')
                # İlk giriş şifre değiştirme kontrolü
                if not s.ilk_giris_sifre_degistirildi:
                    messages.warning(
                        request, 
                        'Güvenliğiniz için lütfen şifrenizi değiştirin. Admin tarafından oluşturulan şifreler güvenlik nedeniyle değiştirilmelidir.'
                    )
                    return redirect('petshop:hesap_ayarlari')
                return redirect('petshop:petshop_paneli')

            # 4) Son kullanıcı (Sahip) - Varsayılan
            Sahip.objects.get_or_create(kullanici=user)
            return redirect('anahtarlik:kullanici_paneli')

        messages.error(request, 'Geçersiz kullanıcı adı veya şifre.')
        return render(request, 'accaunt/login.html')

    return render(request, 'accaunt/login.html')


# --- PROFİL OLUŞTURMA FONKSİYONLARI ---
@login_required
def veteriner_profil_olustur(request):
    """Veteriner profili oluşturma"""
    # Mevcut profil kontrolü
    if hasattr(request.user, 'veteriner_profili'):
        messages.info(request, 'Zaten veteriner profiliniz var.')
        return redirect('veteriner:veteriner_paneli')
    
    if hasattr(request.user, 'petshop_profili'):
        messages.error(request, 'PetShop profiliniz var. Bir kullanıcı sadece bir tür profil olabilir.')
        return redirect('petshop:petshop_paneli')
    
    if request.method == 'POST':
        from veteriner.models import Veteriner
        from veteriner.forms import VeterinerProfilForm
        
        form = VeterinerProfilForm(request.POST)
        if form.is_valid():
            veteriner = form.save(commit=False)
            veteriner.kullanici = request.user
            veteriner.aktif = True
            veteriner.save()
            
            messages.success(request, 'Veteriner profiliniz başarıyla oluşturuldu.')
            return redirect('veteriner:veteriner_paneli')
    else:
        from veteriner.forms import VeterinerProfilForm
        form = VeterinerProfilForm()
    
    return render(request, 'accaunt/veteriner_profil_olustur.html', {'form': form})


@login_required
def petshop_profil_olustur(request):
    """PetShop profili oluşturma"""
    # Mevcut profil kontrolü
    if hasattr(request.user, 'petshop_profili'):
        messages.info(request, 'Zaten PetShop profiliniz var.')
        return redirect('petshop:petshop_paneli')
    
    if hasattr(request.user, 'veteriner_profili'):
        messages.error(request, 'Veteriner profiliniz var. Bir kullanıcı sadece bir tür profil olabilir.')
        return redirect('veteriner:veteriner_paneli')
    
    if request.method == 'POST':
        from petshop.models import PetShop
        from petshop.forms import PetShopProfilForm
        
        form = PetShopProfilForm(request.POST)
        if form.is_valid():
            petshop = form.save(commit=False)
            petshop.kullanici = request.user
            petshop.aktif = True
            petshop.save()
            
            messages.success(request, 'PetShop profiliniz başarıyla oluşturuldu.')
            return redirect('petshop:petshop_paneli')
    else:
        from petshop.forms import PetShopProfilForm
        form = PetShopProfilForm()
    
    return render(request, 'accaunt/petshop_profil_olustur.html', {'form': form})


def user_logout(request):
    logout(request)
    messages.success(request, 'Başarıyla çıkış yaptınız.')
    return redirect('anahtarlik:ev')

def _ensure_guest_code(request):
    code = request.session.get('guest_verification_code')
    if not code:
        code = ''.join(secrets.choice('0123456789') for _ in range(4))
        request.session['guest_verification_code'] = code
    return code


def _clear_guest_code(request):
    request.session.pop('guest_verification_code', None)


def _split_full_name(full_name):
    parts = [p for p in full_name.split() if p]
    if not parts:
        return '', ''
    first = parts[0]
    last = ' '.join(parts[1:]) if len(parts) > 1 else ''
    return first, last


def guest_register(request):
    if request.method == 'GET' and request.GET.get('refresh') == '1':
        _clear_guest_code(request)
    code = _ensure_guest_code(request)
    if request.method == 'POST':
        form = MisafirKayitForm(request.POST, verification_code=code)
        if form.is_valid():
            ad_soyad = form.cleaned_data['ad_soyad'].strip()
            email = form.cleaned_data['email']
            username = form.cleaned_data['username']
            telefon = form.cleaned_data['telefon']
            sifre = form.cleaned_data['sifre']
            first_name, last_name = _split_full_name(ad_soyad)
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=sifre,
                        first_name=first_name,
                        last_name=last_name,
                    )
                    MisafirProfil.objects.create(
                        kullanici=user,
                        ad_soyad=ad_soyad,
                        telefon=telefon,
                        uyelik_sozlesmesi_onay=form.cleaned_data['uyelik_sozlesmesi'],
                    )
            except IntegrityError:
                form.add_error(None, 'Kayit olusturulurken bir sorun olustu. Lutfen tekrar deneyin.')
            else:
                _clear_guest_code(request)
                login(request, user)
                
                # Session sepetini DB sepetine aktar
                from shop.cart_utils import merge_guest_cart_to_user
                merge_guest_cart_to_user(request, user)
                
                messages.success(request, 'Kaydınız oluşturuldu, şimdi ilan vermeye başlayabilirsiniz.')
                return redirect('guest_dashboard')
    else:
        form = MisafirKayitForm(verification_code=code)
    return render(request, 'accaunt/guest_register.html', {'form': form, 'verification_code': code})


@login_required
def guest_dashboard(request):
    """Misafir profil görüntüleme sayfası"""
    from ilan.models import HayvanProfili, KrediHareketi
    
    if hasattr(request.user, 'sahip'):
        return redirect('anahtarlik:kullanici_paneli')

    profil = getattr(request.user, 'misafir_profili', None)
    if profil is None:
        return redirect('kullanici_paneli')
    
    # İstatistikler
    ilan_sayisi = HayvanProfili.objects.filter(kullanici=request.user).count()
    aktif_ilan_sayisi = HayvanProfili.objects.filter(kullanici=request.user, aktif=True).count()
    
    # Kredi bilgileri
    kredi_bakiye = 0
    if hasattr(request.user, 'sahip'):
        from ilan.models import kredi_bakiye as get_kredi_bakiye
        kredi_bakiye = get_kredi_bakiye(request.user.sahip)
    
    # Son kredi hareketleri (3 adet)
    son_kredi_hareketleri = []
    if hasattr(request.user, 'sahip'):
        son_kredi_hareketleri = KrediHareketi.objects.filter(
            sahip=request.user.sahip
        ).order_by('-tarih')[:3]
    
    # Son ilanlar (3 adet)
    son_ilanlar = HayvanProfili.objects.filter(
        kullanici=request.user
    ).order_by('-olusturulma_tarihi')[:3]
    
    context = {
        'profil': profil,
        'ilan_sayisi': ilan_sayisi,
        'aktif_ilan_sayisi': aktif_ilan_sayisi,
        'kredi_bakiye': kredi_bakiye,
        'son_kredi_hareketleri': son_kredi_hareketleri,
        'son_ilanlar': son_ilanlar,
    }
    
    return render(request, 'accaunt/guest_dashboard.html', context)


@login_required
def misafir_profil_duzenle(request):
    """Misafir profil güncelleme"""
    profil = getattr(request.user, 'misafir_profili', None)
    if profil is None:
        messages.error(request, "Misafir profiliniz bulunamadı.")
        return redirect('anahtarlik:ev')
    
    if request.method == 'POST':
        form = MisafirProfilForm(request.POST, instance=profil)
        if form.is_valid():
            form.save()
            
            # User modelinin first_name ve last_name bilgilerini de güncelle
            ad_soyad = form.cleaned_data.get('ad_soyad', '').strip()
            if ad_soyad:
                parts = ad_soyad.split(maxsplit=1)
                request.user.first_name = parts[0] if parts else ''
                request.user.last_name = parts[1] if len(parts) > 1 else ''
                request.user.save()
            
            messages.success(request, "Profiliniz başarıyla güncellendi!")
            return redirect('misafir_profil_duzenle')
        else:
            messages.error(request, "Lütfen form hatalarını düzeltin.")
    else:
        form = MisafirProfilForm(instance=profil)
    
    return render(request, 'accaunt/misafir_profil_duzenle.html', {
        'form': form,
        'profil': profil,
    })





