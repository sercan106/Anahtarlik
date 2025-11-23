"""
Proje Geneli Constants
Hardcoded değerler burada tanımlanır
"""
import logging

logger = logging.getLogger(__name__)

# ========== KREDİ SİSTEMİ ==========
# Etiket satışı başına verilen kredi miktarı
ETIKET_SATIS_KREDI = 150

# ========== KAPASİTE HESAPLAMA ==========
# Veteriner kapasite hesaplama ayarları
VETERINER_BASE_KAPASITE = 50
VETERINER_KAPASITE_ARALIKLAR = {
    'ustas': {'min_satis': 100, 'bonus': 80},
    'uzman': {'min_satis': 50, 'bonus': 60},
    'deneyimli': {'min_satis': 25, 'bonus': 40},
    'gelisen': {'min_satis': 10, 'bonus': 25},
    'baslangic': {'min_satis': 5, 'bonus': 15},
    'yeni': {'min_satis': 1, 'bonus': 5},
}
VETERINER_KAPASITE_MIN = 30
VETERINER_KAPASITE_MAX = 200

# Veteriner yüzde bonus aralıkları
VETERINER_YUZDE_BONUS = {
    'yuksek': {'min_yuzde': 20, 'bonus': 30},
    'orta': {'min_yuzde': 10, 'bonus': 20},
    'dusuk': {'min_yuzde': 5, 'bonus': 10},
}

# ========== E-POSTA AYARLARI ==========
# IP lokasyon API ayarları
IP_LOCATION_API_TIMEOUT = 3  # saniye
IP_LOCATION_CACHE_DURATION = 86400  # 24 saat (saniye cinsinden)

# E-posta gönderimi için timeout
EMAIL_SEND_TIMEOUT = 5  # saniye

# ========== ETİKET SİSTEMİ ==========
# Etiket yenileme ve süre ayarları
ETIKET_YENILEME_SURE_GUN = 365  # 1 yıl
ETIKET_SON_KULLANMA_SURE_GUN = 365  # 1 yıl

# ========== BİLDİRİM SİSTEMİ ==========
# Bildirim saklama süreleri (gün cinsinden)
BILDIRIM_SAKLAMA_SURELERI = {
    'kritik': 30,   # QR_TARAMA, BULAN_BILGI, KAYIP_HAYVAN
    'genel': 7,     # GENEL
    'promosyon': 3, # SISTEM, PROMOSYON
}

# ========== STOK YÖNETİMİ ==========
# Stok uyarı seviyeleri
STOK_KRITIK_SEVIYE = 5
STOK_UYARI_SEVIYESI = 10

# ========== SİPARİŞ AYARLARI ==========
# Minimum sipariş tutarları
MIN_SIPARIS_TUTARI_DEFAULT = 0  # TL

# Kargo ayarları
UCRETSIZ_KARGO_LIMIT_DEFAULT = 0  # TL

# ========== PAGINATION ==========
# Sayfalama ayarları
PAGINATION_SIZE = 20  # Sayfa başına öğe sayısı
PAGINATION_SIZE_LARGE = 50

# ========== QR KOD AYARLARI ==========
# QR kod seri numarası uzunluğu
QR_SERI_NUMARA_UZUNLUGU = 7

# QR kod karakterleri (karışıklık yaratmayacak harfler)
QR_SERI_KARAKTERLER = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'

# ========== SERIAL NUMBER GENERATION ==========
# Seri numarası üretim max deneme sayısı
MAX_SERIAL_GENERATION_TRIES = 1000

# ========== LOGGING ==========
# Log seviyeleri
LOG_LEVEL_INFO = 'INFO'
LOG_LEVEL_DEBUG = 'DEBUG'
LOG_LEVEL_WARNING = 'WARNING'
LOG_LEVEL_ERROR = 'ERROR'

# ========== COOKIE & SESSION ==========
# Session ayarları
SESSION_COOKIE_AGE = 86400 * 30  # 30 gün (saniye)

# ========== FILE UPLOAD ==========
# Maksimum dosya boyutu (byte)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB

# İzin verilen dosya uzantıları
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
ALLOWED_DOCUMENT_EXTENSIONS = ['.pdf', '.doc', '.docx']

# ========== API AYARLARI ==========
# API rate limiting
API_MAX_REQUESTS_PER_MINUTE = 60
API_MAX_REQUESTS_PER_HOUR = 1000

# ========== GEO LOCATION ==========
# GPS timeout ayarları (milisaniye)
GPS_HIGH_ACCURACY_TIMEOUT = 15000  # 15 saniye
GPS_STANDARD_TIMEOUT = 10000  # 10 saniye

