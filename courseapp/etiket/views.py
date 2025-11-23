# etiket/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from .models import Etiket, EtiketTarama, EtiketYenileme, EtiketYenilemeFiyati
from anahtarlik.models import Bildirim
from django.contrib.auth.decorators import login_required
from .forms import SeriNumaraForm, EtiketYenilemeForm
from courseapp.constants import GPS_ACCURACY_IDEAL, GPS_ACCURACY_ACCEPTABLE, GPS_ACCURACY_POOR
from django.db import transaction
from django.core.cache import cache
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import qrcode
import io
import logging
import requests
import stripe
import math
import re

logger = logging.getLogger(__name__)


# Tarama Detay View (Normal Kullanıcılar İçin)
@login_required
def tarama_detay(request, tarama_id):
    """Normal kullanıcılar için tarama detay sayfası"""
    try:
        tarama = EtiketTarama.objects.get(id=tarama_id)
    except EtiketTarama.DoesNotExist:
        messages.error(request, 'Bu tarama detayı bulunamadı veya silinmiş olabilir.')
        return redirect('anahtarlik:bildirimler')
    
    # Sadece hayvan sahibi bu detayı görebilir
    if not hasattr(request.user, 'sahip') or tarama.etiket.evcil_hayvan.sahip.kullanici != request.user:
        messages.error(request, 'Bu tarama detayını görme yetkiniz yok.')
        return redirect('anahtarlik:bildirimler')
    
    # GPS koordinatlarını nokta formatında hazırla
    gps_lat_str = None
    gps_lng_str = None
    if tarama.gps_latitude and tarama.gps_longitude:
        gps_lat_str = f"{tarama.gps_latitude:.6f}".replace(',', '.')
        gps_lng_str = f"{tarama.gps_longitude:.6f}".replace(',', '.')
    
    context = {
        'tarama': tarama,
        'hayvan': tarama.etiket.evcil_hayvan,
        'etiket': tarama.etiket,
        'gps_lat_str': gps_lat_str,
        'gps_lng_str': gps_lng_str,
    }
    return render(request, 'etiket/tarama_detay.html', context)


# Yardımcı Fonksiyonlar
def create_notification(sahip, baslik, mesaj, tur='GENEL', tarama=None, url=None):
    """Sahip için bildirim oluştur"""
    try:
        bildirim = Bildirim.objects.create(
            sahip=sahip,
            baslik=baslik,
            mesaj=mesaj,
            tur=tur,
            tarama=tarama,
            url=url,
            okundu=False
        )
        logger.info(f"✅ Bildirim oluşturuldu: {sahip.kullanici.username} - {baslik}")
        return bildirim
    except Exception as e:
        logger.error(f"❌ Bildirim oluşturma hatası: {e}")
        return None


