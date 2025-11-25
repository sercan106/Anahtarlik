# PythonAnywhere Deployment Rehberi

Bu rehber, Django projenizi PythonAnywhere'in ücretsiz hesabında yayınlamak için adım adım talimatlar içerir.

## 📋 Ön Hazırlık Kontrol Listesi

- [x] Migrations uygulandı (`python manage.py migrate`)
- [x] Static files toplandı (`python manage.py collectstatic`)
- [x] Requirements.txt hazır
- [x] .gitignore yapılandırıldı
- [ ] PythonAnywhere hesabı oluşturuldu
- [ ] GitHub repository hazır (önerilen)

## 🚀 Adım Adım Deployment

### 1. PythonAnywhere Hesabı Oluşturun

1. https://www.pythonanywhere.com adresine gidin
2. Ücretsiz hesap oluşturun
3. E-posta doğrulamasını tamamlayın

### 2. Projeyi PythonAnywhere'e Yükleyin

#### Seçenek A: GitHub ile (Önerilen)

```bash
# PythonAnywhere konsolunda
cd ~
git clone https://github.com/username/repo-name.git courseapp
cd courseapp
```

#### Seçenek B: Manuel Yükleme

1. PythonAnywhere dashboard'undan "Files" sekmesine gidin
2. Dosyalarınızı yükleyin veya zip dosyası olarak yükleyip açın

### 3. Virtual Environment Oluşturun

```bash
cd ~/courseapp
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
# Çıkan değeri kopyalayıp .env dosyasındaki SECRET_KEY yerine yapıştırın
>>> exit()
```

**ÖNEMLİ:** `username` kısmını kendi PythonAnywhere kullanıcı adınızla değiştirin!

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

1. PythonAnywhere dashboard'undan **"Web"** sekmesine gidin
2. **"Add a new web app"** butonuna tıklayın (eğer daha önce oluşturmadıysanız)
3. Domain seçin: `username.pythonanywhere.com`
4. Python framework seçin: **Manual configuration**
5. Python version seçin: **Python 3.10** veya **3.11** (venv'inizde kullandığınız versiyon)

### 9. WSGI Dosyasını Yapılandırın

"Web" sekmesinde **"WSGI configuration file"** linkine tıklayın ve dosyanın içeriğini `PYTHONANYWHERE_WSGI_TEMPLATE.py` dosyasındaki kodu kullanarak değiştirin.

**Önemli:** 
- `/home/username` yerine kendi PythonAnywhere kullanıcı adınızı yazın
- Proje path'ini doğru ayarlayın (genellikle `/home/username/courseapp`)
- Virtual environment path'ini doğru ayarlayın

### 10. Static ve Media Files Yapılandırması

"Web" sekmesinde **"Static files"** bölümüne gidin ve şu mapping'leri ekleyin:

**Static files:**
- URL: `/static/`
- Directory: `/home/username/courseapp/staticfiles`

**Media files:**
- URL: `/media/`
- Directory: `/home/username/courseapp/media`

**Not:** Her mapping'i ekledikten sonra "Add" butonuna tıklamayı unutmayın!

### 11. Web App'i Yeniden Yükleme

"Web" sekmesinde yeşil **"Reload"** butonuna tıklayın.

### 12. Test Etme

Tarayıcınızda şu adresi açın:
```
https://username.pythonanywhere.com
```

## 🐛 Sorun Giderme

### "DisallowedHost" Hatası

- `.env` dosyasında `ALLOWED_HOSTS` değerini kontrol edin
- PythonAnywhere kullanıcı adınızı doğru yazdığınızdan emin olun
- `ALLOWED_HOSTS_REHBERI.md` dosyasına bakın

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
- Production için PostgreSQL kullanmayı düşünün (ücretli hesap gerekir)

### Log Dosyalarını Kontrol Etme

```bash
# Error log
tail -n 50 ~/logs/username.pythonanywhere.com.error.log

# Server log
tail -n 50 ~/logs/username.pythonanywhere.com.server.log
```

## 🔄 Güncelleme İşlemleri

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

## ⚠️ Önemli Notlar

### Ücretsiz Hesap Sınırlamaları

- Sadece 1 web app
- Sınırlı CPU süresi
- Sınırlı disk alanı
- Dışarıdan erişim sınırlı (sadece belirli saatlerde)

### Güvenlik

- `DEBUG=False` olarak ayarlayın
- `SECRET_KEY`'i asla paylaşmayın
- `.env` dosyasını Git'e eklemeyin (zaten .gitignore'da)

### Performans

- SQLite production için ideal değildir
- Büyük dosyalar için cloud storage (AWS S3, Cloudinary vb.) kullanmayı düşünün

### Domain

- Ücretsiz hesapta sadece `username.pythonanywhere.com` kullanılabilir
- Özel domain için ücretli hesap gerekir

## 📚 Ek Kaynaklar

- PythonAnywhere Dokümantasyonu: https://help.pythonanywhere.com/
- Django Deployment: https://docs.djangoproject.com/en/stable/howto/deployment/
- `ALLOWED_HOSTS_REHBERI.md` - ALLOWED_HOSTS ayarlama rehberi
- `PYTHONANYWHERE_WSGI_TEMPLATE.py` - WSGI yapılandırma şablonu

## ✅ Deployment Kontrol Listesi

- [ ] PythonAnywhere hesabı oluşturuldu
- [ ] Proje yüklendi (GitHub veya manuel)
- [ ] Virtual environment oluşturuldu ve aktif edildi
- [ ] Bağımlılıklar yüklendi (`pip install -r requirements.txt`)
- [ ] `.env` dosyası oluşturuldu ve dolduruldu
- [ ] Veritabanı migration'ları uygulandı (`python manage.py migrate`)
- [ ] Superuser oluşturuldu (`python manage.py createsuperuser`)
- [ ] Static files toplandı (`python manage.py collectstatic`)
- [ ] Web app oluşturuldu ve yapılandırıldı
- [ ] WSGI dosyası yapılandırıldı
- [ ] Static ve media files mapping'leri eklendi
- [ ] Web app reload edildi
- [ ] Site test edildi ve çalışıyor

