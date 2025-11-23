from django import forms
from django.contrib.auth.models import User
from django.utils import timezone

from anahtarlik.models import EvcilHayvan, Sahip
from anahtarlik.dictionaries import Tur, Irk, Il, Ilce, Mahalle


class EvcilHayvanKayitForm(forms.Form):
    ad = forms.CharField(label="Ad", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    tur = forms.ModelChoiceField(label="Tür", queryset=Tur.objects.all().order_by('ad'), required=True, empty_label="Seçiniz", widget=forms.Select(attrs={'class': 'form-control'}))
    irk = forms.ModelChoiceField(label="Irk", queryset=Irk.objects.none(), required=True, empty_label="Seçiniz", widget=forms.Select(attrs={'class': 'form-control'}))

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
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        data = self.data or self.initial
        try:
            tur_id = int(data.get('tur')) if data.get('tur') else None
        except ValueError:
            tur_id = None
        if tur_id:
            self.fields['irk'].queryset = Irk.objects.filter(tur_id=tur_id).order_by('ad')
        else:
            self.fields['irk'].queryset = Irk.objects.none()

        self.fields['tur'].widget.attrs.setdefault('data-breed-target', 'id_irk')

    def clean(self):
        c = super().clean()
        if not c.get('tur'):
            self.add_error('tur', 'Lütfen bir tür seçin.')
        if c.get('tur') and not c.get('irk'):
            self.add_error('irk', 'Lütfen bir ırk seçin.')
        from datetime import date
        dogum_tarihi = c.get('dogum_tarihi')
        if dogum_tarihi:
            # Bugünün tarihini al (timezone-aware olmadan)
            bugun = date.today()
            if dogum_tarihi > bugun:
                self.add_error('dogum_tarihi', "Doğum tarihi gelecekte olamaz.")
        return c


class KullaniciAdresForm(forms.Form):
    ad = forms.CharField(max_length=50, label="Ad", widget=forms.TextInput(attrs={'class': 'form-control'}))
    soyad = forms.CharField(max_length=50, label="Soyad", widget=forms.TextInput(attrs={'class': 'form-control'}))
    username = forms.CharField(max_length=150, label="Kullanıcı Adı", widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(
        label="E-posta Adresi", 
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'ornek@email.com'
        })
    )
    telefon = forms.CharField(
        max_length=15, 
        label="Cep Telefonu", 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '5XX XXX XX XX',
            'pattern': '[0-9]{10,11}'
        })
    )
    yedek_telefon = forms.CharField(
        max_length=15, 
        label="Yedek Telefon", 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '5XX XXX XX XX (Opsiyonel)',
            'pattern': '[0-9]{10,11}'
        }), 
        required=False
    )

    il = forms.ModelChoiceField(label="İl", queryset=Il.objects.all().order_by('ad'), required=True, empty_label="Seçiniz", widget=forms.Select(attrs={'class': 'form-control'}))
    ilce = forms.ModelChoiceField(label="İlçe", queryset=Ilce.objects.none(), required=True, empty_label="Seçiniz", widget=forms.Select(attrs={'class': 'form-control'}))
    adres = forms.CharField(label="Detaylı Adres", widget=forms.Textarea(attrs={'class': 'form-control form-textarea'}))

    sifre = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="Şifre")
    sifre_tekrar = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="Şifre (Tekrar)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        data = self.data or self.initial
        try:
            il_id = int(data.get('il')) if data.get('il') else None
        except ValueError:
            il_id = None
        if il_id:
            self.fields['ilce'].queryset = Ilce.objects.filter(il_id=il_id).order_by('ad')
        else:
            self.fields['ilce'].queryset = Ilce.objects.none()

        self.fields['il'].widget.attrs.setdefault('data-district-target', 'id_ilce')

    def clean(self):
        cleaned_data = super().clean()
        sifre = cleaned_data.get("sifre")
        sifre_tekrar = cleaned_data.get("sifre_tekrar")
        if sifre and sifre_tekrar and sifre != sifre_tekrar:
            raise forms.ValidationError("Şifreler eşleşmiyor.")
        if not cleaned_data.get('il'):
            self.add_error('il', 'Lütfen bir il seçin.')
        if cleaned_data.get('il') and not cleaned_data.get('ilce'):
            self.add_error('ilce', 'Lütfen bir ilçe seçin.')
        return cleaned_data

    def clean_telefon(self):
        from veteriner.models import Veteriner
        from petshop.models import PetShop
        from accaunt.models import MisafirProfil
        
        telefon = self.cleaned_data.get('telefon')
        if telefon:
            # Telefon numarasını temizle
            telefon = ''.join(filter(str.isdigit, telefon))
            
            # Telefon numarası formatını kontrol et
            if len(telefon) < 10 or len(telefon) > 11:
                raise forms.ValidationError("Telefon numarası 10-11 haneli olmalıdır.")
            
            # 0 ile başlıyorsa kaldır
            if telefon.startswith('0'):
                telefon = telefon[1:]
            
            # 5 ile başlamalı
            if not telefon.startswith('5'):
                raise forms.ValidationError("Telefon numarası 5 ile başlamalıdır.")
            
            # Tüm profil tiplerinde benzersizlik kontrolü
            if Sahip.objects.filter(telefon=telefon).exists():
                raise forms.ValidationError(
                    "Bu telefon numarası zaten kayıtlı (Sahip). "
                    "Eğer bu sizin telefonunuz ise lütfen giriş yapın."
                )
            if Veteriner.objects.filter(telefon=telefon).exists():
                raise forms.ValidationError("Bu telefon numarası zaten kayıtlı (Veteriner).")
            if PetShop.objects.filter(telefon=telefon).exists():
                raise forms.ValidationError("Bu telefon numarası zaten kayıtlı (PetShop).")
            if MisafirProfil.objects.filter(telefon=telefon).exists():
                raise forms.ValidationError("Bu telefon numarası zaten kayıtlı (Misafir).")
        
        return telefon

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Bu kullanıcı adı zaten kullanılıyor.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Email'i küçük harfe çevir
            email = email.strip().lower()
            
            # Email formatını kontrol et
            if '@' not in email or '.' not in email.split('@')[1]:
                raise forms.ValidationError("Geçerli bir e-posta adresi girin.")
            
            # Benzersizlik kontrolü
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError("Bu e-posta adresi zaten kayıtlı.")
        
        return email