def calculate_distance(lat1, lon1, lat2, lon2):
    """İki GPS koordinatı arası mesafeyi hesapla (Haversine formula - metre cinsinden)"""
    R = 6371000  # Dünya yarıçapı (metre)
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2) * math.sin(delta_lat/2) + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * \
        math.sin(delta_lon/2) * math.sin(delta_lon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def check_location_anomalies(tarama):
    """GPS/IP uyumsuzluğu ve anomali tespiti"""
    anomalies = []
    
    # GPS ve IP lokasyon karşılaştırması
    if tarama.gps_latitude and tarama.gps_longitude and tarama.ip_sehir:
        # IP lokasyonundan koordinat tahmin (basit)
        # Bu gerçek uygulamada geocoding API ile yapılmalı
        # Şimdilik sadece log
        logger.info(f"🔍 GPS/IP karşılaştırma: GPS={tarama.gps_latitude:.6f},{tarama.gps_longitude:.6f} - IP={tarama.ip_sehir}")
        
        # Önceki taramalar ile mesafe kontrolü
        recent_scans = EtiketTarama.objects.filter(
            etiket=tarama.etiket,
            tarama_zamani__lt=tarama.tarama_zamani
        ).order_by('-tarama_zamani')[:3]
        
        if recent_scans.exists():
            for prev_scan in recent_scans:
                if prev_scan.gps_latitude and prev_scan.gps_longitude:
                    distance = calculate_distance(
                        tarama.gps_latitude, tarama.gps_longitude,
                        prev_scan.gps_latitude, prev_scan.gps_longitude
                    )
                    time_diff = (tarama.tarama_zamani - prev_scan.tarama_zamani).total_seconds() / 3600  # saat
                    
                    # 100km'den fazla mesafe ve 1 saatten kısa süre = şüpheli
                    if distance > 100000 and time_diff < 1:
                        anomalies.append({
                            'type': 'DISTANCE_JUMP',
                            'distance_km': distance / 1000,
                            'time_hours': time_diff,
                            'message': f"Son taramadan {distance/1000:.1f}km uzakta (sadece {time_diff:.1f} saat sonra)"
                        })
                        logger.warning(f"⚠️ ŞÜPHELİ KONUM: Son taramadan {distance/1000:.1f}km uzakta")
    
    return anomalies


def get_ip_location(ip):
    """IP adresinden lokasyon bilgisi al - CACHE'Lİ VERSİYON"""
    from django.core.cache import cache
    
    # Cache kontrolü (24 saat)
    cache_key = f'ip_location_{ip}'
    cached_result = cache.get(cache_key)
    
    if cached_result:
        logger.info(f"✅ Cache'den alındı: {ip}")
        return cached_result
    
    # API çağrısı
    try:
        # Localhost IP'si ise gerçek IP'yi al
        if ip in ['127.0.0.1', 'localhost', '::1', '0.0.0.0']:
            logger.info("🔄 Localhost IP tespit edildi, gerçek IP alınıyor...")
            response = requests.get("https://ipinfo.io/json", timeout=5)
            if response.status_code == 200:
                data = response.json()
                sehir = data.get('city', '-')
                bolge = data.get('region', '-')
                ulke = data.get('country', '-')
                real_ip = data.get('ip', ip)
                logger.info(f"🌐 Gerçek IP: {real_ip}, Lokasyon: {sehir}, {bolge}, {ulke}")
                result = (sehir, ulke, f"{sehir}, {bolge}, {ulke}")
        else:
            # Normal IP için lokasyon al
            response = requests.get(f"https://ipinfo.io/{ip}/json", timeout=3)
            if response.status_code == 200:
                data = response.json()
                sehir = data.get('city', '-')
                bolge = data.get('region', '-')
                ulke = data.get('country', '-')
                result = (sehir, ulke, f"{sehir}, {bolge}, {ulke}")
    except Exception as e:
        logger.warning(f"🌐 IP Konum alınamadı: {e}")
        result = ('İstanbul', 'Türkiye', 'İstanbul, İstanbul, Türkiye')
    
    # 24 saat cache'e kaydet
    cache.set(cache_key, result, 86400)
    logger.info(f"💾 Cache'e kaydedildi: {ip}")
    
    return result


def send_scan_notification(etiket, hayvan, sahip, tarama, has_finder_info=False):
    """Tarama bildirimi e-postası gönder"""
    
    zaman = tarama.tarama_zamani.strftime("%d.%m.%Y %H:%M")
    
    # DEBUG: Lokasyon bilgilerini logla
    logger.info(f"🔍 DEBUG - Tarama ID: {tarama.id}")
    logger.info(f"🔍 DEBUG - GPS: {tarama.gps_latitude}, {tarama.gps_longitude}")
    logger.info(f"🔍 DEBUG - IP: {tarama.ip_sehir}, {tarama.ip_ulke}")
    logger.info(f"🔍 DEBUG - IP Adresi: {tarama.ip_adresi}")
    
    # Konum kaynağına göre lokasyon bilgisi - AÇIK VE NET
    from .models import KONUM_KAYNAGI_GPS, KONUM_KAYNAGI_IP, KONUM_KAYNAGI_MANUEL
    
    if tarama.konum_kaynagi == KONUM_KAYNAGI_GPS and tarama.gps_latitude and tarama.gps_longitude:
        # GPS konumu - GERÇEK KONUM
        lokasyon = f"{tarama.gps_latitude:.6f}, {tarama.gps_longitude:.6f}"
        harita_link = f"https://www.google.com/maps?q={tarama.gps_latitude},{tarama.gps_longitude}"
        lokasyon_detay = f"✅ GERÇEK GPS KONUMU (Yüksek Doğruluk)\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📍 Koordinatlar: {lokasyon}\n🗺️ Harita: {harita_link}"
        if tarama.gps_dogruluk:
            lokasyon_detay += f"\n📏 Doğruluk: ±{tarama.gps_dogruluk:.0f} metre"
        logger.info(f"✅ GPS lokasyonu kullanılıyor: {lokasyon}")
    elif tarama.konum_kaynagi == KONUM_KAYNAGI_MANUEL and tarama.gps_latitude and tarama.gps_longitude:
        # Manuel konum - KULLANICI GİRDİ
        lokasyon = f"{tarama.gps_latitude:.6f}, {tarama.gps_longitude:.6f}"
        harita_link = f"https://www.google.com/maps?q={tarama.gps_latitude},{tarama.gps_longitude}"
        lokasyon_detay = f"✏️ MANUEL KONUM (Kullanıcı Girdi)\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📍 Koordinatlar: {lokasyon}\n🗺️ Harita: {harita_link}\nℹ️ Bu konum bulan kişi tarafından manuel olarak girildi."
        if tarama.gps_dogruluk:
            lokasyon_detay += f"\n📏 Doğruluk: ±{tarama.gps_dogruluk:.0f} metre"
        logger.info(f"✏️ Manuel lokasyon kullanılıyor: {lokasyon}")
    elif tarama.konum_kaynagi == KONUM_KAYNAGI_IP or (not tarama.gps_latitude and tarama.ip_sehir):
        # IP lokasyon bilgisi - TAHMİNİ KONUM (YANLIŞ OLABİLİR)
        lokasyon = f"{tarama.ip_sehir}, {tarama.ip_ulke}"
        lokasyon_detay = f"⚠️ TAHMİNİ KONUM (IP Tabanlı - YANLIŞ OLABİLİR!)\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📍 Tahmini Lokasyon: {lokasyon}\n🌐 IP Adresi: {tarama.ip_adresi}"
        if tarama.ip_lokasyon_text:
            lokasyon_detay += f"\n📋 Detay: {tarama.ip_lokasyon_text}"
        lokasyon_detay += f"\n\n⚠️ ÖNEMLİ UYARI:\n• Bu konum IP adresine göre tahmin edilmiştir.\n• PC'lerde GPS olmadığı için konum çok yanlış olabilir.\n• Gerçek GPS konumu bekleniyor veya bulan kişi manuel konum girebilir.\n• Bu konuma güvenmeyin, bulan kişi ile iletişime geçin!"
        logger.warning(f"⚠️ IP lokasyonu kullanılıyor (TAHMİNİ): {lokasyon}")
    else:
        lokasyon = "Konum alınamadı"
        lokasyon_detay = f"❌ KONUM BİLGİSİ YOK\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📍 Lokasyon: {lokasyon}\n🌐 IP Adresi: {tarama.ip_adresi or 'Bilinmiyor'}"
        logger.warning(f"❌ Hiçbir lokasyon bilgisi yok!")
    
    # Hayvan durumu
    hayvan_durum = "🚨 KAYIP!" if hayvan.kayip_durumu else "Normal"
    bildirim_tarihi = hayvan.kayip_bildirim_tarihi.strftime('%d.%m.%Y %H:%M') if hayvan.kayip_bildirim_tarihi else "-"
    odul = f"₺{hayvan.odul_miktari}" if hayvan.odul_miktari else "-"
    
    if has_finder_info and tarama.has_bulan_bilgisi():
        # Detaylı e-posta (bulan kişi bilgileri ile)
        telefon_temiz = tarama.bulan_telefon.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # Konum kaynağına göre konu başlığı
        if tarama.konum_kaynagi == KONUM_KAYNAGI_GPS:
            subject = f"🐾 MÜJDELİ HABER! {hayvan.ad} BULUNDU! 📍 GERÇEK GPS KONUMU"
        elif tarama.konum_kaynagi == KONUM_KAYNAGI_MANUEL:
            subject = f"🐾 MÜJDELİ HABER! {hayvan.ad} BULUNDU! ✏️ MANUEL KONUM"
        else:
            subject = f"🐾 MÜJDELİ HABER! {hayvan.ad} BULUNDU! ⚠️ TAHMİNİ KONUM (IP)"
        message = f"""
Merhaba {sahip.ad},

🎉 HARIKA HABER! {hayvan.ad} adlı evcil hayvanınız bulundu!

📞 BULAN KİŞİ BİLGİLERİ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 İsim: {tarama.bulan_isim}
📱 Telefon: {tarama.bulan_telefon}
📧 E-posta: {tarama.bulan_email or '-'}

💬 Mesajı:
"{tarama.bulan_mesaj}"

📍 KONUM BİLGİSİ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{lokasyon_detay}

⏰ ZAMAN BİLGİSİ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Tarama Zamanı: {zaman}

🐾 HAYVAN BİLGİSİ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🐕 Adı: {hayvan.ad}
🦴 Tür: {hayvan.tur.ad}
⚠️ Durum: {hayvan_durum}
💰 Ödül: {odul}

📲 HEMEN İLETİŞİME GEÇİN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Telefon: {tarama.bulan_telefon}
• WhatsApp: https://wa.me/{telefon_temiz}?text=Merhaba%2C%20{hayvan.ad}%20adl%C4%B1%20hayvan%C4%B1n%C4%B1z%C4%B1%20buldum.%20Konum%3A%20{lokasyon}

Lütfen mümkün olan en kısa sürede bulan kişi ile iletişime geçin!

💚 PetSafe Hub Ekibi
""".strip()
    else:
        # Basit e-posta (sadece tarama) - Konum kaynağına göre
        if tarama.konum_kaynagi == KONUM_KAYNAGI_GPS:
            subject = f"📍 {hayvan.ad} adlı hayvanınıza ait QR etiket tarandı - ✅ GERÇEK GPS KONUMU"
        elif tarama.konum_kaynagi == KONUM_KAYNAGI_MANUEL:
            subject = f"📍 {hayvan.ad} adlı hayvanınıza ait QR etiket tarandı - ✏️ MANUEL KONUM"
        else:
            subject = f"📍 {hayvan.ad} adlı hayvanınıza ait QR etiket tarandı - ⚠️ TAHMİNİ KONUM (IP)"
        message = f"""
Merhaba {sahip.ad},

{hayvan.ad} adlı evcil hayvanınıza ait QR etiketi az önce tarandı.

📍 KONUM BİLGİSİ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{lokasyon_detay}

⏰ ZAMAN BİLGİSİ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Tarama Zamanı: {zaman}

🐾 HAYVAN BİLGİSİ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🐕 Adı: {hayvan.ad}
🦴 Tür: {hayvan.tur.ad}
⚠️ Durum: {hayvan_durum}

ℹ️ Bulan kişi henüz bilgilerini paylaşmadı.

💚 PetSafe Hub Ekibi
""".strip()
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [sahip.kullanici.email],
            fail_silently=False,
        )
        tarama.email_gonderildi = True
        tarama.email_gonderim_zamani = timezone.now()
        tarama.save()
        logger.info(f"✅ E-Posta gönderildi: {sahip.kullanici.email}")
    except Exception as e:
        logger.error(f"❌ E-Posta gönderim hatası: {e}")


