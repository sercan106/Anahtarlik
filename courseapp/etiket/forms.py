# etiket/forms.py
from django import forms
from .models import EtiketYenilemeFiyati

class SeriNumaraForm(forms.Form):
    seri_numarasi = forms.CharField(label="Etiket (Künye) Numarası", max_length=100)


class EtiketYenilemeForm(forms.Form):
    """Künye yenileme formu - Kategori fark etmeksizin genel fiyatlar"""
    
    fiyat_id = forms.ModelChoiceField(
        queryset=EtiketYenilemeFiyati.objects.filter(
            aktif=True,
            etiket_kategori__isnull=True  # Sadece genel fiyatlar
        ),
        widget=forms.RadioSelect,
        label="Yenileme Seçeneği",
        empty_label=None
    )
