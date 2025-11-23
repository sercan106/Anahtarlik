# anahtarlik/forms.py

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import EvcilHayvan, Sahip, HeroSlide, HizmetKarti, AnaSayfaAyar
from django.utils import timezone
from .dictionaries import Tur, Irk, Il, Ilce

class EtiketForm(forms.Form):
    seri_numarasi = forms.CharField(
        label="Etiket Seri Numarası",
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

class EvcilHayvanForm(forms.ModelForm):
    cinsiyet = forms.ChoiceField(
        choices=EvcilHayvan.CINSIYET_SECENEKLERI,
        label="Cinsiyet",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    dogum_tarihi = forms.DateField(
        label="Doğum Tarihi",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=False
    )
    resim = forms.ImageField(
        label="Hayvan Fotoğrafı",
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tür ve ırk alanlarını iyileştir
        self.fields['tur'].queryset = Tur.objects.all().order_by('ad')
        self.fields['tur'].empty_label = "Tür Seçiniz"
        self.fields['irk'].queryset = Irk.objects.none()
        self.fields['irk'].empty_label = "Önce tür seçiniz"
        
        # Dinamik ırk yükleme için data attribute
        self.fields['tur'].widget.attrs.setdefault('data-breed-target', 'id_irk')
        
        # POST verisi varsa ve tür seçilmişse ırk'ları yükle
        data = kwargs.get('data') or self.data
        tur_id = None
        if data:
            tur_id = data.get('tur') or data.get('tur_id')
        if not tur_id and self.instance and self.instance.pk and self.instance.tur_id:
            tur_id = self.instance.tur_id
        try:
            if tur_id:
                self.fields['irk'].queryset = Irk.objects.filter(tur_id=tur_id).order_by('ad')
                self.fields['irk'].empty_label = "Irk Seçiniz"
        except (ValueError, TypeError):
            pass

    class Meta:
        model = EvcilHayvan
        fields = [
            'ad', 'tur', 'irk', 'cinsiyet', 'dogum_tarihi',
            'saglik_notu', 'beslenme_notu', 'genel_not', 'davranis_notu', 'resim'
        ]
        widgets = {
            'ad': forms.TextInput(attrs={'class': 'form-control'}),
            'saglik_notu': forms.Textarea(attrs={'class': 'form-control form-textarea'}),
            'beslenme_notu': forms.Textarea(attrs={'class': 'form-control form-textarea'}),
            'genel_not': forms.Textarea(attrs={'class': 'form-control form-textarea'}),
            'davranis_notu': forms.Textarea(attrs={'class': 'form-control form-textarea'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        tur = cleaned_data.get('tur')
        irk = cleaned_data.get('irk')
        
        # Tür seçilmişse ırk'ları yükle ve validation yap
        if tur and irk:
            # Irk'ın seçilen türe ait olduğunu kontrol et
            if not Irk.objects.filter(id=irk.id, tur=tur).exists():
                raise forms.ValidationError("Seçilen ırk, seçilen türe ait değil.")
        
        return cleaned_data

    def clean_dogum_tarihi(self):
        from datetime import date
        dogum_tarihi = self.cleaned_data.get('dogum_tarihi')
        if dogum_tarihi:
            # Bugünün tarihini al (timezone-aware olmadan)
            bugun = date.today()
            if dogum_tarihi > bugun:
                raise forms.ValidationError("Doğum tarihi gelecekte olamaz.")
        return dogum_tarihi


class SahipProfilForm(forms.ModelForm):
    """Sahip profil güncelleme formu"""
    il = forms.ModelChoiceField(
        label="İl",
        queryset=Il.objects.all().order_by("ad"),
        required=True,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    ilce = forms.ModelChoiceField(
        label="İlçe",
        queryset=Ilce.objects.none(),
        required=True,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    
    class Meta:
        model = Sahip
        fields = ['ad', 'soyad', 'telefon', 'yedek_telefon', 'adres', 'acil_durum_kontagi']
        widgets = {
            'ad': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'soyad': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'telefon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '05XX XXX XX XX'}),
            'yedek_telefon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '05XX XXX XX XX'}),
            'adres': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'acil_durum_kontagi': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '05XX XXX XX XX'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # İlçe queryset'ini başlangıçta boş yap
        self.fields['ilce'].queryset = Ilce.objects.none()
        
        # Mevcut sahip instance varsa il'e göre ilçeleri filtrele
        if self.instance and self.instance.pk and self.instance.il:
            self.fields['ilce'].queryset = Ilce.objects.filter(il=self.instance.il).order_by("ad")
        
        # POST data varsa il'e göre ilçeleri filtrele
        if 'il' in self.data:
            try:
                il_id = int(self.data.get('il'))
                self.fields['ilce'].queryset = Ilce.objects.filter(il_id=il_id).order_by("ad")
            except (ValueError, TypeError):
                pass
    
    def clean(self):
        cleaned_data = super().clean()
        il = cleaned_data.get('il')
        ilce = cleaned_data.get('ilce')
        
        # İl-İlçe uyumluluğunu kontrol et
        if il and ilce and ilce.il != il:
            raise forms.ValidationError("Seçilen ilçe, seçilen ile ait değil.")
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # İl ve İlçe field'larını manuel olarak kaydet
        if self.cleaned_data.get('il'):
            instance.il = self.cleaned_data['il']
        if self.cleaned_data.get('ilce'):
            instance.ilce = self.cleaned_data['ilce']
        
        if commit:
            instance.save()

        return instance


# ============================================================
# CMS Forms - İçerik Yönetim Sistemi Formları
# ============================================================

class HeroSlideForm(forms.ModelForm):
    """Hero slide oluşturma/düzenleme formu"""

    class Meta:
        model = HeroSlide
        fields = [
            'baslik', 'aciklama', 'arka_plan_resim', 'arka_plan_renk',
            'buton_1_metin', 'buton_1_url', 'buton_2_metin', 'buton_2_url',
            'sira', 'aktif'
        ]
        widgets = {
            'baslik': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Örn: Evcil Dostunuz İçin Akıllı Kimlik'
            }),
            'aciklama': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Slide açıklama metni...'
            }),
            'arka_plan_resim': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'arka_plan_renk': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'linear-gradient(135deg, rgba(255, 107, 157, 0.95) 0%, rgba(78, 205, 196, 0.85) 100%)'
            }),
            'buton_1_metin': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Boş bırakırsanız "Bulunan Hayvanı Bildir" kullanılır'
            }),
            'buton_1_url': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '/url/yolu/'
            }),
            'buton_2_metin': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Boş bırakırsanız "Yeni Etiket Aktive Et" kullanılır'
            }),
            'buton_2_url': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '/url/yolu/'
            }),
            'sira': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'aktif': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        help_texts = {
            'arka_plan_resim': '1920x1080 önerilen boyut. Resim yüklerseniz renk/gradient arka planda kalır.',
            'arka_plan_renk': 'CSS gradient kodu veya düz renk (#FF6B9D gibi)',
            'sira': 'Slide\'ların gösterilme sırası (küçükten büyüğe)',
        }