# 1. QR KOD TARAMA - LANDING SAYFASI
def qr_landing_view(request, tag_id):
    etiket = get_object_or_404(Etiket, etiket_id=tag_id)
    hayvan = etiket.evcil_hayvan
    
    # Etiket henüz bir evcil hayvana bağlanmamışsa
    if not hayvan:
        logger.warning(f"⚠️ Etiket {tag_id} henüz bir evcil hayvana bağlanmamış")
        return render(request, 'etiket/etiket_baglanmamis.html', {
            'etiket': etiket,
            'tag_id': tag_id
        })
    
    sahip = hayvan.sahip

    logger.info("[qr_landing_view] view'e giris yapildi.")
    logger.info(f"Hayvan: {hayvan.ad}")
    logger.info(f"Sahip: {sahip.ad} {sahip.soyad}")
    logger.info(f"Sahip e-posta: {sahip.kullanici.email}")

    # ETİKET AKTİF Mİ KONTROL ET - TİCARİ STRATEJİ
    if not etiket.aktif:
        logger.warning(f"⚠️ Etiket {tag_id} pasif - hizmet verilmiyor")
        return render(request, 'etiket/etiket_pasif.html', {
            'etiket': etiket,
            'hayvan': hayvan,
            'sahip': sahip,
            'tag_id': tag_id
        })
    
    # ETİKET SÜRESİ DOLMUŞ MU KONTROL ET
    if etiket.son_kullanma_tarihi and etiket.son_kullanma_tarihi < timezone.now():
        logger.warning(f"⚠️ Etiket {tag_id} süresi dolmuş - hizmet verilmiyor")
        return render(request, 'etiket/etiket_suresi_dolmus.html', {
            'etiket': etiket,
            'hayvan': hayvan,
            'sahip': sahip,
            'tag_id': tag_id
        })

    # GET İşlemi - SAYFA İLK AÇILDIĞINDA OTOMATİK BİLDİRİM
    if request.method == 'GET':
        # IP bilgilerini al
        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', 'Bilinmiyor')).split(',')[0].strip()
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        tarayici_dili = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        
        # RATE LIMITING: Aynı IP'den çok kısa sürede tekrar tarama kontrolü
        rate_limit_key = f'qr_scan_rate_limit_{etiket.id}_{ip}'
        last_scan_time = cache.get(rate_limit_key)
        
        if last_scan_time:
            time_diff = (timezone.now() - last_scan_time).total_seconds()
            if time_diff < 30:  # 30 saniye içinde tekrar tarama yapılamaz
                logger.warning(f"⚠️ Rate limit: Aynı IP'den çok kısa sürede tekrar tarama denemesi ({ip})")
                # Mevcut tarama kaydını bul (son 1 dakika içinde)
                recent_tarama = EtiketTarama.objects.filter(
                    etiket=etiket,
                    ip_adresi=ip,
                    tarama_zamani__gte=timezone.now() - timedelta(minutes=1)
                ).order_by('-tarama_zamani').first()
                
                if recent_tarama:
                    return render(request, 'etiket/qr_landing.html', {
                        'etiket': etiket,
                        'hayvan': hayvan,
                        'tarama_id': recent_tarama.id,
                    })
        
        # Rate limit cache'ini güncelle
        cache.set(rate_limit_key, timezone.now(), 60)  # 60 saniye cache
        
        # IP lokasyon (cache'li)
        ip_sehir, ip_ulke, ip_lokasyon = get_ip_location(ip)
        
        # Transaction içinde tarama kaydı oluştur
        try:
            with transaction.atomic():
                # Otomatik tarama kaydı oluştur (GPS yok - IP konumu)
                from .models import KONUM_KAYNAGI_IP
                tarama = EtiketTarama.objects.create(
                    etiket=etiket,
                    konum_kaynagi=KONUM_KAYNAGI_IP,  # IP konumu - tahmini
                    ip_adresi=ip,
                    ip_sehir=ip_sehir,
                    ip_ulke=ip_ulke,
                    ip_lokasyon_text=ip_lokasyon,
                    user_agent=user_agent,
                    tarayici_dili=tarayici_dili,
                )
                
                # Hemen e-posta bildirimi gönder (GPS olmadan)
                try:
                    send_scan_notification(etiket, hayvan, sahip, tarama, has_finder_info=False)
                    logger.info(f"✅ Otomatik bildirim gönderildi: {sahip.kullanici.email}")
                except Exception as e:
                    logger.error(f"❌ E-posta gönderim hatası (tarama kaydı oluşturuldu): {e}")
                    # E-posta gönderilemese bile tarama kaydı oluşturuldu
                
                # Sahip için bildirim oluştur (IP konumu - tahmini olduğunu belirt)
                bildirim_url = f"/tag/tarama/{tarama.id}/detay/"
                create_notification(
                    sahip=sahip,
                    baslik=f"🔍 {hayvan.ad} adlı hayvanınızın QR kodu tarandı!",
                    mesaj=f"{hayvan.ad} adlı hayvanınızın QR kodu tarandı.\n\n⚠️ TAHMİNİ KONUM: {ip_sehir}, {ip_ulke}\n(IP tabanlı tahmin - PC'lerde GPS olmadığı için yanlış olabilir. Gerçek GPS konumu bekleniyor...)",
                    tur='QR_TARAMA',
                    tarama=tarama,
                    url=bildirim_url
                )
        except Exception as e:
            logger.error(f"❌ Tarama kaydı oluşturma hatası: {e}")
            # Hata durumunda bile sayfayı göster (tarama_id olmadan)
            return render(request, 'etiket/qr_landing.html', {
                'etiket': etiket,
                'hayvan': hayvan,
            })
        
        # Template'e tarama ID'si gönder (GPS paylaşımı için)
        return render(request, 'etiket/qr_landing.html', {
            'etiket': etiket,
            'hayvan': hayvan,
            'tarama_id': tarama.id,
        })

    # POST İşlemleri
    elif request.method == 'POST':
        action = request.POST.get('action')
        
        # 1. Otomatik bildirim (QR tarandığında)
        if action == 'auto_notify':
            bulan_isim = request.POST.get('bulan_isim', 'QR Tarayıcı')
            bulan_telefon = request.POST.get('bulan_telefon', 'Belirtilmedi')
            bulan_email = request.POST.get('bulan_email', '')
            bulan_mesaj = request.POST.get('bulan_mesaj', 'QR etiket tarandı. Sahip bilgilendirildi.')
            
            # IP bilgilerini al
            ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', 'Bilinmiyor')).split(',')[0].strip()
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            tarayici_dili = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
            
            # IP lokasyon bilgisi
            ip_sehir, ip_ulke, ip_lokasyon = get_ip_location(ip)
            
            # Tarama kaydı oluştur (otomatik bildirim)
            tarama = EtiketTarama.objects.create(
                etiket=etiket,
                ip_adresi=ip,
                ip_sehir=ip_sehir,
                ip_ulke=ip_ulke,
                ip_lokasyon_text=ip_lokasyon,
                user_agent=user_agent,
                tarayici_dili=tarayici_dili,
                bulan_isim=bulan_isim,
                bulan_telefon=bulan_telefon,
                bulan_email=bulan_email,
                bulan_mesaj=bulan_mesaj,
            )
            
            # Otomatik e-posta bildirimi
            send_scan_notification(etiket, hayvan, sahip, tarama, has_finder_info=True)
            
            return JsonResponse({'success': True, 'message': 'Otomatik bildirim gönderildi'})
        
        # 2. Sadece GPS lokasyon kaydet (AJAX)
        elif action == 'save_location':
            gps_lat = request.POST.get('gps_latitude')
            gps_lng = request.POST.get('gps_longitude')
            gps_acc = request.POST.get('gps_accuracy')
            
            # IP bilgilerini al
            ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', 'Bilinmiyor')).split(',')[0].strip()
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            tarayici_dili = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
            
            # IP lokasyon bilgisi
            ip_sehir, ip_ulke, ip_lokasyon = get_ip_location(ip)
            
            # Tarama kaydı oluştur (GPS ile)
            tarama = EtiketTarama.objects.create(
                etiket=etiket,
                gps_latitude=float(gps_lat) if gps_lat else None,
                gps_longitude=float(gps_lng) if gps_lng else None,
                gps_dogruluk=float(gps_acc) if gps_acc else None,
                ip_adresi=ip,
                ip_sehir=ip_sehir,
                ip_ulke=ip_ulke,
                ip_lokasyon_text=ip_lokasyon,
                user_agent=user_agent,
                tarayici_dili=tarayici_dili,
            )
            
            # Basit e-posta bildirimi (sadece tarama)
            send_scan_notification(etiket, hayvan, sahip, tarama, has_finder_info=False)
            
            return JsonResponse({'success': True, 'scan_id': tarama.id})
        
        # 3. Bulan kişi bilgi formu
        elif action == 'bulan_bilgisi':
            bulan_isim = request.POST.get('bulan_isim', '').strip()
            bulan_telefon = request.POST.get('bulan_telefon', '').strip()
            bulan_email = request.POST.get('bulan_email', '').strip()
            bulan_mesaj = request.POST.get('bulan_mesaj', '').strip()
            gps_lat = request.POST.get('gps_latitude', '')
            gps_lng = request.POST.get('gps_longitude', '')
            gps_acc = request.POST.get('gps_accuracy', '')
            tarama_id = request.POST.get('tarama_id', '')
            
            # Form validasyonu
            if not bulan_isim:
                return JsonResponse({'success': False, 'error': 'Adınız gereklidir'}, status=400)
            if not bulan_telefon:
                return JsonResponse({'success': False, 'error': 'Telefon numaranız gereklidir'}, status=400)
            if not bulan_mesaj:
                return JsonResponse({'success': False, 'error': 'Mesajınız gereklidir'}, status=400)
            
            # Telefon format validasyonu
            phone_clean = re.sub(r'\D', '', bulan_telefon)  # Sadece rakamlar
            phone_regex = re.compile(r'^(\+90|0)?[5][0-9]{9}$')
            if not phone_regex.match(phone_clean):
                return JsonResponse({'success': False, 'error': 'Geçersiz telefon formatı. Lütfen 05XX XXX XX XX formatında girin.'}, status=400)
            
            # E-posta validasyonu (opsiyonel)
            if bulan_email:
                try:
                    validate_email(bulan_email)
                except ValidationError:
                    return JsonResponse({'success': False, 'error': 'Geçersiz e-posta formatı'}, status=400)
            
            # GPS koordinat validasyonu (varsa)
            lat = None
            lng = None
            accuracy = None
            
            if gps_lat and gps_lng:
                try:
                    lat = float(gps_lat)
                    lng = float(gps_lng)
                    accuracy = float(gps_acc) if gps_acc else None
                    
                    # Koordinat aralık kontrolü
                    if lat < -90 or lat > 90 or lng < -180 or lng > 180:
                        logger.warning(f"⚠️ Geçersiz GPS koordinat aralığı: lat={lat}, lng={lng}")
                        lat = None
                        lng = None
                        accuracy = None
                    elif accuracy and accuracy >= 10000:
                        logger.warning(f"⚠️ GPS doğruluğu çok düşük (IP konumu): {accuracy}m")
                        lat = None
                        lng = None
                        accuracy = None
                except (ValueError, TypeError):
                    logger.warning(f"⚠️ GPS koordinat parse hatası: lat={gps_lat}, lng={gps_lng}")
                    lat = None
                    lng = None
                    accuracy = None
            
            # DEBUG: Gelen verileri logla
            logger.info(f"🔍 BULAN BİLGİSİ - İsim: {bulan_isim}, Telefon: {bulan_telefon}")
            logger.info(f"🔍 BULAN BİLGİSİ - GPS: {lat}, {lng}, Accuracy: {accuracy}")
            
            # IP bilgilerini al
            ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', 'Bilinmiyor')).split(',')[0].strip()
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            tarayici_dili = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
            
            # IP lokasyon bilgisi
            ip_sehir, ip_ulke, ip_lokasyon = get_ip_location(ip)
            
            # Transaction içinde tarama kaydı oluştur
            try:
                with transaction.atomic():
                    # Eğer tarama_id varsa, mevcut taramayı güncelle (ownership kontrolü ile)
                    if tarama_id:
                        try:
                            existing_tarama = EtiketTarama.objects.select_related('etiket').get(id=tarama_id)
                            # Ownership kontrolü
                            if existing_tarama.etiket_id != etiket.id:
                                logger.warning(f"🚨 GÜVENLİK: tarama_id ownership hatası - tarama.etiket_id={existing_tarama.etiket_id}, etiket.id={etiket.id}")
                                tarama_id = None  # Yeni kayıt oluştur
                            else:
                                # Mevcut taramayı güncelle
                                existing_tarama.bulan_isim = bulan_isim
                                existing_tarama.bulan_telefon = bulan_telefon
                                existing_tarama.bulan_email = bulan_email
                                existing_tarama.bulan_mesaj = bulan_mesaj
                                if lat and lng:
                                    existing_tarama.gps_latitude = round(lat, 8)
                                    existing_tarama.gps_longitude = round(lng, 8)
                                    if accuracy:
                                        existing_tarama.gps_dogruluk = accuracy
                                existing_tarama.save()
                                tarama = existing_tarama
                        except EtiketTarama.DoesNotExist:
                            tarama_id = None  # Yeni kayıt oluştur
                    
                    # Yeni tarama kaydı oluştur (eğer tarama_id yoksa veya geçersizse)
                    if not tarama_id or 'tarama' not in locals():
                        from .models import KONUM_KAYNAGI_GPS, KONUM_KAYNAGI_IP
                        konum_kaynagi = KONUM_KAYNAGI_GPS if (lat and lng) else KONUM_KAYNAGI_IP
                        tarama = EtiketTarama.objects.create(
                            etiket=etiket,
                            konum_kaynagi=konum_kaynagi,
                            gps_latitude=round(lat, 8) if lat and lng else None,
                            gps_longitude=round(lng, 8) if lat and lng else None,
                            gps_dogruluk=accuracy if accuracy else None,
                            ip_adresi=ip,
                            ip_sehir=ip_sehir,
                            ip_ulke=ip_ulke,
                            ip_lokasyon_text=ip_lokasyon,
                            user_agent=user_agent,
                            tarayici_dili=tarayici_dili,
                            bulan_isim=bulan_isim,
                            bulan_telefon=bulan_telefon,
                            bulan_email=bulan_email,
                            bulan_mesaj=bulan_mesaj,
                        )
                    
                    # Gelişmiş e-posta bildirimi (bulan kişi bilgileri ile)
                    try:
                        send_scan_notification(etiket, hayvan, sahip, tarama, has_finder_info=True)
                        logger.info(f"✅ Bulan bilgisi e-postası gönderildi: {sahip.kullanici.email}")
                    except Exception as e:
                        logger.error(f"❌ E-posta gönderim hatası (tarama kaydı oluşturuldu): {e}")
                        # E-posta gönderilemese bile tarama kaydı oluşturuldu
            except Exception as e:
                logger.error(f"❌ Tarama kaydı oluşturma hatası: {e}")
                return JsonResponse({'success': False, 'error': 'Bilgiler kaydedilirken bir hata oluştu. Lütfen tekrar deneyin.'}, status=500)
            
            # Sahip için bulan kişi bildirimi oluştur
            bildirim_url = f"/tag/tarama/{tarama.id}/detay/"
            bulan_info = f"Ad: {bulan_isim}" if bulan_isim else ""
            if bulan_telefon:
                bulan_info += f", Tel: {bulan_telefon}" if bulan_info else f"Tel: {bulan_telefon}"
            if bulan_email:
                bulan_info += f", E-posta: {bulan_email}" if bulan_info else f"E-posta: {bulan_email}"
            
            create_notification(
                sahip=sahip,
                baslik=f"👤 {hayvan.ad} adlı hayvanınızı bulan kişi bilgi verdi!",
                mesaj=f"{hayvan.ad} adlı hayvanınızı bulan kişi detaylı bilgi verdi. {bulan_info}",
                tur='BULAN_BILGI',
                tarama=tarama,
                url=bildirim_url
            )
            
            # AJAX / Fetch isteği ise JSON döndür
            accept_header = request.headers.get('Accept', '')
            accepts_json = any('application/json' in part for part in accept_header.split(','))
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or accepts_json
            if is_ajax:
                return JsonResponse({'success': True, 'message': 'Bilgileriniz başarıyla gönderildi!'})
            
            messages.success(request, '✅ Bilgileriniz başarıyla gönderildi! Hayvan sahibi en kısa sürede sizinle iletişime geçecektir.')
            return redirect('etiket:qr_landing', tag_id=tag_id)
        
        # 4. YENİ: Basit GPS güncelleme (kullanıcı butona tıklarsa)
        elif action == 'update_gps':
            tarama_id = request.POST.get('tarama_id')
            gps_lat = request.POST.get('gps_latitude')
            gps_lng = request.POST.get('gps_longitude')
            gps_acc = request.POST.get('gps_accuracy')
            konum_kaynagi = request.POST.get('konum_kaynagi', 'GPS')  # GPS, IP, MANUEL
            
            # tarama_id validation
            if not tarama_id:
                return JsonResponse({'success': False, 'error': 'Tarama ID gerekli'}, status=400)
            
            # DEBUG: Gelen GPS verilerini logla
            logger.info(f"🔍 GPS UPDATE - Tarama ID: {tarama_id}")
            logger.info(f"🔍 GPS UPDATE - Latitude: {gps_lat}")
            logger.info(f"🔍 GPS UPDATE - Longitude: {gps_lng}")
            logger.info(f"🔍 GPS UPDATE - Accuracy: {gps_acc}")
            
            try:
                # GPS koordinat validasyonu
                try:
                    lat = float(gps_lat) if gps_lat else None
                    lng = float(gps_lng) if gps_lng else None
                    accuracy = float(gps_acc) if gps_acc else 0
                except (ValueError, TypeError):
                    return JsonResponse({'success': False, 'error': 'Geçersiz GPS koordinat formatı'}, status=400)
                
                # Koordinat aralık kontrolü
                if lat is None or lng is None:
                    return JsonResponse({'success': False, 'error': 'GPS koordinatları gerekli'}, status=400)
                
                if lat < -90 or lat > 90:
                    return JsonResponse({'success': False, 'error': 'Geçersiz enlem değeri (-90 ile 90 arası olmalı)'}, status=400)
                
                if lng < -180 or lng > 180:
                    return JsonResponse({'success': False, 'error': 'Geçersiz boylam değeri (-180 ile 180 arası olmalı)'}, status=400)
                
                # Accuracy kontrolü (≥5km = IP konumu, reddet - daha sıkı kontrol)
                if accuracy >= 5000:
                    return JsonResponse({
                        'success': False, 
                        'error': f'GPS doğruluğu çok düşük (±{accuracy/1000:.1f}km). Bu bir IP/Wi-Fi tabanlı tahmini konum olabilir. PC\'lerde GPS olmadığı için konum yanlış çıkabilir. Lütfen cep telefonunuzdan konum paylaşın veya manuel olarak doğru konumunuzu girin.'
                    }, status=400)
                
                # Mevcut taramayı bul ve ownership kontrolü
                try:
                    tarama = EtiketTarama.objects.select_related('etiket', 'etiket__evcil_hayvan').get(id=tarama_id)
                except EtiketTarama.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Tarama bulunamadı'}, status=404)
                
                # GÜVENLİK: tarama_id ownership kontrolü - Bu tarama bu etikete ait mi?
                if tarama.etiket_id != etiket.id:
                    logger.warning(f"🚨 GÜVENLİK: tarama_id ownership hatası - tarama.etiket_id={tarama.etiket_id}, etiket.id={etiket.id}")
                    return JsonResponse({'success': False, 'error': 'Bu tarama bu etikete ait değil'}, status=403)
                
                # GPS zaten gönderilmiş mi kontrolü (duplicate önleme)
                if tarama.gps_latitude and tarama.gps_longitude:
                    logger.info(f"ℹ️ GPS zaten mevcut, güncelleniyor: {tarama.gps_latitude}, {tarama.gps_longitude}")
                
                # Doğruluk kategorisi belirle
                if accuracy <= GPS_ACCURACY_IDEAL:
                    accuracy_level = 'IDEAL'
                    logger.info(f"✅ GPS doğruluğu mükemmel: ±{accuracy:.0f}m")
                elif accuracy <= GPS_ACCURACY_ACCEPTABLE:
                    accuracy_level = 'ACCEPTABLE'
                    logger.info(f"✅ GPS doğruluğu iyi: ±{accuracy:.0f}m")
                elif accuracy <= GPS_ACCURACY_POOR:
                    accuracy_level = 'POOR'
                    logger.warning(f"⚠️ GPS doğruluğu düşük: ±{accuracy:.0f}m")
                else:
                    accuracy_level = 'VERY_POOR'
                    logger.warning(f"🚨 GPS doğruluğu çok düşük: ±{accuracy:.0f}m")
                
                # Transaction içinde GPS güncelle
                with transaction.atomic():
                    # GPS bilgilerini ekle (daha yüksek hassasiyet)
                    from .models import KONUM_KAYNAGI_GPS, KONUM_KAYNAGI_MANUEL, KONUM_KAYNAGI_IP
                    # Konum kaynağını belirle
                    if konum_kaynagi == 'MANUEL':
                        kaynak = KONUM_KAYNAGI_MANUEL
                    elif konum_kaynagi == 'IP':
                        kaynak = KONUM_KAYNAGI_IP
                    else:
                        kaynak = KONUM_KAYNAGI_GPS  # Varsayılan GPS
                    
                    tarama.gps_latitude = round(lat, 8)
                    tarama.gps_longitude = round(lng, 8)
                    tarama.gps_dogruluk = accuracy
                    tarama.konum_kaynagi = kaynak
                    tarama.save(update_fields=['gps_latitude', 'gps_longitude', 'gps_dogruluk', 'konum_kaynagi'])
                    
                    # DEBUG: Kaydedilen GPS verilerini kontrol et
                    tarama.refresh_from_db()  # Veritabanından güncel veriyi al
                    logger.info(f"🔍 GPS KAYDEDİLDİ - Latitude: {tarama.gps_latitude}")
                    logger.info(f"🔍 GPS KAYDEDİLDİ - Longitude: {tarama.gps_longitude}")
                    logger.info(f"🔍 GPS KAYDEDİLDİ - Accuracy: {tarama.gps_dogruluk}")
                    
                    # Anomali kontrolü
                    anomalies = check_location_anomalies(tarama)
                    if anomalies:
                        anomaly_messages = '\n'.join([a['message'] for a in anomalies])
                        logger.warning(f"⚠️ KONUM ANOMALISI tespit edildi:\n{anomaly_messages}")
                    
                    # GPS'li e-posta bildirimi gönder (YENİ E-POSTA)
                    try:
                        send_scan_notification(etiket, hayvan, sahip, tarama, has_finder_info=False)
                        logger.info(f"✅ GPS güncellendi ve YENİ e-posta gönderildi: {tarama_id}")
                    except Exception as e:
                        logger.error(f"❌ E-posta gönderim hatası (GPS güncellendi): {e}")
                        # E-posta gönderilemese bile GPS güncellendi
                
                # DEBUG: E-posta içeriğini logla
                logger.info(f"📧 E-POSTA GÖNDERİLDİ - GPS: {tarama.gps_latitude}, {tarama.gps_longitude}")
                logger.info(f"📧 E-POSTA GÖNDERİLDİ - IP: {tarama.ip_sehir}, {tarama.ip_ulke}")
                
                # Sahip için GPS bildirimi oluştur
                bildirim_url = f"/tag/tarama/{tarama.id}/detay/"
                # Koordinatları 8 ondalık basamağa yuvarla (daha yüksek doğruluk)
                lat_rounded = round(float(gps_lat), 8)
                lng_rounded = round(float(gps_lng), 8)
                harita_link = f"https://www.google.com/maps/place/{lat_rounded},{lng_rounded}"
                
                # Bildirim mesajına doğruluk bilgisi ekle
                accuracy_status = ''
                if accuracy_level == 'IDEAL':
                    accuracy_status = 'Mükemmel doğruluk!'
                elif accuracy_level == 'ACCEPTABLE':
                    accuracy_status = 'İyi doğruluk.'
                elif accuracy_level == 'POOR':
                    accuracy_status = 'Düşük doğruluk (VPN/Wi-Fi konumu olabilir).'
                else:
                    accuracy_status = 'Çok düşük doğruluk (şüpheli).'
                
                # Anomali varsa mesaja ekle
                anomaly_note = ''
                if anomalies:
                    anomaly_note = f"\n⚠️ UYARI: {len(anomalies)} anomali tespit edildi."
                
                create_notification(
                    sahip=sahip,
                    baslik=f"📍 {hayvan.ad} adlı hayvanınızın GPS konumu alındı!",
                    mesaj=f"{hayvan.ad} adlı hayvanınızın 📍 GERÇEK GPS KONUMU paylaşıldı.\n\n✅ Konum Kaynağı: GPS (Gerçek Konum)\n📏 Doğruluk: ±{float(gps_acc):.0f}m ({accuracy_status}){anomaly_note}\n🗺️ Harita: {harita_link}",
                    tur='QR_TARAMA',
                    tarama=tarama,
                    url=bildirim_url
                )
                logger.info(f"✅ GPS bildirimi oluşturuldu: {sahip.kullanici.username}")
                
                return JsonResponse({
                    'success': True, 
                    'message': 'GPS konumu güncellendi ve sahibe bildirildi',
                    'accuracy': float(gps_acc),
                    'accuracy_level': accuracy_level,
                    'anomalies_detected': len(anomalies) if anomalies else 0
                })
            except EtiketTarama.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Tarama bulunamadı'}, status=404)
            except Exception as e:
                logger.error(f"❌ GPS güncelleme hatası: {e}")
                return JsonResponse({'success': False, 'error': str(e)}, status=500)


