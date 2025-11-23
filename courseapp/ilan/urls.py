# ilan/urls.py

from django.urls import path
from . import views

app_name = 'ilan'

urlpatterns = [
    # Ana sayfa - İlan listesi
    path('', views.ilan_listesi, name='ilan_listesi'),
    
    # İlan detay
    path('<int:ilan_id>/', views.ilan_detay, name='ilan_detay'),
    
    # İlan oluşturma
    path('olustur/', views.ilan_olustur, name='ilan_olustur'),
    path('olustur/<int:hayvan_profili_id>/', views.ilan_olustur_profil, name='ilan_olustur_profil'),
    
    # Hayvan profili yönetimi
    path('profil-olustur/', views.hayvan_profili_olustur, name='hayvan_profili_olustur'),
    path('profil/<int:profil_id>/', views.hayvan_profili_detay, name='hayvan_profili_detay'),
    path('profil/<int:profil_id>/duzenle/', views.hayvan_profili_duzenle, name='hayvan_profili_duzenle'),
    path('profil/<int:profil_id>/sil/', views.hayvan_profili_sil, name='hayvan_profili_sil'),
    
    # Kullanıcı ilanları
    path('ilanlarim/', views.kullanici_ilanlari, name='kullanici_ilanlari'),
    path('ilanlarim/<int:ilan_id>/duzenle/', views.ilan_duzenle, name='ilan_duzenle'),
    path('ilanlarim/<int:ilan_id>/sil/', views.ilan_sil, name='ilan_sil'),
    
    # Kredi yönetimi
    path('kredilerim/', views.kredi_durumu, name='kredi_durumu'),
    path('kredi-satin-al/', views.kredi_satin_al, name='kredi_satin_al'),
    
    # Sahip kullanıcıları için özel sayfalar
    path('sahip-hayvan-secimi/', views.sahip_hayvan_secimi, name='sahip_hayvan_secimi'),
    path('sahip-ilan-olustur/<int:evcil_hayvan_id>/', views.sahip_ilan_olustur, name='sahip_ilan_olustur'),
    path('sahip-ilan-verme-kontrol/', views.sahip_ilan_verme_kontrol, name='sahip_ilan_verme_kontrol'),
    
    # Kullanıcı ilanları
    path('kullanici-ilanlari/', views.kullanici_ilanlari, name='kullanici_ilanlari'),
    
    # AJAX endpoints
    path('api/ilceler/', views.ilce_listesi, name='ilce_listesi'),
    path('api/mahalleler/', views.mahalle_listesi, name='mahalle_listesi'),
    path('api/irkler/', views.irk_listesi, name='irk_listesi'),
    path('api/kredi-kontrol/', views.kredi_kontrol, name='kredi_kontrol'),
    
    # Webhook
    path('webhook/kredi-odeme/', views.kredi_odeme_webhook, name='kredi_odeme_webhook'),
]
