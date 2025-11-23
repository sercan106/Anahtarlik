# shop/urls.py
from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    # Ana mağaza sayfası
    path('', views.shop_home, name='shop_home'),

    # Mağaza kategorileri
    path('petshop/', views.petshop_list, name='petshop_list'),
    path('etiket/', views.etiket_list, name='etiket_list'),

    # Ürün detay
    path('urun/<int:urun_id>/', views.urun_detay, name='urun_detay'),
    
    # Sepet işlemleri
    path('sepet/', views.sepet_goster, name='sepet_goster'),
    path('sepet-ekle/<int:urun_id>/', views.sepet_ekle, name='sepet_ekle'),
    path('sepet-kalemi-sil/<int:kalem_id>/', views.sepet_kalemi_sil, name='sepet_kalemi_sil'),
    path('sepet-guncelle/<int:kalem_id>/', views.sepet_guncelle, name='sepet_guncelle'),
    
    # Ödeme ve sipariş
    path('checkout/', views.checkout, name='checkout'),
    path('siparis-olustur/', views.siparis_olustur, name='siparis_olustur'),
    path('siparislerim/', views.siparis_listesi, name='siparis_listesi'),
    path('siparis/<int:siparis_id>/', views.siparis_detay, name='siparis_detay'),
    path('kargo-takip/<int:siparis_id>/', views.kargo_takip, name='kargo_takip'),
    
    # Adres yönetimi
    path('adresler/', views.adres_yonet, name='adres_yonet'),
    path('adres-ekle/', views.adres_ekle, name='adres_ekle'),
    path('adres-sil/<int:adres_id>/', views.adres_sil, name='adres_sil'),

    # AJAX endpoints
    path('ajax/get-ilceler/', views.get_ilceler, name='get_ilceler'),
    path('ajax/get-mahalleler/', views.get_mahalleler, name='get_mahalleler'),
    path('ajax/calculate-cargo/', views.calculate_cargo_ajax, name='calculate_cargo_ajax'),
    
    # Admin endpoints
    path('admin/siparis-yonet/', views.admin_siparis_yonet, name='admin_siparis_yonet'),
    path('admin/siparis/<int:siparis_id>/', views.admin_siparis_detay, name='admin_siparis_detay'),
    path('admin/kargo-yonet/', views.admin_kargo_yonet, name='admin_kargo_yonet'),
]