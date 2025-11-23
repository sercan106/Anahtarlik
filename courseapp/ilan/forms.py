# ilan/forms.py

from django import forms
from django.contrib.auth.models import User
from .models import HayvanProfili, Ilan, HayvanResmi
from anahtarlik.dictionaries import Il, Ilce, Tur, Irk, Mahalle


class HayvanProfiliForm(forms.ModelForm):
    """Hayvan profili oluşturma formu"""
    
    class Meta:
        model = HayvanProfili
        fields = [
            'hayvan_adi', 'tur', 'irk', 'dogum_tarihi', 'cinsiyet',
            'asi_durumu', 'ic_parazit', 'dis_parazit',
            'sehir_disi_gonderim',
            'il', 'ilce', 'mahalle', 'telefon', 'aciklama', 'profil_fotografi'
        ]
        widgets = {
            'hayvan_adi': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Hayvan adını girin'
            }),
            'tur': forms.Select(attrs={
                'class': 'form-control'
            }),
            'irk': forms.Select(attrs={
                'class': 'form-control'
            }),
            'dogum_tarihi': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'Doğum tarihi seçin'
            }),
            'cinsiyet': forms.Select(attrs={
                'class': 'form-control'
            }),
            'il': forms.Select(attrs={
                'class': 'form-control'
            }),
            'ilce': forms.Select(attrs={
                'class': 'form-control'
            }),
            'mahalle': forms.Select(attrs={
                'class': 'form-control'
            }),
            'telefon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '05XX XXX XX XX',
                'pattern': '^(\+90|0)?[5][0-9]{9}$'
            }),
            'aciklama': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Hayvan hakkında detaylı bilgi verin'
            }),
            'profil_fotografi': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'required': True
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # İl seçeneklerini doldur
        self.fields['il'].queryset = Il.objects.all().order_by('ad')
        self.fields['il'].empty_label = "İl seçin"
        
        # İlçe ve mahalle cascade dropdown'ları için başlangıçta boş
        self.fields['ilce'].queryset = Ilce.objects.none()
        self.fields['ilce'].empty_label = "Önce il seçiniz"
        self.fields['ilce'].required = True  # Backend'de zorunlu
        
        # Mahalle dropdown
        self.fields['mahalle'].queryset = Mahalle.objects.none()  # Başlangıçta boş
        self.fields['mahalle'].empty_label = "Önce ilçe seçiniz"
        self.fields['mahalle'].required = False  # Optional
        
        # POST data varsa cascade filtrele
        if 'il' in self.data:
            try:
                il_id = int(self.data.get('il'))
                self.fields['ilce'].queryset = Ilce.objects.filter(il_id=il_id).order_by("ad")
            except (ValueError, TypeError):
                pass
        
        if 'ilce' in self.data:
            try:
                ilce_id = int(self.data.get('ilce'))
                self.fields['mahalle'].queryset = Mahalle.objects.filter(ilce_id=ilce_id).order_by("ad")
            except (ValueError, TypeError):
                pass
        
        # Tür seçeneklerini doldur
        self.fields['tur'].queryset = Tur.objects.all().order_by('ad')
        self.fields['tur'].empty_label = "Tür seçin"
        
        # Irk seçeneklerini ayarla - tür seçiliyse ona göre filtrele
        # Instance varsa (düzenleme durumu) instance'dan al
        if self.instance and self.instance.pk and self.instance.tur_id:
            self.fields['irk'].queryset = Irk.objects.filter(tur_id=self.instance.tur_id).order_by('ad')
            self.fields['irk'].empty_label = "Irk seçin"
        # POST data varsa (form gönderilmişse veya geri dönüş durumu) tür'e göre filtrele
        elif self.data and 'tur' in self.data:
            try:
                tur_id = int(self.data.get('tur'))
                if tur_id:
                    self.fields['irk'].queryset = Irk.objects.filter(tur_id=tur_id).order_by('ad')
                    self.fields['irk'].empty_label = "Irk seçin"
                else:
                    self.fields['irk'].queryset = Irk.objects.none()
                    self.fields['irk'].empty_label = "Önce tür seçiniz"
            except (ValueError, TypeError):
                self.fields['irk'].queryset = Irk.objects.none()
                self.fields['irk'].empty_label = "Önce tür seçiniz"
        else:
            # İlk yüklemede veya tür seçilmemişse boş göster
            self.fields['irk'].queryset = Irk.objects.none()
            self.fields['irk'].empty_label = "Önce tür seçiniz"
        
        # Boolean alanları optional yap ve checkbox stil
        boolean_fields = ['asi_durumu', 'ic_parazit', 'dis_parazit', 'sehir_disi_gonderim']
        for field in boolean_fields:
            self.fields[field].required = False
            self.fields[field].widget = forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        
        # Doğum tarihi için bugünün tarihini max olarak ayarla ve zorunlu yap
        from datetime import date
        if 'dogum_tarihi' in self.fields:
            self.fields['dogum_tarihi'].widget.attrs['max'] = date.today().strftime('%Y-%m-%d')
            self.fields['dogum_tarihi'].required = True
        
        # Profil fotoğrafını zorunlu yap
        if 'profil_fotografi' in self.fields:
            self.fields['profil_fotografi'].required = True
        
        # Telefon numarasını zorunlu yap
        if 'telefon' in self.fields:
            self.fields['telefon'].required = True
    
    def clean_dogum_tarihi(self):
        """Doğum tarihi validasyonu - gelecek tarih seçilemez"""
        dogum_tarihi = self.cleaned_data.get('dogum_tarihi')
        if dogum_tarihi:
            from datetime import date
            if dogum_tarihi > date.today():
                raise forms.ValidationError("Doğum tarihi gelecekten bir tarih olamaz!")
        return dogum_tarihi


