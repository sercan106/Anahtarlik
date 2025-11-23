import os
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from anahtarlik.models import (
    EvcilHayvan, Alerji, SaglikKaydi,
    IlacKaydi, AmeliyatKaydi, BeslenmeKaydi
)
from .forms import (
    AlerjiForm, PetEditForm, NotGuncellemeForm,
    SahipForm, SaglikForm, IlacForm, AmeliyatForm, BeslenmeForm
)

logger = logging.getLogger(__name__)

@login_required
def panel(request):
    # Kullanıcının evcil hayvanlarını getir
    pets = EvcilHayvan.objects.filter(sahip__kullanici=request.user)
    return render(request, 'petpanel/panel.html', {'pets': pets})

### --- ALERJİ --- ###
@login_required
def alerji_ekle(request, pet_id):
    pet = get_object_or_404(EvcilHayvan, id=pet_id, sahip__kullanici=request.user)
    form = AlerjiForm(request.POST or None)
    if form.is_valid():
        alerji = form.save(commit=False)
        alerji.evcil_hayvan = pet
        alerji.save()
        return redirect('anahtarlik:pet_detail', pet_id=pet.id)
    return render(request, 'petpanel/alerji_form.html', {'form': form, 'pet': pet, 'is_edit': False})

@login_required
def alerji_duzenle(request, record_id):
    alerji = get_object_or_404(Alerji, id=record_id, evcil_hayvan__sahip__kullanici=request.user)
    form = AlerjiForm(request.POST or None, instance=alerji)
    if form.is_valid():
        form.save()
        return redirect('anahtarlik:pet_detail', pet_id=alerji.evcil_hayvan.id)
    return render(request, 'petpanel/alerji_form.html', {'form': form, 'pet': alerji.evcil_hayvan, 'is_edit': True})

@login_required
def alerji_sil(request, record_id):
    alerji = get_object_or_404(Alerji, id=record_id, evcil_hayvan__sahip__kullanici=request.user)
    pet_id = alerji.evcil_hayvan.id
    alerji.delete()
    return redirect('anahtarlik:pet_detail', pet_id=pet_id)

### --- SAĞLIK --- ###
@login_required
def saglik_ekle(request, pet_id):
    pet = get_object_or_404(EvcilHayvan, id=pet_id, sahip__kullanici=request.user)
    form = SaglikForm(request.POST or None)
    if form.is_valid():
        kayit = form.save(commit=False)
        kayit.evcil_hayvan = pet
        kayit.save()
        return redirect('anahtarlik:pet_detail', pet_id=pet.id)
    return render(request, 'petpanel/saglik_form.html', {'form': form, 'pet': pet, 'is_edit': False})

@login_required
def saglik_duzenle(request, record_id):
    kayit = get_object_or_404(SaglikKaydi, id=record_id, evcil_hayvan__sahip__kullanici=request.user)
    form = SaglikForm(request.POST or None, instance=kayit)
    if form.is_valid():
        form.save()
        return redirect('anahtarlik:pet_detail', pet_id=kayit.evcil_hayvan.id)
    return render(request, 'petpanel/saglik_form.html', {'form': form, 'pet': kayit.evcil_hayvan, 'is_edit': True})

@login_required
def saglik_sil(request, record_id):
    kayit = get_object_or_404(SaglikKaydi, id=record_id, evcil_hayvan__sahip__kullanici=request.user)
    pet_id = kayit.evcil_hayvan.id
    kayit.delete()
    return redirect('anahtarlik:pet_detail', pet_id=pet_id)

### --- İLAÇ --- ###
@login_required
def ilac_ekle(request, pet_id):
    pet = get_object_or_404(EvcilHayvan, id=pet_id, sahip__kullanici=request.user)
    form = IlacForm(request.POST or None)
    if form.is_valid():
        kayit = form.save(commit=False)
        kayit.evcil_hayvan = pet
        kayit.save()
        return redirect('anahtarlik:pet_detail', pet_id=pet.id)
    return render(request, 'petpanel/ilac_form.html', {'form': form, 'pet': pet, 'is_edit': False})

@login_required
def ilac_duzenle(request, record_id):
    kayit = get_object_or_404(IlacKaydi, id=record_id, evcil_hayvan__sahip__kullanici=request.user)
    form = IlacForm(request.POST or None, instance=kayit)
    if form.is_valid():
        form.save()
        return redirect('anahtarlik:pet_detail', pet_id=kayit.evcil_hayvan.id)
    return render(request, 'petpanel/ilac_form.html', {'form': form, 'pet': kayit.evcil_hayvan, 'is_edit': True})

@login_required
def ilac_sil(request, record_id):
    kayit = get_object_or_404(IlacKaydi, id=record_id, evcil_hayvan__sahip__kullanici=request.user)
    pet_id = kayit.evcil_hayvan.id
    kayit.delete()
    return redirect('anahtarlik:pet_detail', pet_id=pet_id)