def location_test_view(request):
    """Konum test sayfası - Debug için"""
    if request.method == 'GET':
        return render(request, 'etiket/location_test.html')
    
    elif request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'test_gps':
            gps_lat = request.POST.get('gps_latitude')
            gps_lng = request.POST.get('gps_longitude')
            gps_acc = request.POST.get('gps_accuracy')
            
            logger.info(f"🧪 GPS TEST - Latitude: {gps_lat}")
            logger.info(f"🧪 GPS TEST - Longitude: {gps_lng}")
            logger.info(f"🧪 GPS TEST - Accuracy: {gps_acc}")
            
            return JsonResponse({
                'success': True,
                'message': 'GPS test başarılı',
                'gps_latitude': gps_lat,
                'gps_longitude': gps_lng,
                'gps_accuracy': gps_acc
            })
        
        elif action == 'test_ip':
            # IP bilgilerini al
            ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', 'Bilinmiyor')).split(',')[0].strip()
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # IP lokasyon bilgisi
            ip_sehir, ip_ulke, ip_lokasyon = get_ip_location(ip)
            
            logger.info(f"🧪 IP TEST - IP: {ip}")
            logger.info(f"🧪 IP TEST - Şehir: {ip_sehir}")
            logger.info(f"🧪 IP TEST - Ülke: {ip_ulke}")
            
            return JsonResponse({
                'success': True,
                'message': 'IP test başarılı',
                'ip_address': ip,
                'ip_city': ip_sehir,
                'ip_country': ip_ulke,
                'ip_location': ip_lokasyon,
                'user_agent': user_agent
            })
        
        return JsonResponse({'success': False, 'message': 'Geçersiz action'})


