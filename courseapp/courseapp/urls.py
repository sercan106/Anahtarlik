# courseapp/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Global API endpoints (admin paneli için)
    path('api/districts/', core_views.districts_for_province, name='districts_for_province'),
    
    # Ana uygulamalar
    path('', include(('anahtarlik.urls', 'anahtarlik'), namespace='anahtarlik')),
    path('accaunt/', include('accaunt.urls')),
    path('shop/', include(('shop.urls', 'shop'), namespace='shop')),
    path('tag/', include('etiket.urls', namespace='etiket')),  # co Etiket app'ini dahil ettik
    path('petpanel/', include(('petpanel.urls', 'petpanel'), namespace='petpanel')),  # ekli olmali 

    path("veteriner/", include(("veteriner.urls", "veteriner"), namespace="veteriner")),
    path("petshop/", include(("petshop.urls", "petshop"), namespace="petshop")),
    path("ilanlar/", include(("ilan.urls", "ilan"), namespace="ilan")),
]

# Medya ve statik dosyalar
# PythonAnywhere'de production'da (DEBUG=False) static ve media dosyaları
# Web server tarafından serve edilir, Django'dan serve edilmemeli
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
