from django import forms
from django.utils import timezone
from datetime import date, time, timedelta
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm

from anahtarlik.dictionaries import Il, Ilce, Mahalle
from .models import Veteriner, SiparisIstemi, VeterinerHizmet, VeterinerDegerlendirme


class VeterinerProfilForm(forms.ModelForm):
    """Veteriner temel profil bilgileri formu"""
    il = forms.ModelChoiceField(
        label="İl",
        queryset=Il.objects.all().order_by("ad"),
        required=True,
        widget=forms.Select(attrs={"class": "form-control", "id": "id_il"}),
    )
    ilce = forms.ModelChoiceField(
        label="İlçe",
        queryset=Ilce.objects.none(),
        required=True,
        widget=forms.Select(attrs={"class": "form-control", "id": "id_ilce"}),
    )
    mahalle = forms.ModelChoiceField(
        label="Mahalle",
        queryset=Mahalle.objects.none(),
        required=False,
        widget=forms.Select(attrs={"class": "form-control", "id": "id_mahalle"}),
    )
    mahalle_diger = forms.CharField(
        label="Mahalle (Manuel)",
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "id": "id_mahalle_diger",
            "placeholder": "Mahalle listede yoksa buraya yazınız"
        }),
    )
    
    class Meta:
        model = Veteriner
        fields = ['ad', 'telefon', 'email', 'adres_detay']
        widgets = {
            'ad': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'telefon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '05XX XXX XX XX'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'adres_detay': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # İlçe ve mahalle queryset'lerini başlangıçta boş yap
        self.fields['ilce'].queryset = Ilce.objects.none()
        self.fields['mahalle'].queryset = Mahalle.objects.none()

        # Mevcut veteriner instance varsa cascade filtrele
        if self.instance and self.instance.pk:
            if self.instance.il:
                self.fields['ilce'].queryset = Ilce.objects.filter(il=self.instance.il).order_by("ad")

            if self.instance.ilce:
                self.fields['mahalle'].queryset = Mahalle.objects.filter(ilce=self.instance.ilce).order_by("ad")

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

        # İl, İlçe, Mahalle ve Mahalle_diger field'larını manuel olarak kaydet
        if self.cleaned_data.get('il'):
            instance.il = self.cleaned_data['il']
        if self.cleaned_data.get('ilce'):
            instance.ilce = self.cleaned_data['ilce']
        if self.cleaned_data.get('mahalle'):
            instance.mahalle = self.cleaned_data['mahalle']
        if self.cleaned_data.get('mahalle_diger'):
            instance.mahalle_diger = self.cleaned_data['mahalle_diger']

        if commit:
            instance.save()

        return instance








class VeterinerDegerlendirmeForm(forms.ModelForm):
    class Meta:
        model = VeterinerDegerlendirme
        fields = ["puan", "yorum", "musteri_adi", "musteri_telefon"]
        widgets = {
            "puan": forms.Select(attrs={"class": "form-select"}, choices=[
                (1, "1 - Çok Kötü"),
                (2, "2 - Kötü"),
                (3, "3 - Orta"),
                (4, "4 - İyi"),
                (5, "5 - Mükemmel"),
            ]),
            "yorum": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Deneyiminizi paylaşın..."}),
            "musteri_adi": forms.TextInput(attrs={"class": "form-control"}),
            "musteri_telefon": forms.TextInput(attrs={"class": "form-control"}),
        }


class SiparisForm(forms.ModelForm):
    il = forms.ModelChoiceField(
        label="İl",
        queryset=Il.objects.all().order_by("ad"),
        empty_label="Seçiniz",
        required=False,
        widget=forms.Select(attrs={"class": "form-control", "data-district-target": "id_ilce"}),
    )
    ilce = forms.ModelChoiceField(
        label="İlçe",
        queryset=Ilce.objects.none(),
        empty_label="Seçiniz",
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = SiparisIstemi
        fields = ["talep_edilen_adet", "farkli_adres_kullan", "il", "ilce", "adres_detay"]
        widgets = {
            "talep_edilen_adet": forms.NumberInput(attrs={"class": "form-control", "min": 5}),
            "farkli_adres_kullan": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "adres_detay": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        il_field = self.fields["il"]
        ilce_field = self.fields["ilce"]
        ilce_field.widget.attrs.setdefault("data-district-placeholder", ilce_field.empty_label or "Seçiniz")

        # İlçe queryset'ini tüm ilçeleri içerecek şekilde ayarla
        # Bu sayede validation hatası almayız
        ilce_field.queryset = Ilce.objects.all().order_by("ad")
        
        selected_il = None
        initial_il = self.initial.get("il") or getattr(self.instance, "il", "")
        if isinstance(initial_il, Il):
            selected_il = initial_il
        elif initial_il:
            selected_il = Il.objects.filter(ad=initial_il).first()
        if selected_il:
            il_field.initial = selected_il
            ilce_qs = Ilce.objects.filter(il=selected_il).order_by("ad")
            ilce_field.queryset = ilce_qs
            initial_ilce = self.initial.get("ilce") or getattr(self.instance, "ilce", "")
            if isinstance(initial_ilce, Ilce):
                ilce_field.initial = initial_ilce
            elif initial_ilce:
                ilce_field.initial = ilce_qs.filter(ad=initial_ilce).first()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("farkli_adres_kullan"):
            if not cleaned.get("il") or not cleaned.get("ilce") or not cleaned.get("adres_detay"):
                raise forms.ValidationError("Farklı adrese gönderim seçildi. İl / İlçe / Adres zorunlu.")
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        il_obj = self.cleaned_data.get("il")
        ilce_obj = self.cleaned_data.get("ilce")
        instance.il = il_obj  # Model instance atanmalı, string değil
        instance.ilce = ilce_obj  # Model instance atanmalı, string değil
        if commit:
            instance.save()
        return instance


class VeterinerWebForm(forms.ModelForm):
    # Slug düzenleme için özel alan
    web_slug = forms.SlugField(
        required=False,
        max_length=200,
        help_text="URL slug (boş bırakırsanız otomatik oluşturulur)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'pati-veteriner-klinigi'
        })
    )
    
    class Meta:
        model = Veteriner
        fields = [
            'web_aktif', 'web_baslik', 'web_slogan', 'web_aciklama',
            'logo', 'birincil_renk',
            'web_resim1', 'web_resim2', 'web_resim3',
            'hizmet1_baslik','hizmet1_aciklama','hizmet1_icon',
            'hizmet2_baslik','hizmet2_aciklama','hizmet2_icon',
            'hizmet3_baslik','hizmet3_aciklama','hizmet3_icon',
            'website','instagram','facebook','twitter','linkedin','youtube',
            'cta_metin','cta_link','whatsapp',
            'uzmanlik_alanlari', 'calisma_saatleri',  # Yeni eklenenler
            'konum_koordinat',  # Yeni eklenen
            'goster_sosyal', 'goster_hizmetler', 'goster_calisma_saatleri', 'goster_galeri',  # Yeni eklenenler
            'pazartesi_baslangic','pazartesi_bitis','pazartesi_kapali',
            'sali_baslangic','sali_bitis','sali_kapali',
            'carsamba_baslangic','carsamba_bitis','carsamba_kapali',
            'persembe_baslangic','persembe_bitis','persembe_kapali',
            'cuma_baslangic','cuma_bitis','cuma_kapali',
            'cumartesi_baslangic','cumartesi_bitis','cumartesi_kapali',
            'pazar_baslangic','pazar_bitis','pazar_kapali',
            'web_seo_baslik','web_seo_aciklama','web_seo_anahtar_kelimeler'
        ]
        widgets = {
            'birincil_renk': forms.TextInput(attrs={'class':'form-control','placeholder':'#4cc9f0'}),
            'logo': forms.FileInput(attrs={'class':'form-control','accept':'image/*'}),
            'web_resim1': forms.FileInput(attrs={'class':'form-control','accept':'image/*'}),
            'web_resim2': forms.FileInput(attrs={'class':'form-control','accept':'image/*'}),
            'web_resim3': forms.FileInput(attrs={'class':'form-control','accept':'image/*'}),
            'cta_metin': forms.TextInput(attrs={'class':'form-control','placeholder':'Randevu Al'}),
            'cta_link': forms.URLInput(attrs={'class':'form-control','placeholder':'https://...'}),
            'whatsapp': forms.TextInput(attrs={'class':'form-control','placeholder':'905551112233'}),
            'uzmanlik_alanlari': forms.Textarea(attrs={'class':'form-control','rows':3,'placeholder':'Kedi, Köpek, Kuş, Tavşan (virgülle ayırın)'}),
            'calisma_saatleri': forms.Textarea(attrs={'class':'form-control','rows':2,'placeholder':'Pazartesi-Cuma: 09:00-18:00, Cumartesi: 10:00-16:00'}),
            'konum_koordinat': forms.TextInput(attrs={'class':'form-control','placeholder':'38.231952, 42.428070'}),
            'hizmet1_icon': forms.TextInput(attrs={'class':'form-control','placeholder':'🩺 (emoji veya FontAwesome icon)'}),
            'hizmet2_icon': forms.TextInput(attrs={'class':'form-control','placeholder':'💉 (emoji veya FontAwesome icon)'}),
            'hizmet3_icon': forms.TextInput(attrs={'class':'form-control','placeholder':'🔬 (emoji veya FontAwesome icon)'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Slug alanını instance'dan al
        if self.instance and self.instance.pk and self.instance.web_slug:
            self.fields['web_slug'].initial = self.instance.web_slug
    
    def clean_birincil_renk(self):
        """HEX renk formatı kontrolü"""
        renk = self.cleaned_data.get('birincil_renk')
        if renk is None:
            return ''
        renk = str(renk).strip()
        if renk:
            # HEX format kontrolü (# ile başlamalı, 6 veya 3 karakter)
            import re
            hex_pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
            if not re.match(hex_pattern, renk):
                raise forms.ValidationError(
                    "Renk formatı geçersiz. HEX formatında olmalı (örn: #4cc9f0 veya #4cf)"
                )
        return renk
    
    def clean_whatsapp(self):
        """WhatsApp numarası format kontrolü"""
        whatsapp = self.cleaned_data.get('whatsapp')
        if whatsapp is None:
            return ''
        whatsapp = str(whatsapp).strip()
        if whatsapp:
            # Sadece rakam olmalı
            if not whatsapp.isdigit():
                raise forms.ValidationError(
                    "WhatsApp numarası sadece rakamlardan oluşmalı (örn: 905551112233)"
                )
            # Minimum 10, maksimum 15 karakter
            if len(whatsapp) < 10 or len(whatsapp) > 15:
                raise forms.ValidationError(
                    "WhatsApp numarası 10-15 karakter arasında olmalı"
                )
        return whatsapp
    
    def clean_konum_koordinat(self):
        """Koordinat formatı kontrolü"""
        koordinat = self.cleaned_data.get('konum_koordinat')
        if koordinat is None:
            return ''
        koordinat = str(koordinat).strip()
        if koordinat:
            # Format: "lat, lng" veya "lat,lng"
            import re
            coord_pattern = r'^-?\d+\.?\d*,\s*-?\d+\.?\d*$'
            if not re.match(coord_pattern, koordinat):
                raise forms.ValidationError(
                    "Koordinat formatı geçersiz. Format: '38.231952, 42.428070' (enlem, boylam)"
                )
            # Değer aralığı kontrolü
            try:
                parts = koordinat.replace(' ', '').split(',')
                lat = float(parts[0])
                lng = float(parts[1])
                if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                    raise forms.ValidationError(
                        "Koordinat değerleri geçersiz. Enlem: -90 ile 90, Boylam: -180 ile 180 arasında olmalı"
                    )
            except (ValueError, IndexError):
                raise forms.ValidationError(
                    "Koordinat formatı geçersiz. Format: '38.231952, 42.428070'"
                )
        return koordinat
    
    def clean_web_slug(self):
        """Slug çakışma kontrolü"""
        slug = self.cleaned_data.get('web_slug')
        if slug is None:
            return ''
        slug = str(slug).strip()
        if slug:
            # Mevcut slug'ı kontrol et
            existing = Veteriner.objects.filter(web_slug=slug)
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError(
                    f"Bu slug zaten kullanılıyor: '{slug}'. Lütfen farklı bir slug seçin."
                )
        return slug
    
    def clean_cta_link(self):
        """CTA link format kontrolü"""
        cta_link = self.cleaned_data.get('cta_link')
        if cta_link is None:
            return ''
        cta_link = str(cta_link).strip()
        if cta_link:
            # URL format kontrolü
            if not (cta_link.startswith('http://') or cta_link.startswith('https://')):
                raise forms.ValidationError(
                    "Link 'http://' veya 'https://' ile başlamalı"
                )
        return cta_link
    
    def clean_website(self):
        """Website URL format kontrolü"""
        website = self.cleaned_data.get('website')
        if website is None:
            return ''
        website = str(website).strip()
        if website:
            if not (website.startswith('http://') or website.startswith('https://')):
                raise forms.ValidationError(
                    "Website URL'si 'http://' veya 'https://' ile başlamalı"
                )
        return website
    
    def clean_instagram(self):
        """Instagram format kontrolü"""
        instagram = self.cleaned_data.get('instagram')
        if instagram is None:
            return ''
        instagram = str(instagram).strip()
        if instagram:
            # @ işareti varsa kaldır
            if instagram.startswith('@'):
                instagram = instagram[1:]
            # URL formatında değilse, sadece kullanıcı adı olmalı
            if 'http' in instagram or 'instagram.com' in instagram:
                if not (instagram.startswith('http://') or instagram.startswith('https://')):
                    raise forms.ValidationError(
                        "Instagram linki 'http://' veya 'https://' ile başlamalı"
                    )
        return instagram
    
    def clean_facebook(self):
        """Facebook format kontrolü"""
        facebook = self.cleaned_data.get('facebook')
        if facebook is None:
            return ''
        facebook = str(facebook).strip()
        if facebook:
            # URL formatında değilse, sadece kullanıcı adı olabilir
            if 'http' in facebook or 'facebook.com' in facebook:
                if not (facebook.startswith('http://') or facebook.startswith('https://')):
                    raise forms.ValidationError(
                        "Facebook linki 'http://' veya 'https://' ile başlamalı"
                    )
        return facebook
    
    def clean_twitter(self):
        """Twitter/X format kontrolü"""
        twitter = self.cleaned_data.get('twitter')
        if twitter is None:
            return ''
        twitter = str(twitter).strip()
        if twitter:
            # @ işareti varsa kaldır
            if twitter.startswith('@'):
                twitter = twitter[1:]
            # URL formatında değilse, sadece kullanıcı adı olmalı
            if 'http' in twitter or 'twitter.com' in twitter or 'x.com' in twitter:
                if not (twitter.startswith('http://') or twitter.startswith('https://')):
                    raise forms.ValidationError(
                        "Twitter/X linki 'http://' veya 'https://' ile başlamalı"
                    )
        return twitter
    
    def clean_linkedin(self):
        """LinkedIn format kontrolü"""
        linkedin = self.cleaned_data.get('linkedin')
        if linkedin is None:
            return ''
        linkedin = str(linkedin).strip()
        if linkedin:
            if 'http' in linkedin or 'linkedin.com' in linkedin:
                if not (linkedin.startswith('http://') or linkedin.startswith('https://')):
                    raise forms.ValidationError(
                        "LinkedIn linki 'http://' veya 'https://' ile başlamalı"
                    )
        return linkedin
    
    def clean_youtube(self):
        """YouTube format kontrolü"""
        youtube = self.cleaned_data.get('youtube')
        if youtube is None:
            return ''
        youtube = str(youtube).strip()
        if youtube:
            if 'http' in youtube or 'youtube.com' in youtube or 'youtu.be' in youtube:
                if not (youtube.startswith('http://') or youtube.startswith('https://')):
                    raise forms.ValidationError(
                        "YouTube linki 'http://' veya 'https://' ile başlamalı"
                    )
        return youtube
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Slug'ı kaydet (eğer manuel girildiyse)
        slug = self.cleaned_data.get('web_slug', '').strip()
        if slug:
            instance.web_slug = slug
        elif not instance.web_slug and instance.ad:
            # Slug yoksa otomatik oluştur (model'in save metodunda yapılacak)
            pass
        
        if commit:
            instance.save()
        return instance


class VeterinerHesapForm(forms.ModelForm):
    """Veteriner hesap ayarları formu - kullanıcı bilgileri ve şifre değiştirme"""
    
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
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        
        # Şifre değiştirme kontrolü
        if new_password1 or new_password2:
            if not new_password1:
                raise forms.ValidationError("Yeni şifre gerekli.")
            if not new_password2:
                raise forms.ValidationError("Şifre tekrarı gerekli.")
            if new_password1 != new_password2:
                raise forms.ValidationError("Şifreler eşleşmiyor.")
            if len(new_password1) < 8:
                raise forms.ValidationError("Şifre en az 8 karakter olmalı.")
        
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