# 2. SERİ NUMARASIYLA YÖNLENDİRME
def qr_by_serial_view(request, serial_number):
    try:
        etiket = Etiket.objects.get(seri_numarasi=serial_number)
        return redirect('etiket:qr_landing', tag_id=etiket.etiket_id)
    except Etiket.DoesNotExist:
        messages.error(request, "❌ Bu seri numarasına ait etiket bulunamadı.")
        return redirect('etiket:lookup')


# 3. QR KODUNU OLUŞTUR VE İNDİR
def qr_download_view(request, tag_id):
    etiket = get_object_or_404(Etiket, etiket_id=tag_id)
    qr_url = request.build_absolute_uri(
        redirect('etiket:qr_landing', tag_id=etiket.etiket_id).url
    )

    qr = qrcode.make(qr_url)
    buffer = io.BytesIO()
    qr.save(buffer, format='PNG')
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="etiket_{etiket.seri_numarasi}.png"'
    return response


# 4. KONUM BİLDİRİMİ (DUMMY SAYFA)
def qr_notify_location(request, tag_id):
    etiket = get_object_or_404(Etiket, etiket_id=tag_id)
    return render(request, 'etiket/notify_success.html', {
        'etiket': etiket,
        'hayvan': etiket.evcil_hayvan
    })