### --- AMELİYAT --- ###
@login_required
def ameliyat_ekle(request, pet_id):
    pet = get_object_or_404(EvcilHayvan, id=pet_id, sahip__kullanici=request.user)
    form = AmeliyatForm(request.POST or None)
    if form.is_valid():
        kayit = form.save(commit=False)
        kayit.evcil_hayvan = pet
        kayit.save()
        return redirect('anahtarlik:pet_detail', pet_id=pet.id)
    return render(request, 'petpanel/ameliyat_form.html', {'form': form, 'pet': pet, 'is_edit': False})

@login_required
def ameliyat_duzenle(request, record_id):
    kayit = get_object_or_404(AmeliyatKaydi, id=record_id, evcil_hayvan__sahip__kullanici=request.user)
    form = AmeliyatForm(request.POST or None, instance=kayit)
    if form.is_valid():
        form.save()
        return redirect('anahtarlik:pet_detail', pet_id=kayit.evcil_hayvan.id)
    return render(request, 'petpanel/ameliyat_form.html', {'form': form, 'pet': kayit.evcil_hayvan, 'is_edit': True})

@login_required
def ameliyat_sil(request, record_id):
    kayit = get_object_or_404(AmeliyatKaydi, id=record_id, evcil_hayvan__sahip__kullanici=request.user)
    pet_id = kayit.evcil_hayvan.id
    kayit.delete()
    return redirect('anahtarlik:pet_detail', pet_id=pet_id)

### --- BESLENME --- ###
@login_required
def beslenme_ekle(request, pet_id):
    pet = get_object_or_404(EvcilHayvan, id=pet_id, sahip__kullanici=request.user)
    form = BeslenmeForm(request.POST or None)
    if form.is_valid():
        kayit = form.save(commit=False)
        kayit.evcil_hayvan = pet
        kayit.save()
        return redirect('anahtarlik:pet_detail', pet_id=pet.id)
    return render(request, 'petpanel/beslenme_form.html', {'form': form, 'pet': pet, 'is_edit': False})

@login_required
def beslenme_duzenle(request, record_id):
    kayit = get_object_or_404(BeslenmeKaydi, id=record_id, evcil_hayvan__sahip__kullanici=request.user)
    form = BeslenmeForm(request.POST or None, instance=kayit)
    if form.is_valid():
        form.save()
        return redirect('anahtarlik:pet_detail', pet_id=kayit.evcil_hayvan.id)
    return render(request, 'petpanel/beslenme_form.html', {'form': form, 'pet': kayit.evcil_hayvan, 'is_edit': True})

@login_required
def beslenme_sil(request, record_id):
    kayit = get_object_or_404(BeslenmeKaydi, id=record_id, evcil_hayvan__sahip__kullanici=request.user)
    pet_id = kayit.evcil_hayvan.id
    kayit.delete()
    return redirect('anahtarlik:pet_detail', pet_id=pet_id)

### --- DİĞER --- ###
@login_required
def sahip_bilgilerini_duzenle(request, pet_id):
    pet = get_object_or_404(EvcilHayvan, id=pet_id, sahip__kullanici=request.user)
    sahip = pet.sahip
    form = SahipForm(request.POST or None, instance=sahip)
    if form.is_valid():
        form.save()
        return redirect('anahtarlik:pet_detail', pet_id=pet.id)
    return render(request, 'petpanel/sahip_duzenle.html', {'form': form, 'pet': pet})

@login_required
def notlari_duzenle(request, pet_id):
    pet = get_object_or_404(EvcilHayvan, id=pet_id, sahip__kullanici=request.user)
    form = NotGuncellemeForm(request.POST or None, instance=pet)
    if form.is_valid():
        form.save()
        return redirect('anahtarlik:pet_detail', pet_id=pet.id)
    return render(request, 'petpanel/notlari_duzenle.html', {'form': form, 'pet': pet})

@login_required
def edit_pet(request, pet_id):
    pet = get_object_or_404(EvcilHayvan, id=pet_id, sahip__kullanici=request.user)
    
    # Eski fotoğrafı sakla (silme için)
    eski_foto = pet.resim if pet.resim else None
    
    form = PetEditForm(request.POST or None, request.FILES or None, instance=pet)
    if form.is_valid():
        # Yeni fotoğraf yüklenmiş mi kontrol et
        yeni_foto = form.cleaned_data.get('resim')
        
        # Eski fotoğrafı sil (yeni fotoğraf yüklenmişse ve eski fotoğraf varsa)
        if yeni_foto and eski_foto:
            try:
                # Dosya sisteminden sil
                if os.path.isfile(eski_foto.path):
                    os.remove(eski_foto.path)
                    logger.info(f"✅ Eski fotoğraf silindi: {eski_foto.path}")
            except Exception as e:
                logger.error(f"❌ Eski fotoğraf silinirken hata: {e}")
                # Hata olsa bile devam et (kritik değil)
        
        form.save()
        messages.success(request, 'Evcil hayvan bilgileri güncellendi!')
        return redirect('anahtarlik:pet_detail', pet_id=pet.id)
    return render(request, 'petpanel/edit_pet.html', {'form': form, 'pet': pet})


