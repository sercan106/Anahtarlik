# PythonAnywhere Deployment Kontrol Listesi

Bu dosya, PythonAnywhere'e deployment sırasında takip edilecek adımları içerir.

## ✅ Tamamlanan Adımlar

- [x] 1. PythonAnywhere hesabı oluşturuldu
- [x] 2. Proje GitHub'dan klonlandı
- [x] 3. Virtual environment oluşturuldu (Python 3.9)
- [x] 4. Requirements.txt güncellendi (Django 4.2)
- [x] 5. Bağımlılıklar yüklendi (pip install -r requirements.txt)

## 📋 Yapılacak Adımlar

### 6. Environment Variables (.env) Dosyası Oluşturma

PythonAnywhere konsolunda şu komutları çalıştırın:

```bash
cd ~/Anahtarlik/courseapp
nano .env
```

Aşağıdaki içeriği ekleyin (kendi değerlerinizle değiştirin):

```env
SECRET_KEY=your-secret-key-here-generate-with-command-below
DEBUG=False
ALLOWED_HOSTS=serco.pythonanywhere.com
SITE_URL=https://serco.pythonanywhere.com

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

STRIPE_PUBLIC_KEY=pk_test_your_key
STRIPE_SECRET_KEY=sk_test_your_key
STRIPE_WEBHOOK_SECRET=whsec_your_secret
STRIPE_TEST_MODE=True

CONTACT_EMAIL=info@petsafehub.com
ADMIN_EMAILS=admin@petsafehub.com
```

**SECRET_KEY oluşturma:**
```bash
python manage.py shell
>>> from django.core.management.utils import get_random_secret_key
>>> print(get_random_secret_key())
# Çıkan değeri kopyalayıp .env dosyasındaki SECRET_KEY yerine yapıştırın
>>> exit()
```

**Önemli:** `serco.pythonanywhere.com` yerine kendi PythonAnywhere kullanıcı adınızı yazın!

---

### 7. Veritabanı Migration ve Superuser

```bash
cd ~/Anahtarlik/courseapp
python manage.py migrate
python manage.py createsuperuser
```

Superuser oluştururken kullanıcı adı, e-posta ve şifre girmeniz istenecek.

---

### 8. Static Files Toplama

```bash
python manage.py collectstatic --noinput
```

Bu komut tüm static dosyaları `staticfiles` klasörüne toplayacak.

---

### 9. Web App Yapılandırması

1. PythonAnywhere dashboard'undan **"Web"** sekmesine gidin
2. **"Add a new web app"** butonuna tıklayın (eğer daha önce oluşturmadıysanız)
3. Domain seçin: `serco.pythonanywhere.com` (kendi kullanıcı adınız)
4. Python framework seçin: **Manual configuration**
5. Python version seçin: **Python 3.9** (venv'inizde kullandığınız versiyon)

---

### 10. WSGI Dosyası Yapılandırması

"Web" sekmesinde **"WSGI configuration file"** linkine tıklayın ve dosyanın içeriğini şu şekilde değiştirin:

```python
import os
import sys

# Proje dizinini path'e ekle
path = '/home/serco/Anahtarlik/courseapp'
if path not in sys.path:
    sys.path.insert(0, path)

# Virtual environment'ı aktif et
activate_this = '/home/serco/.virtualenvs/venv/bin/activate_this.py'
if os.path.exists(activate_this):
    exec(open(activate_this).read(), {'__file__': activate_this})

# Django settings modülünü ayarla
os.environ['DJANGO_SETTINGS_MODULE'] = 'courseapp.settings'

# WSGI application'ı import et
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

**Önemli:** 
- `/home/serco` yerine kendi PythonAnywhere kullanıcı adınızı yazın
- Virtual environment path'i doğru olmalı: `/home/serco/.virtualenvs/venv/bin/activate_this.py`

---

### 11. Static ve Media Files Yapılandırması

"Web" sekmesinde **"Static files"** bölümüne gidin ve şu mapping'leri ekleyin:

**Static files:**
- URL: `/static/`
- Directory: `/home/serco/Anahtarlik/courseapp/staticfiles`

**Media files:**
- URL: `/media/`
- Directory: `/home/serco/Anahtarlik/courseapp/media`

**Not:** Her mapping'i ekledikten sonra "Add" butonuna tıklamayı unutmayın!

---

### 12. Web App'i Yeniden Yükleme

"Web" sekmesinde yeşil **"Reload"** butonuna tıklayın.

---

### 13. Test Etme

Tarayıcınızda şu adresi açın:
```
https://serco.pythonanywhere.com
```

Eğer hata alırsanız, log dosyalarını kontrol edin:
```bash
# Error log
tail -n 50 ~/logs/serco.pythonanywhere.com.error.log

# Server log
tail -n 50 ~/logs/serco.pythonanywhere.com.server.log
```

---

## 🐛 Yaygın Hatalar ve Çözümleri

### "DisallowedHost" Hatası
- `.env` dosyasında `ALLOWED_HOSTS` değerini kontrol edin
- PythonAnywhere kullanıcı adınızı doğru yazdığınızdan emin olun

### "ModuleNotFoundError" Hatası
- Virtual environment'ın doğru aktif olduğundan emin olun
- WSGI dosyasında path'lerin doğru olduğunu kontrol edin
- `pip list` ile paketlerin yüklü olduğunu kontrol edin

### "Static files not found" Hatası
- `collectstatic` komutunu çalıştırdığınızdan emin olun
- Web app ayarlarında static files mapping'in doğru olduğunu kontrol edin

### "Database locked" Hatası
- SQLite kullanıyorsanız normal olabilir
- Ücretsiz hesapta aynı anda çok fazla istek gelirse bu hata oluşabilir

---

## 📝 Notlar

1. **Ücretsiz hesap sınırlamaları:**
   - Sadece 1 web app
   - Sınırlı CPU süresi
   - Sınırlı disk alanı
   - Dışarıdan erişim sınırlı (sadece belirli saatlerde)

2. **Güvenlik:**
   - `DEBUG=False` olarak ayarlayın
   - `SECRET_KEY`'i asla paylaşmayın
   - `.env` dosyasını Git'e eklemeyin

3. **Domain:**
   - Ücretsiz hesapta sadece `username.pythonanywhere.com` kullanılabilir
   - Özel domain için ücretli hesap gerekir

---

## 🔄 Güncelleme İşlemleri

Projeyi güncellediğinizde:

```bash
cd ~/Anahtarlik
git pull
cd courseapp
source ~/.virtualenvs/venv/bin/activate  # Virtual env'i aktif et
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Sonra Web sekmesinden "Reload" butonuna tıklayın.



