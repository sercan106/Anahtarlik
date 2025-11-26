# 🔒 Güvenlik Açıkları Raporu

## 📋 Özet

Bu rapor, Django tabanlı PetSafe Hub uygulamasında tespit edilen güvenlik açıklarını ve önerileri içermektedir.

---

## 🚨 KRİTİK GÜVENLİK AÇIKLARI

### 1. ⚠️ DEBUG Modu Production'da Aktif Olabilir

**Konum:** `courseapp/settings.py:15`

**Sorun:**
```python
DEBUG = config('DEBUG', default=True, cast=bool)
```

**Risk:** Production ortamında DEBUG=True olması durumunda:
- Hassas bilgiler (SECRET_KEY, veritabanı bilgileri) hata sayfalarında görünebilir
- Stack trace'ler saldırganlara kod yapısı hakkında bilgi verir
- Güvenlik açıkları daha kolay tespit edilebilir

**Öneri:**
```python
# Production'da mutlaka False olmalı
DEBUG = config('DEBUG', default=False, cast=bool)
```

**Öncelik:** 🔴 YÜKSEK

---

### 2. ⚠️ SECRET_KEY için Güvensiz Default Değer

**Konum:** `courseapp/settings.py:14`

**Sorun:**
```python
SECRET_KEY = config('SECRET_KEY', default='django-insecure-$1!qju8gp_pq9!64se@y!n-h!=@f3%xgf(sx9*o43i$696k(4t-DEVELOPMENT-ONLY')
```