class IlanForm(forms.ModelForm):
    """İlan oluşturma formu"""
    
    # Sadece sahiplendirme seçeneği
    ilan_turu = forms.ChoiceField(
        choices=[('SAHIPLENDIRME', 'Sahiplendirme')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Ilan
        fields = ['hayvan_profili', 'baslik', 'ilan_turu', 'aciklama', 'onemli_mi']
        widgets = {
            'hayvan_profili': forms.Select(attrs={
                'class': 'form-control'
            }),
            'baslik': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'İlan başlığını girin'
            }),
            'ilan_turu': forms.Select(attrs={
                'class': 'form-control'
            }),
            'aciklama': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'İlan açıklamasını girin'
            }),
            'onemli_mi': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Sadece kullanıcının aktif hayvan profillerini göster
            self.fields['hayvan_profili'].queryset = HayvanProfili.objects.filter(
                kullanici=user,
                aktif=True
            ).order_by('-olusturulma_tarihi')
            self.fields['hayvan_profili'].empty_label = "Hayvan profili seçin"
        


class HayvanResmiForm(forms.ModelForm):
    """Hayvan resmi ekleme formu"""
    
    class Meta:
        model = HayvanResmi
        fields = ['resim', 'sira']
        widgets = {
            'resim': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'sira': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            })
        }


class HayvanResmiForm(forms.ModelForm):
    """Hayvan resmi yükleme formu"""
    
    class Meta:
        model = HayvanResmi
        fields = ['resim']
        widgets = {
            'resim': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }


class IlanAramaForm(forms.Form):
    """İlan arama ve filtreleme formu"""
    
    # Arama
    arama = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Hayvan adı, açıklama ara...'
        })
    )
    
    # Filtreler
    ilan_turu = forms.ChoiceField(
        required=False,
        choices=[('', 'Tüm İlanlar'), ('SAHIPLENDIRME', 'Sahiplendirme')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    tur = forms.ModelChoiceField(
        required=False,
        queryset=Tur.objects.all().order_by('ad'),
        empty_label="Tüm Türler",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    irk = forms.ModelChoiceField(
        required=False,
        queryset=Irk.objects.all().order_by('ad'),
        empty_label="Tüm Irklar",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    il = forms.ModelChoiceField(
        required=False,
        queryset=Il.objects.all().order_by('ad'),
        empty_label="Tüm İller",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    ilce = forms.ModelChoiceField(
        required=False,
        queryset=Ilce.objects.all().order_by('ad'),
        empty_label="Tüm İlçeler",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Fiyat aralığı
    min_fiyat = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min fiyat',
            'step': '0.01',
            'min': '0'
        })
    )
    
    max_fiyat = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max fiyat',
            'step': '0.01',
            'min': '0'
        })
    )
    
    # Öne çıkan ilanlar
    onemli_ilanlar = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # İlçe seçeneklerini dinamik olarak ayarla
        if 'il' in self.data:
            try:
                il_id = int(self.data.get('il'))
                self.fields['ilce'].queryset = Ilce.objects.filter(il_id=il_id).order_by('ad')
            except (ValueError, TypeError):
                pass
