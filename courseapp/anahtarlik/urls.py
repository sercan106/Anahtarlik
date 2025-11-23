# anahtarlik/urls.py

from django.urls import path, include
from . import views

app_name = 'anahtarlik'

urlpatterns = [
    path('', views.ev, name='ev'),
    
    # QR Künye Sistemi Tanıtım
    path('qr-kunye-sistemi/', views.qr_kunye_nasil_calisir, name='qr_kunye_nasil_calisir'),

    # Kullanıcı Paneli
    path('panel/', views.kullanici_paneli, name='kullanici_paneli'),
    path('evcil-hayvanlarim/', views.evcil_hayvanlarim, name='evcil_hayvanlarim'),
    path('kunyelerim/', views.kunyelerim, name='kunyelerim'),
    path('sahip-profilim/', views.sahip_profilim, name='sahip_profilim'),
    path('panel/add-pet/', views.add_pet, name='add_pet'),
    path('panel/pet/<int:pet_id>/', views.pet_detail, name='pet_detail'),
    path('panel/pet/<int:pet_id>/pdf/', views.hayvan_pdf_indir, name='hayvan_pdf_indir'),
    path('panel/profil-duzenle/', views.profil_duzenle, name='profil_duzenle'),
    path('panel/hesap-ayarlari/', views.hesap_ayarlari, name='hesap_ayarlari'),
    path("panel/found/<int:evcil_hayvan_id>/", views.hayvan_bulundu, name="mark_found"),
  

    # Evcil hayvan işlemleri
    path('panel/kayip-bildir/<int:evcil_hayvan_id>/', views.kayip_bildir, name='kayip_bildir'),

    # Edit pet artık petpanel'de (petpanel/edit/<pet_id>/)
    path('panel/delete-pet/<int:pet_id>/', views.delete_pet, name='delete_pet'),

    # Pro Paket Sistemi
    path('pro-paketler/', views.sahip_pro_paketler, name='sahip_pro_paketler'),
    path('pro-abonelik-al/<int:paket_id>/', views.sahip_pro_abonelik_al, name='sahip_pro_abonelik_al'),
    path('pro-panel/', views.sahip_pro_panel, name='sahip_pro_panel'),

    # API Endpoints
    path('api/ilceler/', views.ilce_api, name='ilce_api'),
    path('ajax/get-ilceler/', views.get_ilceler, name='get_ilceler'),
    path('ajax/get-mahalleler/', views.get_mahalleler, name='get_mahalleler'),

    # Bildirim Sistemi
    path('bildirimler/', views.bildirimler, name='bildirimler'),
    path('bildirim/<int:bildirim_id>/oku/', views.bildirim_oku, name='bildirim_oku'),
    path('tum-bildirimleri-oku/', views.tum_bildirimleri_oku, name='tum_bildirimleri_oku'),

    # Django login/logout
    path('auth/', include('django.contrib.auth.urls')),

    # ============================================================
    # İçerik Yönetim Sistemi (CMS) - Kullanıcı Dostu Arayüz
    # ============================================================
    path('yonetim/icerik/', views.cms_dashboard, name='cms_dashboard'),

    # Hero Slide Yönetimi
    path('yonetim/icerik/slide/yeni/', views.cms_slide_create, name='cms_slide_create'),
    path('yonetim/icerik/slide/<int:slide_id>/duzenle/', views.cms_slide_edit, name='cms_slide_edit'),
    path('yonetim/icerik/slide/<int:slide_id>/sil/', views.cms_slide_delete, name='cms_slide_delete'),
    path('yonetim/icerik/slide/<int:slide_id>/toggle/', views.cms_slide_toggle, name='cms_slide_toggle'),

    # Hizmet Kartı Yönetimi
    path('yonetim/icerik/hizmet/yeni/', views.cms_hizmet_create, name='cms_hizmet_create'),
    path('yonetim/icerik/hizmet/<int:hizmet_id>/duzenle/', views.cms_hizmet_edit, name='cms_hizmet_edit'),
    path('yonetim/icerik/hizmet/<int:hizmet_id>/sil/', views.cms_hizmet_delete, name='cms_hizmet_delete'),
    path('yonetim/icerik/hizmet/<int:hizmet_id>/toggle/', views.cms_hizmet_toggle, name='cms_hizmet_toggle'),

    # Genel Ayarlar
    path('yonetim/icerik/ayarlar/', views.cms_ayarlar, name='cms_ayarlar'),
]
















    # path('deneme', views.deneme),
    # path('ev', views.ev), 
    # path('hakkımızda', views.hakkımızda),  
    # path('yayıncılık', views.yayıncılık),  
    # path('program', views.program), 
    # path('program/<slug:slug>/', views.program_detail, name='program_detail'),
    # path('program/<str:kategori>/<slug:slug>/', views.program_etkinlik, name='program_etkinlik'),
    # path('program/<slug:slug>/', views.program_detail, name='program_detail'),
    # path('logo', views.logo), 
    # path('projeler', views.projeler),
    # path('projeler/<slug:slug>/', views.proje, name='proje'),
    # path('projeler/<str:kategori>/<slug:slug>/', views.proje_etkinlik, name='proje_etkinlik'),

    # path('arşiv/<str:kategori>/<str:kategori2>/', views.arşiv_detay, name='arşiv_detay'),
    # path('arşiv', views.arşiv),



    # path('search_results/', views.search_results, name='search_results'),



    # path('hakkında', views.hakkında, name='hakkında'),
    # path('shop', views.shop, name='shop'),
    # path('contact', views.contact, name='contact'),
    # path('urun_ekle', views.urun_ekle, name='urun_ekle'),
    # path('urun_detay/<slug:slug>/<int:id>', views.urun_detay, name='urun_detay'),





