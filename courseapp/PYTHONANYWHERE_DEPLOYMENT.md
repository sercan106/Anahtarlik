# PythonAnywhere Deployment Rehberi

Bu rehber, Django projenizi PythonAnywhere'in ücretsiz hesabında yayınlamak için adım adım talimatlar içerir.

## Ön Hazırlık

### 1. Projeyi GitHub'a Yükleyin (Önerilen)

```bash
# Git repository oluşturun (eğer yoksa)
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/username/repo-name.git
git push -u origin main
```

**Önemli:** `.env` dosyasını `.gitignore`'a ekleyin:
```
.env
*.pyc
__pycache__/
db.sqlite3
logs/
media/
staticfiles/
```

### 2. PythonAnywhere Hesabı Oluşturun

1. https://www.pythonanywhere.com adresine gidin
2. Ücretsiz hesap oluşturun
3. E-posta doğrulamasını tamamlayın

## PythonAnywhere'de Kurulum

### 1. Konsol (Bash Console) Açın

PythonAnywhere dashboard'undan "Consoles" sekmesine gidin ve "Bash" konsolu açın.

### 2. Projeyi Klonlayın

```bash
cd ~
git clone https://github.com/username/repo-name.git courseapp
cd courseapp
```

**Not:** Eğer GitHub kullanmıyorsanız, dosyaları File tab'ından manuel olarak yükleyebilirsiniz.

### 3. Virtual Environment Oluşturun

```bash
# Python 3.10 veya 3.11 kullanın (PythonAnywhere'in desteklediği versiyon)
python3.10 -m venv venv
# veya
python3.11 -m venv venv

# Virtual environment'ı aktif edin
source venv/bin/activate
```

### 4. Bağımlılıkları Yükleyin

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Not:** Eğer `python-decouple` kurulumunda sorun yaşarsanız:
```bash
pip install python-decouple
```

### 5. Environment Variables Ayarlayın

`.env` dosyası oluşturun:

```bash
cd ~/courseapp
nano .env
```

Aşağıdaki içeriği ekleyin (kendi değerlerinizle değiştirin):

```env
SECRET_KEY=your-very-secret-key-here-generate-with-django
DEBUG=False
ALLOWED_HOSTS=username.pythonanywhere.com
SITE_URL=https://username.pythonanywhere.com

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
```

### 6. Veritabanını Oluşturun

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 7. Static Files Toplayın

```bash
python manage.py collectstatic --noinput
```

### 8. Web App Yapılandırması

1. PythonAnywhere dashboard'undan "Web" sekmesine gidin
2. "Add a new web app" butonuna tıklayın
3. Domain seçin: `username.pythonanywhere.com`
4. Python framework seçin: **Manual configuration**
5. Python version seçin: **Python 3.10** veya **3.11**

### 9. WSGI Dosyasını Yapılandırın

"Web" sekmesinde "WSGI configuration file" linkine tıklayın ve dosyayı şu şekilde güncelleyin:

```python
import os
import sys

# Proje dizinini path'e ekle
path = '/home/username/courseapp'
if path not in sys.path:
    sys.path.insert(0, path)

# Virtual environment'ı aktif et
activate_this = '/home/username/courseapp/venv/bin/activate_this.py'
if os.path.exists(activate_this):
    exec(open(activate_this).read(), {'__file__': activate_this})

# Django settings modülünü ayarla
os.environ['DJANGO_SETTINGS_MODULE'] = 'courseapp.settings'

# WSGI application'ı import et
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

**Önemli:** `username` kısmını kendi PythonAnywhere kullanıcı adınızla değiştirin.

### 10. Static ve Media Files Yapılandırması

"Web" sekmesinde "Static files" bölümüne gidin:

**Static files:**
- URL: `/static/`
- Directory: `/home/username/courseapp/staticfiles`

**Media files:**
- URL: `/media/`
- Directory: `/home/username/courseapp/media`

**Not:** Ücretsiz hesapta media files için sınırlı depolama alanı vardır. Büyük dosyalar için alternatif çözümler düşünün.

### 11. Web App'i Yeniden Yükleyin

"Web" sekmesinde yeşil "Reload" butonuna tıklayın.

## Sorun Giderme

### Hata: "ModuleNotFoundError"

- Virtual environment'ın doğru aktif olduğundan emin olun
- WSGI dosyasında path'lerin doğru olduğunu kontrol edin
- `pip list` ile paketlerin yüklü olduğunu kontrol edin

### Hata: "DisallowedHost"

- `.env` dosyasında `ALLOWED_HOSTS` değerini kontrol edin
- PythonAnywhere kullanıcı adınızı doğru yazdığınızdan emin olun

### Hata: "Static files not found"

- `collectstatic` komutunu çalıştırdığınızdan emin olun
- Web app ayarlarında static files mapping'in doğru olduğunu kontrol edin

### Hata: "Database locked"

- SQLite kullanıyorsanız, bu normal olabilir
- Ücretsiz hesapta aynı anda çok fazla istek gelirse bu hata oluşabilir
- Production için PostgreSQL kullanmayı düşünün (ücretli hesap gerekir)

### Log Dosyalarını Kontrol Etme

```bash
# Error log
tail -n 50 ~/logs/username.pythonanywhere.com.error.log

# Server log
tail -n 50 ~/logs/username.pythonanywhere.com.server.log
```

## Güncelleme İşlemleri

Projeyi güncellediğinizde:

```bash
cd ~/courseapp
git pull  # veya dosyaları manuel güncelleyin
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Sonra Web sekmesinden "Reload" butonuna tıklayın.

## Önemli Notlar

1. **Ücretsiz hesap sınırlamaları:**
   - Sadece 1 web app
   - Sınırlı CPU süresi
   - Sınırlı disk alanı
   - Dışarıdan erişim sınırlı (sadece belirli saatlerde)

2. **Güvenlik:**
   - `DEBUG=False` olarak ayarlayın
   - `SECRET_KEY`'i asla paylaşmayın
   - `.env` dosyasını Git'e eklemeyin

3. **Performans:**
   - SQLite production için ideal değildir
   - Büyük dosyalar için cloud storage (AWS S3, Cloudinary vb.) kullanmayı düşünün

4. **Domain:**
   - Ücretsiz hesapta sadece `username.pythonanywhere.com` kullanılabilir
   - Özel domain için ücretli hesap gerekir

## Yardım

- PythonAnywhere Dokümantasyonu: https://help.pythonanywhere.com/
- Django Deployment: https://docs.djangoproject.com/en/stable/howto/deployment/