# 5. MANUEL SERİ NUMARA ARAMA FORMU
def serial_number_lookup_view(request):
    form = SeriNumaraForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            serial_number = form.cleaned_data['seri_numarasi']
            return redirect('etiket:qr_by_serial', serial_number=serial_number)

    return render(request, 'etiket/serial_lookup_form.html', {'form': form})


# ============= KÜNYE YENİLEME SİSTEMİ =============

@login_required
def etiket_yenileme_listesi(request):
    """Kullanıcının künyelerini ve yenileme durumlarını listele"""
    
    # Kullanıcının etiketleri (aktif ve süresi dolmuş)
    etiketler = Etiket.objects.filter(
        evcil_hayvan__sahip__kullanici=request.user
    ).select_related('evcil_hayvan', 'evcil_hayvan__sahip')
    
    # Süresi dolmuş etiketler
    suresi_dolmus = etiketler.filter(
        aktif=True,
        son_kullanma_tarihi__lt=timezone.now()
    )
    
    # Aktif etiketler
    aktif_etiketler = etiketler.filter(
        aktif=True,
        son_kullanma_tarihi__gte=timezone.now()
    )
    
    # Pasif etiketler
    pasif_etiketler = etiketler.filter(aktif=False)
    
    context = {
        'suresi_dolmus': suresi_dolmus,
        'aktif_etiketler': aktif_etiketler,
        'pasif_etiketler': pasif_etiketler,
    }
    
    return render(request, 'etiket/etiket_yenileme_listesi.html', context)


