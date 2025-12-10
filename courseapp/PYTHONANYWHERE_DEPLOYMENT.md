# PythonAnywhere Deployment Rehberi

Bu rehber, Anahtarlık projesini PythonAnywhere ücretsiz hesabında yayınlamak için adım adım talimatlar içerir.

## 📋 Ön Gereksinimler

1. PythonAnywhere ücretsiz hesabı (https://www.pythonanywhere.com)
2. Git repository (GitHub, GitLab, vb.)
3. Proje dosyalarının hazır olması

---

## 🚀 Adım 1: Projeyi PythonAnywhere'e Yükleme

### 1.1. PythonAnywhere Console'a Giriş

1. PythonAnywhere'e giriş yapın
2. **Consoles** sekmesine gidin
3. **Bash** konsolu açın

### 1.2. Projeyi Klonlama veya Yükleme

```bash
# Proje dizinine git
cd ~

# Git ile klonlama (önerilen)
git clone https://github.com/yourusername/your-repo.git courseapp
cd courseapp

# VEYA dosyaları manuel yükleme
# Files sekmesinden dosyaları yükleyin
```

---

## 🔧 Adım 2: Python Ortamı ve Bağımlılıklar

### 2.1. Virtual Environment Oluşturma

```bash
cd ~/courseapp
python3.10 -m venv venv
source venv/bin/activate
```

### 2.2. Bağımlılıkları Yükleme

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## ⚙️ Adım 3: Environment Variables (.env Dosyası)

### 3.1. .env Dosyası Oluşturma

```bash
cd ~/courseapp
nano .env
```

### 3.2. .env İçeriği

```env
# Django Settings
SECRET_KEY=your-very-secret-key-here-generate-with-django-secret-key-generator
DEBUG=False
ALLOWED_HOSTS=yourusername.pythonanywhere.com
SITE_URL=https://yourusername.pythonanywhere.com

# Email Settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Stripe Settings (Test modunda)
STRIPE_PUBLIC_KEY=pk_test_your_key
STRIPE_SECRET_KEY=sk_test_your_key
STRIPE_WEBHOOK_SECRET=whsec_your_secret
STRIPE_TEST_MODE=True

# Site Settings
CONTACT_EMAIL=info@petsafehub.com
ADMIN_EMAILS=admin@petsafehub.com
```

**ÖNEMLİ:** 
- `SECRET_KEY` için: https://djangosecret.com/ adresinden yeni bir key oluşturun
- `ALLOWED_HOSTS` içine kendi PythonAnywhere domain'inizi yazın: `yourusername.pythonanywhere.com`
- `SITE_URL` içine HTTPS ile domain'inizi yazın

---

## 🗄️ Adım 4: Veritabanı Ayarları

### 4.1. Migration'ları Çalıştırma

```bash
cd ~/courseapp
source venv/bin/activate
python manage.py migrate
```

### 4.2. Superuser Oluşturma

```bash
python manage.py createsuperuser
```

---

## 📦 Adım 5: Static Files Toplama

### 5.1. Static Files Klasörünü Oluşturma

```bash
mkdir -p ~/courseapp/staticfiles
```

### 5.2. Collectstatic Komutu

```bash
python manage.py collectstatic --noinput
```

Bu komut tüm static dosyaları `staticfiles/` klasörüne toplar.

---

## 🌐 Adım 6: Web App Yapılandırması

### 6.1. Web App Oluşturma

1. PythonAnywhere dashboard'da **Web** sekmesine gidin
2. **Add a new web app** butonuna tıklayın
3. **Manual configuration** seçin
4. **Python 3.10** seçin (veya mevcut Python versiyonunuz)

### 6.2. WSGI Configuration

**WSGI configuration file** linkine tıklayın ve şu içeriği yazın:

```python
# /var/www/yourusername_pythonanywhere_com_wsgi.py

import os
import sys

# Proje dizinini path'e ekle
path = '/home/yourusername/courseapp'
if path not in sys.path:
    sys.path.insert(0, path)

# Virtual environment'i aktif et
activate_this = '/home/yourusername/courseapp/venv/bin/activate_this.py'
if os.path.exists(activate_this):
    with open(activate_this) as file_:
        exec(file_.read(), {'__file__': activate_this})

# Django settings modülünü ayarla
os.environ['DJANGO_SETTINGS_MODULE'] = 'courseapp.settings'

# Django WSGI application'ı import et
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

**ÖNEMLİ:** `yourusername` kısmını kendi kullanıcı adınızla değiştirin!

### 6.3. Static Files Mapping

**Static files** bölümünde:

- **URL:** `/static/`
- **Directory:** `/home/yourusername/courseapp/staticfiles`

### 6.4. Media Files Mapping

**Static files** bölümünde (media için):

- **URL:** `/media/`
- **Directory:** `/home/yourusername/courseapp/media`

**NOT:** Media klasörünü oluşturmayı unutmayın:
```bash
mkdir -p ~/courseapp/media
```

---

## 🔄 Adım 7: Web App'i Yeniden Yükleme

1. **Web** sekmesinde **Reload** butonuna tıklayın
2. Veya domain'inize gidip test edin: `https://yourusername.pythonanywhere.com`

---

## ✅ Adım 8: Kontrol ve Test

### 8.1. Site Kontrolü

- Ana sayfa açılıyor mu?
- Static dosyalar (CSS, JS, resimler) yükleniyor mu?
- Media dosyalar (yüklenen resimler) görünüyor mu?
- Admin paneli çalışıyor mu? (`/admin/`)

### 8.2. Hata Kontrolü

Hata alırsanız:

1. **Error log** dosyasını kontrol edin:
   - Web sekmesinde **Error log** linkine tıklayın
   - Veya: `/var/log/yourusername.pythonanywhere.com.error.log`

2. **Server log** dosyasını kontrol edin:
   - Web sekmesinde **Server log** linkine tıklayın

---

## 🔧 Sık Karşılaşılan Sorunlar ve Çözümleri

### Sorun 1: Static Files Görünmüyor

**Çözüm:**
```bash
# Static files'ı tekrar topla
cd ~/courseapp
source venv/bin/activate
python manage.py collectstatic --noinput

# Web app'i reload edin
```

### Sorun 2: Media Files Görünmüyor

**Çözüm:**
1. Media klasörünün var olduğundan emin olun: `ls -la ~/courseapp/media`
2. Web app ayarlarında media mapping'in doğru olduğundan emin olun
3. Dosya izinlerini kontrol edin: `chmod 755 ~/courseapp/media`

### Sorun 3: Database Locked Hatası

**Çözüm:**
```bash
# SQLite database'i kontrol et
cd ~/courseapp
sqlite3 db.sqlite3 ".timeout 20"
```

### Sorun 4: Import Error

**Çözüm:**
1. Virtual environment'in aktif olduğundan emin olun
2. Tüm bağımlılıkların yüklü olduğundan emin olun: `pip install -r requirements.txt`
3. WSGI dosyasında path'lerin doğru olduğundan emin olun

### Sorun 5: 500 Internal Server Error

**Çözüm:**
1. Error log'u kontrol edin
2. DEBUG=True yapıp hatayı görün (sonra tekrar False yapın)
3. .env dosyasının doğru yüklendiğinden emin olun

---

## 📝 Güncelleme İşlemi

Projeyi güncellediğinizde:

```bash
cd ~/courseapp
source venv/bin/activate

# Git'ten çek
git pull

# Bağımlılıkları güncelle
pip install -r requirements.txt

# Migration'ları çalıştır
python manage.py migrate

# Static files'ı topla
python manage.py collectstatic --noinput

# Web app'i reload et (Web sekmesinden)
```

---

## 🔐 Güvenlik Notları

1. **SECRET_KEY:** Asla paylaşmayın, her production ortamında farklı olmalı
2. **DEBUG:** Production'da mutlaka `False` olmalı
3. **ALLOWED_HOSTS:** Sadece kendi domain'inizi ekleyin
4. **.env dosyası:** `.gitignore`'da olduğundan emin olun

---

## 📞 Destek

Sorun yaşarsanız:
1. PythonAnywhere Error log'larını kontrol edin
2. Django error log'larını kontrol edin: `~/courseapp/logs/django.log`
3. PythonAnywhere forum'larına bakın: https://www.pythonanywhere.com/forums/

---

## ✅ Deployment Checklist

- [ ] Proje PythonAnywhere'e yüklendi
- [ ] Virtual environment oluşturuldu ve aktif
- [ ] Bağımlılıklar yüklendi (`pip install -r requirements.txt`)
- [ ] .env dosyası oluşturuldu ve dolduruldu
- [ ] Migration'lar çalıştırıldı (`python manage.py migrate`)
- [ ] Superuser oluşturuldu
- [ ] Static files toplandı (`python manage.py collectstatic`)
- [ ] Web app oluşturuldu ve yapılandırıldı
- [ ] WSGI dosyası düzenlendi
- [ ] Static files mapping yapıldı (`/static/` -> `staticfiles/`)
- [ ] Media files mapping yapıldı (`/media/` -> `media/`)
- [ ] Web app reload edildi
- [ ] Site test edildi (ana sayfa, admin, static/media dosyalar)
- [ ] DEBUG=False yapıldı
- [ ] ALLOWED_HOSTS doğru ayarlandı

---

**Başarılar! 🎉**

