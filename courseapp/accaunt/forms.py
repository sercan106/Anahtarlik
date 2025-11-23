# accaunt/forms.py (Register için özel, import hataları düzeltildi, fields kısıtlandı)

from django import forms
from django.contrib.auth.models import User
from anahtarlik.models import EvcilHayvan, Sahip
from django.utils import timezone
from .models import MisafirProfil

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

    class Meta:
        model = EvcilHayvan
        fields = ['ad', 'tur', 'irk', 'cinsiyet', 'dogum_tarihi']
        widgets = {
            'ad': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_dogum_tarihi(self):
        from datetime import date
        dogum_tarihi = self.cleaned_data.get('dogum_tarihi')
        if dogum_tarihi:
            # Bugünün tarihini al (timezone-aware olmadan)
            bugun = date.today()
            if dogum_tarihi > bugun:
                raise forms.ValidationError("Doğum tarihi gelecekte olamaz.")
        return dogum_tarihi

class KullaniciForm(forms.Form):
    ad = forms.CharField(
        max_length=50,
        label="Ad",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    soyad = forms.CharField(
        max_length=50,
        label="Soyad",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    username = forms.CharField(
        max_length=150,
        label="Kullanıcı Adı",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label="E-posta",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    telefon = forms.CharField(
        max_length=15,
        label="Telefon",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    yedek_telefon = forms.CharField(
        max_length=15,
        label="Yedek Telefon",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )
    adres = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control form-textarea'})
    )
    sifre = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Şifre"
    )
    sifre_tekrar = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Şifre (Tekrar)"
    )

    def clean(self):
        cleaned_data = super().clean()
        sifre = cleaned_data.get("sifre")
        sifre_tekrar = cleaned_data.get("sifre_tekrar")
        if sifre and sifre_tekrar and sifre != sifre_tekrar:
            raise forms.ValidationError("Şifreler eşleşmiyor.")
        return cleaned_data

    def clean_telefon(self):
        from veteriner.models import Veteriner
        from petshop.models import PetShop
        
        telefon = self.cleaned_data.get('telefon')
        if not telefon:
            return telefon
        
        # Telefon numarasını temizle
        telefon = ''.join(filter(str.isdigit, telefon))
        if telefon.startswith('0'):
            telefon = telefon[1:]
        
        # Tüm profil tiplerinde kontrol et
        if Sahip.objects.filter(telefon=telefon).exists():
            raise forms.ValidationError("Bu telefon numarası zaten kayıtlı (Sahip).")
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
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Bu e-posta adresi zaten kayıtlı.")
        return email

class MisafirProfilForm(forms.ModelForm):
    """Misafir profil güncelleme formu"""
    class Meta:
        model = MisafirProfil
        fields = ['ad_soyad', 'telefon']
        widgets = {
            'ad_soyad': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'telefon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '5XXXXXXXXX'}),
        }
    
    def clean_telefon(self):
        telefon = self.cleaned_data.get('telefon', '').strip()
        if not telefon.isdigit():
            raise forms.ValidationError("Telefon sadece rakamlardan oluşmalıdır.")
        if telefon.startswith("0"):
            telefon = telefon[1:]  # Başındaki 0'ı kaldır
        
        # Aynı telefon numarası başka bir misafirde var mı kontrol et
        if MisafirProfil.objects.filter(telefon=telefon).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Bu telefon numarası zaten kayıtlı.")
        
        return telefon


class MisafirKayitForm(forms.Form):
    ad_soyad = forms.CharField(
        label="Ad Soyad",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ad Soyad"})
    )
    email = forms.EmailField(
        label="E-posta Adresi",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "E-posta"})
    )
    username = forms.CharField(
        label="Kullanıcı Adı",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Kullanıcı Adı"})
    )
    telefon = forms.CharField(
        label="Cep Telefonu",
        max_length=15,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Cep Telefonu"})
    )
    sifre = forms.CharField(
        label="Parola",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Parola"})
    )
    sifre_tekrar = forms.CharField(
        label="Parola (Tekrar)",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Parolayı tekrar girin"})
    )
    dogrulama_kodu = forms.CharField(
        label="Dogrulama Kodu",
        max_length=6,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Dogrulama Kodu"})
    )
    uyelik_sozlesmesi = forms.BooleanField(
        label="Uyelik Sozlesmesini okudum, onayliyorum.",
        required=True
    )

    def __init__(self, *args, verification_code=None, **kwargs):
        self.verification_code = verification_code
        super().__init__(*args, **kwargs)

    def clean_ad_soyad(self):
        ad_soyad = self.cleaned_data["ad_soyad"].strip()
        if len(ad_soyad.split()) < 2:
            raise forms.ValidationError("Lütfen adınızı ve soyadınızı giriniz.")
        if len(ad_soyad) < 3:
            raise forms.ValidationError("Ad Soyad alanı en az 3 karakter olmalıdır.")
        return ad_soyad

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
            raise forms.ValidationError("Bu e-posta ile zaten bir kullanici bulunuyor.")
        return email

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if " " in username:
            raise forms.ValidationError("Kullanıcı adı boşluk içeremez.")
        if len(username) < 3:
            raise forms.ValidationError("Kullanıcı adı en az 3 karakter olmalıdır.")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Bu kullanıcı adı zaten kullanılıyor.")
        return username

    def clean_telefon(self):
        from veteriner.models import Veteriner
        from petshop.models import PetShop
        
        telefon = self.cleaned_data["telefon"].strip()
        if not telefon.isdigit():
            raise forms.ValidationError("Telefon sadece rakamlardan olusmalidir.")
        if len(telefon) == 11 and telefon.startswith("0"):
            telefon = telefon[1:]
        if len(telefon) != 10:
            raise forms.ValidationError("Telefon numarası 10 haneli olmalıdır.")
        if not telefon.startswith("5"):
            raise forms.ValidationError("Telefon numarası 5 ile başlamalıdır.")
        
        # Tüm profil tiplerinde benzersizlik kontrolü
        if Sahip.objects.filter(telefon=telefon).exists():
            raise forms.ValidationError("Bu telefon numarasi zaten kayitli (Sahip).")
        if Veteriner.objects.filter(telefon=telefon).exists():
            raise forms.ValidationError("Bu telefon numarasi zaten kayitli (Veteriner).")
        if PetShop.objects.filter(telefon=telefon).exists():
            raise forms.ValidationError("Bu telefon numarasi zaten kayitli (PetShop).")
        if MisafirProfil.objects.filter(telefon=telefon).exists():
            raise forms.ValidationError("Bu telefon numarasi zaten kayitli (Misafir).")
        
        return telefon

    def clean_dogrulama_kodu(self):
        kod = self.cleaned_data["dogrulama_kodu"].strip()
        if self.verification_code and kod != self.verification_code:
            raise forms.ValidationError("Dogrulama kodu hatali.")
        return kod

    def clean_sifre(self):
        sifre = self.cleaned_data["sifre"]
        if len(sifre) < 8:
            raise forms.ValidationError("Parola en az 8 karakter olmalıdır.")
        if sifre.isdigit() or sifre.isalpha():
            raise forms.ValidationError("Parola harf ve rakam içermelidir.")
        return sifre

    def clean(self):
        cleaned_data = super().clean()
        sifre = cleaned_data.get("sifre")
        sifre_tekrar = cleaned_data.get("sifre_tekrar")
        if sifre and sifre_tekrar and sifre != sifre_tekrar:
            self.add_error("sifre_tekrar", "Parolalar eşleşmiyor.")
        return cleaned_data