@login_required
def etiket_yenileme_baslat(request, etiket_id):
    """Künye yenileme işlemini başlat"""
    
    etiket = get_object_or_404(Etiket, id=etiket_id, evcil_hayvan__sahip__kullanici=request.user)
    
    # Etiket süresi dolmuş mu kontrol et
    if etiket.aktif and etiket.son_kullanma_tarihi and etiket.son_kullanma_tarihi > timezone.now():
        messages.warning(request, "Bu künyenin süresi henüz dolmamış!")
        return redirect('etiket:etiket_yenileme_listesi')
    
    # Fiyatlandırma seçenekleri - Kategori fark etmeksizin genel fiyatlar
    fiyatlar = EtiketYenilemeFiyati.objects.filter(
        aktif=True,
        etiket_kategori__isnull=True  # Sadece genel fiyatlar
    ).order_by('sure_gun')
    
    if request.method == 'POST':
        form = EtiketYenilemeForm(request.POST)
        if form.is_valid():
            fiyat_obj = form.cleaned_data['fiyat_id']  # ModelChoiceField zaten obje döndürüyor
            
            # Yenileme kaydı oluştur
            yenileme = EtiketYenileme.objects.create(
                etiket=etiket,
                kullanici=request.user,
                yenileme_ucreti=fiyat_obj.get_kullanici_fiyati(request.user),
                yenileme_suresi_gun=fiyat_obj.sure_gun
            )
            
            # Stripe API key kontrolü
            if not settings.STRIPE_SECRET_KEY or settings.STRIPE_SECRET_KEY.startswith('sk_test_51234567890'):
                # Test modu - Gerçek ödeme yapmadan simüle et
                messages.warning(request, "⚠️ Test Modu: Gerçek ödeme yapılmadı. Stripe API key'i geçerli değil.")
                
                # Yenileme kaydını ödendi olarak işaretle (test için)
                yenileme.odeme_durumu = 'ODENDI'
                yenileme.odeme_tarihi = timezone.now()
                yenileme.yeni_bitis_tarihi = timezone.now() + timedelta(days=fiyat_obj.sure_gun)
                yenileme.save()
                
                # Etiket süresini güncelle
                etiket.son_kullanma_tarihi = yenileme.yeni_bitis_tarihi
                etiket.aktif = True
                etiket.save()
                
                sure_text = "Sınırsız" if fiyat_obj.sure_gun == 9999 else f"{fiyat_obj.sure_gun} günlük"
                messages.success(request, f"✅ Test Modu: {sure_text} yenileme başarıyla tamamlandı! (Gerçek ödeme yapılmadı)")
                
                return redirect('etiket:etiket_yenileme_detay', yenileme_id=yenileme.id)
            
            # Gerçek Stripe ödemesi
            try:
                stripe.api_key = settings.STRIPE_SECRET_KEY
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{
                        'price_data': {
                            'currency': 'try',
                            'product_data': {
                                'name': f'Künye Yenileme - {etiket.seri_numarasi}',
                                'description': f'{"Sınırsız" if fiyat_obj.sure_gun == 9999 else f"{fiyat_obj.sure_gun} günlük"} yenileme',
                            },
                            'unit_amount': int(fiyat_obj.get_kullanici_fiyati(request.user) * 100),  # Kuruş cinsinden
                        },
                        'quantity': 1,
                    }],
                    mode='payment',
                    success_url=request.build_absolute_uri(
                        f'/etiket/yenileme/basarili/{yenileme.id}/'
                    ),
                    cancel_url=request.build_absolute_uri(
                        f'/etiket/yenileme/iptal/{yenileme.id}/'
                    ),
                    metadata={
                        'yenileme_id': yenileme.id,
                        'etiket_id': etiket.id,
                    }
                )
                
                # Stripe session ID'yi kaydet
                yenileme.stripe_session_id = checkout_session.id
                yenileme.save()
                
                # Başarı mesajı
                sure_text = "Sınırsız" if fiyat_obj.sure_gun == 9999 else f"{fiyat_obj.sure_gun} günlük"
                messages.success(request, f"Ödeme sayfasına yönlendiriliyorsunuz. {sure_text} yenileme için {fiyat_obj.get_kullanici_fiyati(request.user):.2f} TL ödenecek.")
                
                return redirect(checkout_session.url)
                
            except stripe.error.StripeError as e:
                messages.error(request, f"Ödeme sistemi hatası: {str(e)}")
                return redirect('etiket:etiket_yenileme_baslat', etiket_id=etiket.id)
    
    else:
        form = EtiketYenilemeForm()
    
    # Fiyatları kullanıcı için hesapla
    fiyatlar_with_user_price = []
    for fiyat in fiyatlar:
        fiyat.user_price = fiyat.get_kullanici_fiyati(request.user)
        fiyatlar_with_user_price.append(fiyat)
    
    context = {
        'etiket': etiket,
        'fiyatlar': fiyatlar_with_user_price,
        'form': form,
    }
    
    return render(request, 'etiket/etiket_yenileme_baslat.html', context)