**Risk:** 
- Environment variable ayarlanmazsa, bilinen bir default değer kullanılıyor
- Bu değer kod deposunda görünüyor (Git'te commit edilmiş)
- Saldırganlar bu değeri kullanarak session'ları çalabilir

**Öneri:**
```python
# Default değer kaldırılmalı, environment variable zorunlu olmalı
SECRET_KEY = config('SECRET_KEY')  # default kaldırıldı, hata versin
```

**Öncelik:** 🔴 YÜKSEK

---

### 3. ⚠️ ALLOWED_HOSTS Güvenlik Açığı

**Konum:** `courseapp/settings.py:20`

**Sorun:**
```python
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())
```

**Risk:**
- Production'da yanlış domain ayarlanırsa Host Header Injection saldırılarına açık olabilir
- Default değerler production için uygun değil

**Öneri:**
```python
# Production'da mutlaka gerçek domain belirtilmeli
# .env dosyasında: ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())
```

**Öncelik:** 🟡 ORTA

---

## 🟡 ORTA SEVİYE GÜVENLİK AÇIKLARI

### 4. ⚠️ Input Validation Eksiklikleri

**Konum:** `veteriner/views.py:272-276`, `petshop/views.py:245-249`

**Sorun:**
```python
ad = request.POST.get('ad', '').strip()
telefon = request.POST.get('telefon', '').strip()
il_id = request.POST.get('il')
ilce_id = request.POST.get('ilce')
```

**Risk:**
- Kullanıcı girdileri doğrudan kullanılıyor, validasyon eksik
- `il_id` ve `ilce_id` integer'a cast edilmeden kullanılıyor
- SQL injection riski (Django ORM kullanıldığı için düşük ama yine de risk var)

**Öneri:**
```python
# Form validation kullanılmalı veya manuel validasyon yapılmalı
try:
    il_id = int(request.POST.get('il'))
    il_obj = Il.objects.get(id=il_id)
except (ValueError, TypeError, Il.DoesNotExist):
    messages.error(request, 'Geçersiz il seçimi')
    return redirect('...')
```

**Öncelik:** 🟡 ORTA

---

### 5. ⚠️ File Upload Güvenlik Kontrolleri

**Konum:** `ilan/views.py:318-336`, `accaunt/views.py:99-108`

**Sorun:**
- Dosya yükleme işlemlerinde dosya tipi kontrolü yetersiz
- Dosya boyutu kontrolü yok
- Dosya adı sanitization var ama yeterli değil

**Mevcut Kod:**
```python
resimler = request.FILES.getlist('resimler')
if resimler:
    if len(resimler) > 3:
        messages.warning(request, 'Maksimum 3 resim yüklenebilir.')
        resimler = resimler[:3]
```

**Risk:**
- Zararlı dosya tipleri yüklenebilir
- Çok büyük dosyalar sunucuyu yavaşlatabilir
- Dosya adlarında özel karakterler path traversal'a neden olabilir

**Öneri:**
```python
import os
from django.core.exceptions import ValidationError

ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

for resim in resimler:
    # Dosya tipi kontrolü
    if resim.content_type not in ALLOWED_IMAGE_TYPES:
        raise ValidationError('Sadece resim dosyaları yüklenebilir')
    
    # Dosya boyutu kontrolü
    if resim.size > MAX_FILE_SIZE:
        raise ValidationError('Dosya boyutu 5MB\'dan küçük olmalıdır')
    
    # Dosya adı sanitization
    filename = os.path.basename(resim.name)
    # Tehlikeli karakterleri temizle
    filename = "".join(c for c in filename if c.isalnum() or c in "._-")
```

**Öncelik:** 🟡 ORTA

---

### 6. ⚠️ Authorization Kontrolleri Eksiklikleri

**Konum:** `ilan/views.py:372-389`, `veteriner/views.py:272-276`

**Sorun:**
- Bazı view'larda kullanıcının kendi verilerine erişim kontrolü yapılıyor ama bazılarında eksik
- `get_object_or_404` kullanılıyor ama kullanıcı kontrolü her yerde yok

**İyi Örnek:**
```python
hayvan_profili = get_object_or_404(
    HayvanProfili,
    id=profil_id,
    kullanici=request.user  # ✅ Kullanıcı kontrolü var
)
```

**Riskli Örnek:**
```python
# Eğer kullanıcı kontrolü yoksa, başka kullanıcıların verilerine erişilebilir
hayvan_profili = get_object_or_404(HayvanProfili, id=profil_id)
```

**Öncelik:** 🟡 ORTA

---

## 🟢 DÜŞÜK SEVİYE / İYİLEŞTİRME ÖNERİLERİ

### 7. ✅ CSRF Koruması

**Durum:** ✅ İYİ
- `CsrfViewMiddleware` aktif
- `@csrf_exempt` kullanımı yok

**Öneri:** Mevcut durum yeterli, değişiklik gerekmiyor.

---

### 8. ✅ SQL Injection Koruması

**Durum:** ✅ İYİ
- Django ORM kullanılıyor (parametreli sorgular)
- Raw SQL kullanımları sadece management komutlarında ve sabit string'lerle

**Öneri:** Mevcut durum yeterli, ancak raw SQL kullanımlarında dikkatli olunmalı.

---

### 9. ⚠️ XSS Koruması

**Konum:** `shop/admin.py:6`

**Durum:** 🟡 KISMEN İYİ
- `mark_safe` kullanımı var ama sadece admin panelinde
- `format_html` kullanılıyor (güvenli)
- Template'lerde Django'nun otomatik escape mekanizması var

**Öneri:** 
- Admin panelinde `mark_safe` kullanımı kabul edilebilir (admin güvenilir kullanıcılar)
- Kullanıcı girdilerinde asla `mark_safe` kullanılmamalı

---

### 10. ⚠️ Session Güvenliği

**Konum:** `courseapp/settings.py:202-220`

**Durum:** 🟡 KISMEN İYİ
- Production ayarları var ama sadece DEBUG=False olduğunda aktif
- `SESSION_COOKIE_SECURE` ve `CSRF_COOKIE_SECURE` sadece production'da aktif

**Öneri:**
```python
# Her zaman HTTPS kullanılıyorsa (production'da olmalı)
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
```

---

## 📝 ÖNERİLER ÖZETİ

### Acil Yapılması Gerekenler (🔴 YÜKSEK ÖNCELİK):

1. ✅ **DEBUG=False** production'da mutlaka ayarlanmalı
2. ✅ **SECRET_KEY** için default değer kaldırılmalı, environment variable zorunlu olmalı
3. ✅ **ALLOWED_HOSTS** production domain'i ile ayarlanmalı

### Kısa Vadede Yapılması Gerekenler (🟡 ORTA ÖNCELİK):

4. ✅ **Input Validation** - Tüm kullanıcı girdileri validate edilmeli
5. ✅ **File Upload Güvenliği** - Dosya tipi, boyut ve ad sanitization kontrolü
6. ✅ **Authorization Kontrolleri** - Tüm view'larda kullanıcı yetki kontrolü

### İyileştirme Önerileri (🟢 DÜŞÜK ÖNCELİK):

7. ✅ **Rate Limiting** - Brute force saldırılarına karşı
8. ✅ **Logging** - Güvenlik olayları için detaylı loglama
9. ✅ **Security Headers** - CSP, X-Frame-Options, vb. header'lar

---

## 🔧 HIZLI DÜZELTME KODLARI

### settings.py Düzeltmeleri:

```python
# SECURITY: Environment variables kullan - default kaldır
SECRET_KEY = config('SECRET_KEY')  # default kaldırıldı
DEBUG = config('DEBUG', default=False, cast=bool)  # default False
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())  # default kaldırıldı

# Production güvenlik ayarları - her zaman aktif olmalı (HTTPS kullanılıyorsa)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
```

### File Upload Güvenlik Fonksiyonu:

```python
# courseapp/utils.py
import os
from django.core.exceptions import ValidationError

def validate_image_file(file):
    """Resim dosyası validasyonu"""
    ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    MAX_SIZE = 5 * 1024 * 1024  # 5MB
    
    if file.content_type not in ALLOWED_TYPES:
        raise ValidationError('Sadece JPEG, PNG, GIF veya WebP dosyaları yüklenebilir')
    
    if file.size > MAX_SIZE:
        raise ValidationError('Dosya boyutu 5MB\'dan küçük olmalıdır')
    
    # Dosya adı sanitization
    filename = os.path.basename(file.name)
    filename = "".join(c for c in filename if c.isalnum() or c in "._-")
    
    return filename
```

---

## 📚 KAYNAKLAR

- [Django Security Best Practices](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django Security Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)

---

**Rapor Tarihi:** 2024
**İnceleme Kapsamı:** Tüm Python dosyaları, settings.py, views.py, admin.py
**Toplam Tespit Edilen Açık:** 10 (3 Kritik, 3 Orta, 4 Düşük/İyileştirme)
