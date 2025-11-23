from django.urls import path
from . import views

app_name = 'petpanel'

urlpatterns = [
    # Ana panel sayfası
    path('', views.panel, name='panel'),
    # Pet düzenleme
    path('edit/<int:pet_id>/', views.edit_pet, name='pet_edit'),
    path('edit-notes/<int:pet_id>/', views.notlari_duzenle, name='notlari_duzenle'),
    path('edit-owner/<int:pet_id>/', views.sahip_bilgilerini_duzenle, name='sahip_bilgilerini_duzenle'),

    # Alerji
    path('add-allergy/<int:pet_id>/', views.alerji_ekle, name='alerji_ekle'),
    path('edit-allergy/<int:record_id>/', views.alerji_duzenle, name='alerji_duzenle'),
    path('delete-allergy/<int:record_id>/', views.alerji_sil, name='alerji_sil'),

    # Sağlık Kaydı
    path('add-health/<int:pet_id>/', views.saglik_ekle, name='saglik_ekle'),
    path('edit-health/<int:record_id>/', views.saglik_duzenle, name='saglik_duzenle'),
    path('delete-health/<int:record_id>/', views.saglik_sil, name='saglik_sil'),

    # İlaç Kaydı
    path('add-medication/<int:pet_id>/', views.ilac_ekle, name='ilac_ekle'),
    path('edit-medication/<int:record_id>/', views.ilac_duzenle, name='ilac_duzenle'),
    path('delete-medication/<int:record_id>/', views.ilac_sil, name='ilac_sil'),

    # Ameliyat Kaydı
    path('add-surgery/<int:pet_id>/', views.ameliyat_ekle, name='ameliyat_ekle'),
    path('edit-surgery/<int:record_id>/', views.ameliyat_duzenle, name='ameliyat_duzenle'),
    path('delete-surgery/<int:record_id>/', views.ameliyat_sil, name='ameliyat_sil'),

    # Beslenme Kaydı
    path('add-nutrition/<int:pet_id>/', views.beslenme_ekle, name='beslenme_ekle'),
    path('edit-nutrition/<int:record_id>/', views.beslenme_duzenle, name='beslenme_duzenle'),
    path('delete-nutrition/<int:record_id>/', views.beslenme_sil, name='beslenme_sil'),
]