def etiket_yenileme_basarili(request, yenileme_id):
    """Stripe ödeme başarılı callback"""
    
    yenileme = get_object_or_404(EtiketYenileme, id=yenileme_id)
    
    # Stripe session'ı kontrol et
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        session = stripe.checkout.Session.retrieve(yenileme.stripe_session_id)
        
        if session.payment_status == 'paid':
            # Ödeme başarılı
            yenileme.odeme_durumu = 'ODENDI'
            yenileme.stripe_payment_intent_id = session.payment_intent
            yenileme.save()  # save() metodu otomatik olarak etiket süresini uzatacak
            
            messages.success(request, f"Künye başarıyla yenilendi! Yeni bitiş tarihi: {yenileme.yeni_bitis_tarihi.strftime('%d.%m.%Y')}")
        else:
            messages.error(request, "Ödeme işlemi tamamlanamadı.")
            
    except stripe.error.StripeError as e:
        messages.error(request, f"Ödeme doğrulama hatası: {str(e)}")
    
    return redirect('etiket:etiket_yenileme_listesi')


def etiket_yenileme_iptal(request, yenileme_id):
    """Stripe ödeme iptal callback"""
    
    yenileme = get_object_or_404(EtiketYenileme, id=yenileme_id)
    yenileme.odeme_durumu = 'IPTAL'
    yenileme.save()
    
    messages.info(request, "Ödeme işlemi iptal edildi.")
    return redirect('etiket:etiket_yenileme_listesi')


@login_required
def etiket_yenileme_detay(request, yenileme_id):
    """Yenileme detaylarını göster"""
    
    yenileme = get_object_or_404(
        EtiketYenileme, 
        id=yenileme_id, 
        kullanici=request.user
    )
    
    context = {
        'yenileme': yenileme,
    }
    
    return render(request, 'etiket/etiket_yenileme_detay.html', context)
