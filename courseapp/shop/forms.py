from django import forms
from shop.models import Adres
from anahtarlik.dictionaries import Il, Ilce, Mahalle


class AdresForm(forms.ModelForm):
    """Adres oluşturma/düzenleme formu - İl → İlçe → Mahalle cascade"""

    il = forms.ModelChoiceField(
        queryset=Il.objects.all().order_by('ad'),
        empty_label="İl Seçiniz",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_il',
            'required': True
        })
    )

    ilce = forms.ModelChoiceField(
        queryset=Ilce.objects.none(),  # Başlangıçta boş
        empty_label="Önce İl Seçiniz",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_ilce',
            'required': True
        })
    )

    mahalle = forms.ModelChoiceField(
        queryset=Mahalle.objects.none(),  # Başlangıçta boş
        empty_label="Önce İlçe Seçiniz",
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_mahalle'
        })
    )
    
    # Manuel mahalle girişi için ekstra alan (formda, modelde zaten var)
    mahalle_diger = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mahalle listede yoksa manuel giriniz',
            'id': 'id_mahalle_diger'
        })
    )

    class Meta:
        model = Adres
        fields = [
            'baslik', 'adres_tipi', 'ad_soyad', 'telefon',
            'il', 'ilce', 'mahalle', 'mahalle_diger', 'adres_satiri', 'posta_kodu',
            'adres_tarifi', 'varsayilan'
        ]
        widgets = {
            'baslik': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: Ev Adresim'}),
            'adres_tipi': forms.Select(attrs={'class': 'form-select'}),
            'ad_soyad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ad Soyad'}),
            'telefon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0555 555 55 55'}),
            'adres_satiri': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Sokak, Cadde, Bina No, Daire No'
            }),
            'posta_kodu': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '34000'}),
            'adres_tarifi': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Adres tarifi (opsiyonel)'
            }),
            'varsayilan': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Eğer instance varsa (düzenleme modunda)
        if self.instance and self.instance.pk:
            # İl seçiliyse ilçeleri doldur
            if self.instance.il:
                self.fields['ilce'].queryset = Ilce.objects.filter(
                    il=self.instance.il
                ).order_by('ad')

            # İlçe seçiliyse mahalleleri doldur
            if self.instance.ilce:
                self.fields['mahalle'].queryset = Mahalle.objects.filter(
                    ilce=self.instance.ilce
                ).order_by('ad')
        
        # POST datası varsa cascade filtrele
        if 'il' in self.data:
            try:
                il_id = int(self.data.get('il'))
                self.fields['ilce'].queryset = Ilce.objects.filter(
                    il_id=il_id
                ).order_by('ad')
            except (ValueError, TypeError):
                pass

        if 'ilce' in self.data:
            try:
                ilce_id = int(self.data.get('ilce'))
                self.fields['mahalle'].queryset = Mahalle.objects.filter(
                    ilce_id=ilce_id
                ).order_by('ad')
            except (ValueError, TypeError):
                pass
