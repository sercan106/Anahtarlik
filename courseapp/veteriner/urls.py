# veteriner/urls.py

from django.urls import path, register_converter
from . import views

# Temiz slug converter (sadece İngilizce karakterler)
class CleanSlugConverter:
    regex = r'[-a-zA-Z0-9_]+'
    
    def to_python(self, value):
        return value
    
    def to_url(self, value):
        return value

register_converter(CleanSlugConverter, 'trslug')

app_name = "veteriner"

urlpatterns = [
    # Ana panel
    path("panel/", views.veteriner_paneli, name="veteriner_paneli"),
    
    # Profil yönetimi
    path("profilim/", views.veteriner_profilim, name="veteriner_profilim"),
    path("profil-duzenle/", views.profil_duzenle, name="profil_duzenle"),
    path("profil-tamamla/", views.veteriner_profil_tamamla, name="veteriner_profil_tamamla"),
    path("hesap-ayarlari/", views.hesap_ayarlari, name="hesap_ayarlari"),



    # Randevu yönetimi
    path("randevular/", views.randevu_yonetimi, name="randevu_yonetimi"),
    path("randevular/<int:randevu_id>/", views.randevu_detay, name="randevu_detay"),
    path("randevular/<int:randevu_id>/durum/", views.randevu_durum_guncelle, name="randevu_durum_guncelle"),

    # Değerlendirme yönetimi
    path("degerlendirmeler/", views.degerlendirme_listesi, name="degerlendirme_listesi"),
    path("degerlendirmeler/ekle/", views.degerlendirme_ekle, name="degerlendirme_ekle"),

    # Mevcut etiket sistemi
    path("tahsisler/", views.tahsis_listesi, name="tahsis_listesi"),
    path("satislar/", views.satis_listesi, name="satis_listesi"),
    path("siparisler/", views.siparis_listesi, name="siparis_listesi"),
    
    # AJAX endpoints
    path("api/districts/", views.districts_for_city, name="districts_for_city"),
    
    # Mini web
    path("web/", views.web_sayfasi_duzenle, name="web_sayfasi_duzenle"),
    path("web/<trslug:slug>/", views.web_sayfasi_gorunum, name="web_sayfasi_gorunum"),
    path("web/<trslug:slug>/randevu/", views.public_randevu_olustur, name="public_randevu_olustur"),
    path("web-id/<int:veteriner_id>/", views.web_sayfasi_gorunum_legacy, name="web_sayfasi_gorunum_legacy"),
]









