# etiket/urls.py
from django.urls import path
from . import views

app_name = "etiket"

urlpatterns = [
    path("lookup/", views.serial_number_lookup_view, name="lookup"),  # Türkçe içerikli arama formu
    path("serial/<str:serial_number>/", views.qr_by_serial_view, name="qr_by_serial"),  # Künye numarası ile yönlendirme
    path("<uuid:tag_id>/", views.qr_landing_view, name="qr_landing"),  # Ana QR açılış sayfası
    path("<uuid:tag_id>/download/", views.qr_download_view, name="qr_download"),  # QR kod indir
    path("<uuid:tag_id>/location/", views.qr_notify_location, name="qr_notify_location"),  # Konum bildirimi
    path("tarama/<int:tarama_id>/detay/", views.tarama_detay, name="tarama_detay"),  # Tarama detay sayfası
    path("location-test/", views.location_test_view, name="location_test"),  # Konum test sayfası
    
    # Künye yenileme URL'leri
    path("yenileme/", views.etiket_yenileme_listesi, name="etiket_yenileme_listesi"),
    path("yenileme/baslat/<int:etiket_id>/", views.etiket_yenileme_baslat, name="etiket_yenileme_baslat"),
    path("yenileme/basarili/<int:yenileme_id>/", views.etiket_yenileme_basarili, name="etiket_yenileme_basarili"),
    path("yenileme/iptal/<int:yenileme_id>/", views.etiket_yenileme_iptal, name="etiket_yenileme_iptal"),
    path("yenileme/detay/<int:yenileme_id>/", views.etiket_yenileme_detay, name="etiket_yenileme_detay"),
]
