# petshop/urls.py

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

app_name = "petshop"

urlpatterns = [
    # Ana panel
    path("panel/", views.petshop_paneli, name="petshop_paneli"),
    
    # Profil yönetimi
    path("profilim/", views.petshop_profilim, name="petshop_profilim"),
    path("profil-duzenle/", views.profil_duzenle, name="profil_duzenle"),
    path("profil-tamamla/", views.petshop_profil_tamamla, name="petshop_profil_tamamla"),
    path("hesap-ayarlari/", views.hesap_ayarlari, name="hesap_ayarlari"),


    # Mevcut etiket sistemi
    path("tahsisler/", views.tahsis_listesi, name="tahsis_listesi"),
    path("satislar/", views.satis_listesi, name="satis_listesi"),
    path("siparisler/", views.siparis_listesi, name="siparis_listesi"),
    
    # AJAX endpoints
    path("api/districts/", views.districts_for_city, name="districts_for_city"),
    
    # Web sayfası
    path("web/", views.web_sayfasi_duzenle, name="web_sayfasi_duzenle"),
    path("web/<trslug:slug>/", views.web_sayfasi_gorunum, name="web_sayfasi_gorunum"),
    path("web-id/<int:petshop_id>/", views.web_sayfasi_gorunum_legacy, name="web_sayfasi_gorunum_legacy"),
]