class GuestOwnerInfoForm(forms.Form):
    ad = forms.CharField(max_length=50, label="Ad", widget=forms.TextInput(attrs={'class': 'form-control'}))
    soyad = forms.CharField(max_length=50, label="Soyad", widget=forms.TextInput(attrs={'class': 'form-control'}))
    telefon = forms.CharField(
        max_length=15,
        label="Cep Telefonu",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '5XX XXX XX XX',
            'pattern': '[0-9]{10,11}'
        })
    )
    yedek_telefon = forms.CharField(
        max_length=15,
        label="Yedek Telefon",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '5XX XXX XX XX (Opsiyonel)',
            'pattern': '[0-9]{10,11}'
        })
    )
    il = forms.ModelChoiceField(label="İl", queryset=Il.objects.all().order_by('ad'), required=True, empty_label="Seçiniz", widget=forms.Select(attrs={'class': 'form-control'}))
    ilce = forms.ModelChoiceField(label="İlçe", queryset=Ilce.objects.none(), required=True, empty_label="Seçiniz", widget=forms.Select(attrs={'class': 'form-control'}))
    mahalle = forms.ModelChoiceField(label="Mahalle", queryset=Mahalle.objects.none(), required=False, empty_label="Seçiniz", widget=forms.Select(attrs={'class': 'form-control'}))
    mahalle_diger = forms.CharField(max_length=200, label="Mahalle (Manuel)", required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mahalle listede yoksa yazınız'}))
    adres = forms.CharField(label="Detaylı Adres", widget=forms.Textarea(attrs={'class': 'form-control form-textarea'}))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        data = self.data or self.initial

        try:
            il_id = int(data.get('il')) if data.get('il') else None
        except (TypeError, ValueError):
            il_id = None
        if il_id:
            self.fields['ilce'].queryset = Ilce.objects.filter(il_id=il_id).order_by('ad')
        else:
            self.fields['ilce'].queryset = Ilce.objects.none()

        try:
            ilce_id = int(data.get('ilce')) if data.get('ilce') else None
        except (TypeError, ValueError):
            ilce_id = None
        if ilce_id:
            self.fields['mahalle'].queryset = Mahalle.objects.filter(ilce_id=ilce_id).order_by('ad')
        else:
            self.fields['mahalle'].queryset = Mahalle.objects.none()

        self.fields['il'].widget.attrs.setdefault('data-district-target', 'id_ilce')
        self.fields['ilce'].widget.attrs.setdefault('data-mahalle-target', 'id_mahalle')

    def clean(self):
        cleaned_data = super().clean()
        il = cleaned_data.get('il')
        ilce = cleaned_data.get('ilce')
        mahalle = cleaned_data.get('mahalle')
        mahalle_diger = cleaned_data.get('mahalle_diger', '').strip()

        if not il:
            self.add_error('il', 'Lütfen bir il seçin.')
        if il and not ilce:
            self.add_error('ilce', 'Lütfen bir ilçe seçin.')

        if mahalle and mahalle_diger:
            self.add_error('mahalle_diger', 'Mahalle seçtiğinizde manuel mahalle alanını boş bırakın.')

        return cleaned_data

    def _normalize_phone(self, value):
        if not value:
            return ''
        digits = ''.join(filter(str.isdigit, value))
        if len(digits) == 11 and digits.startswith('0'):
            digits = digits[1:]
        return digits

    def clean_telefon(self):
        from veteriner.models import Veteriner
        from petshop.models import PetShop
        from accaunt.models import MisafirProfil

        telefon = self._normalize_phone(self.cleaned_data.get('telefon'))

        if len(telefon) != 10:
            raise forms.ValidationError("Telefon numarası 10 haneli olmalıdır.")
        if not telefon.startswith('5'):
            raise forms.ValidationError("Telefon numarası 5 ile başlamalıdır.")

        user = self.user

        if Sahip.objects.filter(telefon=telefon).exclude(kullanici=user).exists():
            raise forms.ValidationError("Bu telefon numarası zaten kayıtlı (Sahip).")
        if Veteriner.objects.filter(telefon=telefon).exists():
            raise forms.ValidationError("Bu telefon numarası zaten kayıtlı (Veteriner).")
        if PetShop.objects.filter(telefon=telefon).exists():
            raise forms.ValidationError("Bu telefon numarası zaten kayıtlı (PetShop).")

        misafir_qs = MisafirProfil.objects.filter(telefon=telefon)
        if user and hasattr(user, 'misafir_profili'):
            misafir_qs = misafir_qs.exclude(pk=user.misafir_profili.pk)
        if misafir_qs.exists():
            raise forms.ValidationError("Bu telefon numarası zaten kayıtlı (Misafir).")

        return telefon

    def clean_yedek_telefon(self):
        yedek = self._normalize_phone(self.cleaned_data.get('yedek_telefon'))
        if yedek and len(yedek) != 10:
            raise forms.ValidationError("Yedek telefon 10 haneli olmalıdır.")
        if yedek and not yedek.startswith('5'):
            raise forms.ValidationError("Yedek telefon 5 ile başlamalıdır.")
        return yedek