# urlpatterns = [
#     path('', views.home),
#     path('borc', views.borc, name='borc'),
#     path('sonuc/<int:id>', views.sonuc, name='sonuc'),
#     path('gıda', views.gıda, name='gıda'),
#     path('aileharcama', views.aileharcama, name='aileharcama'),
#     path('kartlar', views.kartlar, name='kartlar'),
#     path('analiz', views.analiz, name='analiz'),
#     path('silgıdaharcama', views.silgıdaharcama, name='silgıdaharcama'),
    
#     path('silsercanharcama', views.silsercanharcama, name='silsercanharcama'),
#     path('silmehmetharcama', views.silmehmetharcama, name='silmehmetharcama'),
#     path('silerenharcama', views.silerenharcama, name='silerenharcama'),

#     path('sercanharcama', views.sercanharcama, name='sercanharcama'),
#     path('mehmetharcama', views.mehmetharcama, name='mehmetharcama'),
#     path('erenharcama', views.erenharcama, name='erenharcama'),



#     #______________SİL_______________________
#     path('kart_sil/<int:id>', views.kart_sil, name='kart_sil'),
#     path('sil/<int:id>', views.sil, name='sil'),
#     path('gıda_sil/<int:id>', views.gıda_sil, name='gıda_sil'),


#     #_____________________EKLE________________
#     path('ekle', views.ekle, name='ekle'),
#     path('kart_ekle', views.kart_ekle, name='kart_ekle'),
#     path('eklegıda', views.eklegıda, name='eklegıda'),
#     path('gıdaisimekle', views.gıdaisimekle, name='gıdaisimekle')

    




    # path('iletişim', views.kurslar),
    # path('search', views.search, name='search'),#arama sayfası burası
    # path('post', views.post, name='post'),#post
    # path('post2', views.post2, name='post2'),#post etme ve girilen verileri kontrol etme
    # path('ürün_detay', views.ürün_detay, name='ürün_detay'),
    # path('güncelle/<int:idurls>', views.güncelle, name='güncelle'),
    # path('sil/<int:idurls>', views.sil, name='sil'),
    # path('yükle', views.yükle, name='resim_yükle'),
    # path('index', views.index),
    # path('index/<int:kategori>', views.kategori),
    # path('veritabanı', views.veritabanı),
    
    # path('anasayfa', views.anasayfa),
    # path('<int:kategori>',views.dinamik),#burda ketegori değişkenimizi oluşturduk.Eğer str türünde veri
    # #alırsa views.dinamik çalışır
    # #not:yukarıdan aşağıya okuma yaptığı için üstte şartı karşılayan bir path varsa onu görür 
    # #aşağıdakileri görmez.
    # path('<str:kategori>',views.dinamikstr),
# ]
    