class HizmetKartiForm(forms.ModelForm):
    """Hizmet kartı oluşturma/düzenleme formu"""

    class Meta:
        model = HizmetKarti
        fields = [
            'baslik', 'aciklama', 'ikon', 'buton_metin', 'buton_url',
            'sira', 'aktif', 'animasyon_gecikmesi'
        ]
        widgets = {
            'baslik': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Örn: QR Etiket Sistemi'
            }),
            'aciklama': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Hizmet açıklaması...'
            }),
            'ikon': forms.Select(attrs={
                'class': 'form-control'
            }),
            'buton_metin': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Örn: Keşfet, İncele, Başla'
            }),
            'buton_url': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '/url/yolu/'
            }),
            'sira': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'aktif': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'animasyon_gecikmesi': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '100'
            }),
        }
        help_texts = {
            'ikon': 'Font Awesome ikonu (kartın üstünde görünür)',
            'animasyon_gecikmesi': 'Animasyon gecikmesi (ms), genellikle 0, 100, 200 gibi değerler kullanılır',
        }


class AnaSayfaAyarForm(forms.ModelForm):
    """Ana sayfa genel ayarlar formu"""

    class Meta:
        model = AnaSayfaAyar
        fields = [
            'hizmetler_baslik', 'hizmetler_aciklama',
            'slide_gecis_suresi', 'slide_animasyon'
        ]
        widgets = {
            'hizmetler_baslik': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Örn: Hizmetlerimiz'
            }),
            'hizmetler_aciklama': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Hizmetler bölümü açıklaması...'
            }),
            'slide_gecis_suresi': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1000',
                'step': '1000'
            }),
            'slide_animasyon': forms.Select(attrs={
                'class': 'form-control'
            }, choices=[
                ('fade', 'Fade (Solma)'),
                ('slide', 'Slide (Kaydırma)'),
            ]),
        }
        help_texts = {
            'slide_gecis_suresi': 'Milisaniye cinsinden (5000 = 5 saniye)',
            'slide_animasyon': 'Slide geçiş animasyon türü',
        }


class HesapAyarlariForm(forms.ModelForm):
    """Genel kullanıcı hesap ayarları formu - kullanıcı bilgileri ve şifre değiştirme"""
    
    # Şifre değiştirme alanları
    new_password1 = forms.CharField(
        label="Yeni Şifre",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Boş bırakırsanız şifre değişmez."
    )
    new_password2 = forms.CharField(
        label="Yeni Şifre (Tekrar)",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Yeni şifrenizi tekrar girin."
    )
    
    # Mevcut şifre kontrolü
    current_password = forms.CharField(
        label="Mevcut Şifre",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Şifre değiştirmek için mevcut şifrenizi girin."
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Email alanını zorunlu yap
        self.fields['email'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        current_password = cleaned_data.get('current_password')
        
        # Şifre değiştirme kontrolü
        if new_password1 or new_password2:
            if not current_password:
                raise forms.ValidationError("Şifre değiştirmek için mevcut şifrenizi girmelisiniz.")
            
            # Mevcut şifre kontrolü
            if not authenticate(username=self.instance.username, password=current_password):
                raise forms.ValidationError("Mevcut şifreniz yanlış.")
            
            if new_password1 != new_password2:
                raise forms.ValidationError("Yeni şifreler eşleşmiyor.")
            
            if len(new_password1) < 8:
                raise forms.ValidationError("Yeni şifre en az 8 karakter olmalıdır.")
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Şifre değiştirme
        new_password = self.cleaned_data.get('new_password1')
        if new_password:
            user.set_password(new_password)
        
        if commit:
            user.save()
        
        return user