# GPS maksimum yaş (milisaniye)
GPS_MAX_AGE_NONE = 0  # Her zaman yeni konum al
GPS_MAX_AGE_CACHED = 60000  # 1 dakika

# GPS doğruluk eşikleri (metre)
GPS_ACCURACY_IDEAL = 30  # İdeal doğruluk (≤30m)
GPS_ACCURACY_ACCEPTABLE = 100  # Kabul edilebilir doğruluk (≤100m)
GPS_ACCURACY_POOR = 500  # Kötü doğruluk (>100m <500m)
GPS_ACCURACY_VERY_POOR = 500  # Çok kötü doğruluk (≥500m)

# GPS örnek toplama ayarları
GPS_MAX_SAMPLES = 5  # Maksimum örnek sayısı
GPS_MAX_WAIT_MS = 25000  # Maksimum bekleme süresi (25 saniye)

# ========== VETERINER RANDEVU ==========
# Randevu ayarları
RANDEVU_MINUTES_INTERVAL = 30  # dakika
RANDEVU_ADVANCE_DAYS = 30  # Gün

# ========== PRO ABONELIK ==========
# Pro abonelik süreleri (gün cinsinden)
PRO_ABONELIK_SURE_DEFAULT = 30

# Fotoğraf galeri limiti
PRO_FOTO_GALERI_LIMIT_DEFAULT = 50

# ========== STRIPE AYARLARI ==========
# Stripe webhook tolerance (saniye)
STRIPE_WEBHOOK_TOLERANCE = 300  # 5 dakika

# ========== HIZLIMAN ==========
# Hizmet kartları ayarları
HIZMET_KARTI_ANIMASYON_DELAY_DEFAULT = 100  # milisaniye

# ========== HERO SLIDER ==========
# Hero slider geçiş süresi (milisaniye)
HERO_SLIDE_DURATION_DEFAULT = 5000  # 5 saniye

# ========== OYUNCULAR VE BAŞARIMLAR ==========
# Veteriner satış başarı seviyeleri
VETERINER_BASARI_SEVIYELERI = {
    'ustasi': {'min_satis': 100, 'ikon': '🏆', 'ad': 'Ustası'},
    'uzman': {'min_satis': 50, 'ikon': '🥇', 'ad': 'Uzman'},
    'deneyimli': {'min_satis': 25, 'ikon': '🥈', 'ad': 'Deneyimli'},
    'gelisen': {'min_satis': 10, 'ikon': '🥉', 'ad': 'Gelişen'},
    'baslangic': {'min_satis': 5, 'ikon': '⭐', 'ad': 'Başlangıç'},
    'yeni': {'min_satis': 0, 'ikon': '🌱', 'ad': 'Yeni'},
}

# ========== KAPASİTE DURUMLARI ==========
# Veteriner kapasite durumları
KAPASITE_DURUMLARI = {
    'dolu': {'min_oran': 100, 'ad': 'Dolu'},
    'doluya_yakin': {'min_oran': 80, 'ad': 'Doluya Yakın'},
    'orta': {'min_oran': 50, 'ad': 'Orta'},
    'bos': {'min_oran': 0, 'ad': 'Boş'},
}

# ========== DICTIONARY REFERENCE ==========
# Constants'ları kullanan modeller için helper fonksiyonlar
def get_veteriner_basari_seviyesi(satis_sayisi):
    """
    Veteriner satış sayısına göre başarı seviyesi döndürür
    """
    for level_key, level_info in VETERINER_BASARI_SEVIYELERI.items():
        if satis_sayisi >= level_info['min_satis']:
            return level_key, level_info
    return 'yeni', VETERINER_BASARI_SEVIYELERI['yeni']

def get_veteriner_kapasite_bonus(satis_sayisi):
    """
    Veteriner satış sayısına göre kapasite bonus'u döndürür
    """
    for level_key, level_info in VETERINER_KAPASITE_ARALIKLAR.items():
        if satis_sayisi >= level_info['min_satis']:
            return level_info['bonus']
    return 0

def get_kapasite_durumu(yuk, kapasite):
    """
    Veteriner yük ve kapasitesine göre durum döndürür
    """
    oran = (yuk / kapasite * 100) if kapasite > 0 else 0
    
    for durum_key, durum_info in KAPASITE_DURUMLARI.items():
        if oran >= durum_info['min_oran']:
            return durum_key, durum_info['ad']
    
    return 'bos', 'Boş'

