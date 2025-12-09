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
    web_slug = forms.SlugField(
        required=False,
        label="Web Sayfası URL Adresi",
        help_text="Örnek: pati-veteriner-klinigi (sadece küçük harf, rakam ve tire kullanın. Türkçe karakterler otomatik dönüştürülür.)",
        widget=forms.TextInput(attrs={
            'class': 'w-full p-4 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all',
            'placeholder': 'pati-veteriner-klinigi'
        })
    )
    
    class Meta:
        model = Veteriner
        fields = [
            'web_slug',  # En başa eklendi
            'web_aktif', 'web_baslik', 'web_slogan', 'web_aciklama',
            'logo', 'birincil_renk',
            'web_resim1', 'web_resim2', 'web_resim3',
            'hizmet1_baslik','hizmet1_aciklama','hizmet1_icon',
            'hizmet2_baslik','hizmet2_aciklama','hizmet2_icon',
            'hizmet3_baslik','hizmet3_aciklama','hizmet3_icon',
            'website','instagram','facebook','twitter','linkedin','youtube',
            'cta_metin','cta_link','whatsapp',
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
        }
    
    def clean_web_slug(self):
        """Web slug validasyonu - benzersizlik kontrolü ve temizleme"""
        web_slug = self.cleaned_data.get('web_slug', '').strip()
        
        # Boş bırakılabilir (otomatik oluşturulacak)
        if not web_slug:
            return None
        
        # Türkçe karakterleri temizle ve slugify
        from django.utils.text import slugify
        tr_map = str.maketrans('çğıöşüÇĞIÖŞÜ', 'cgiosuCGIOSU')
        temiz_slug = web_slug.translate(tr_map)
        web_slug = slugify(temiz_slug, allow_unicode=False)
        
        # Boş slug kontrolü (sadece özel karakterler girilmişse)
        if not web_slug:
            raise forms.ValidationError(
                "Geçerli bir URL adresi giriniz. Sadece küçük harf, rakam ve tire (-) kullanabilirsiniz."
            )
        
        # Minimum uzunluk kontrolü
        if len(web_slug) < 3:
            raise forms.ValidationError(
                "URL adresi en az 3 karakter olmalıdır."
            )
        
        # Maksimum uzunluk kontrolü (model'de 200, ama daha kısa tutalım)
        if len(web_slug) > 100:
            raise forms.ValidationError(
                "URL adresi çok uzun. Maksimum 100 karakter olabilir."
            )
        
        # Benzersizlik kontrolü
        instance = self.instance
        mevcut_veteriner = Veteriner.objects.filter(web_slug=web_slug).exclude(pk=instance.pk if instance.pk else None).first()
        
        if mevcut_veteriner:
            # Öneri oluştur
            oneri_slug = f"{web_slug}-{instance.pk}" if instance.pk else f"{web_slug}-{Veteriner.objects.count() + 1}"
            raise forms.ValidationError(
                f"Bu URL adresi zaten kullanılıyor. Lütfen farklı bir adres seçin. "
                f"Öneri: '{oneri_slug}' veya '{web_slug}-{instance.ad[:10].lower().replace(' ', '-') if instance.ad else 'klinik'}'"
            )
        
        return web_slug
    
    def clean(self):
        """Form genel validasyonu"""
        cleaned_data = super().clean()
        web_aktif = cleaned_data.get('web_aktif', False)
        web_slug = cleaned_data.get('web_slug', '').strip() if cleaned_data.get('web_slug') else None
        web_baslik = cleaned_data.get('web_baslik', '').strip()
        
        # Web aktif seçilmişse ama slug yoksa ve başlık da yoksa uyarı ver
        if web_aktif and not web_slug and not web_baslik:
            raise forms.ValidationError({
                'web_aktif': 'Web sayfanızı yayına almak için önce "Web Sayfası URL Adresi" veya "Başlık (Klinik Adı)" alanını doldurmanız gerekiyor.'
            })
        
        # Çalışma saatleri validasyonu - Kapalı olmayan günler için başlangıç ve bitiş zorunlu
        gunler = [
            ('pazartesi', 'Pazartesi'),
            ('sali', 'Salı'),
            ('carsamba', 'Çarşamba'),
            ('persembe', 'Perşembe'),
            ('cuma', 'Cuma'),
            ('cumartesi', 'Cumartesi'),
            ('pazar', 'Pazar'),
        ]
        
        for gun_adi, gun_label in gunler:
            kapali = cleaned_data.get(f'{gun_adi}_kapali', False)
            baslangic = cleaned_data.get(f'{gun_adi}_baslangic')
            bitis = cleaned_data.get(f'{gun_adi}_bitis')
            
            # Eğer gün kapalı değilse, başlangıç ve bitiş saatleri zorunlu
            if not kapali:
                if not baslangic:
                    self.add_error(f'{gun_adi}_baslangic', f'{gun_label} günü için başlangıç saati zorunludur.')
                if not bitis:
                    self.add_error(f'{gun_adi}_bitis', f'{gun_label} günü için bitiş saati zorunludur.')
                
                # Başlangıç ve bitiş saatleri varsa, bitiş başlangıçtan sonra olmalı
                if baslangic and bitis and bitis <= baslangic:
                    self.add_error(f'{gun_adi}_bitis', f'{gun_label} günü için bitiş saati, başlangıç saatinden sonra olmalıdır.')
        
        return cleaned_data
    
    def save(self, commit=True):
        """Form kaydetme - web_slug yoksa otomatik oluştur, eski fotoğrafları sil"""
        instance = super().save(commit=False)
        
        # Eski fotoğrafları kontrol et ve sil
        if instance.pk:
            eski_veteriner = Veteriner.objects.get(pk=instance.pk)
            
            # Logo değiştiyse eski logo'yu sil
            if 'logo' in self.changed_data and eski_veteriner.logo:
                try:
                    eski_veteriner.logo.delete(save=False)
                except Exception:
                    pass
            
            # Web resimleri değiştiyse eski resimleri sil
            if 'web_resim1' in self.changed_data and eski_veteriner.web_resim1:
                try:
                    eski_veteriner.web_resim1.delete(save=False)
                except Exception:
                    pass
            
            if 'web_resim2' in self.changed_data and eski_veteriner.web_resim2:
                try:
                    eski_veteriner.web_resim2.delete(save=False)
                except Exception:
                    pass
            
            if 'web_resim3' in self.changed_data and eski_veteriner.web_resim3:
                try:
                    eski_veteriner.web_resim3.delete(save=False)
                except Exception:
                    pass
        
        # Eğer web_slug boşsa ve web_baslik varsa, otomatik oluştur
        if not instance.web_slug and instance.web_baslik:
            from django.utils.text import slugify
            tr_map = str.maketrans('çğıöşüÇĞIÖŞÜ', 'cgiosuCGIOSU')
            temiz_ad = instance.web_baslik.translate(tr_map)
            base_slug = slugify(temiz_ad, allow_unicode=False)
            
            if base_slug:  # Slug oluşturulabildiyse
                slug = base_slug
                counter = 1
                # Benzersiz slug bul
                while Veteriner.objects.filter(web_slug=slug).exclude(pk=instance.pk).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                    # Sonsuz döngü önleme
                    if counter > 1000:
                        slug = f"{base_slug}-{instance.pk}" if instance.pk else f"{base_slug}-{Veteriner.objects.count() + 1}"
                        break
                instance.web_slug = slug
        
        # Web sayfası yayına alınınca aktif yap
        web_aktif = self.cleaned_data.get('web_aktif', False)
        if web_aktif and instance.web_slug:
            # Web sayfası yayına alınıyor ve slug var → aktif yap
            if not instance.aktif:
                instance.aktif = True
                # Aktif olunca atamalar yapılacak (save metodunda)
        
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
