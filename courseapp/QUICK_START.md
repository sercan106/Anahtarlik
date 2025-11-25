# 🚀 PythonAnywhere Hızlı Başlangıç Rehberi

## ⚡ Hızlı Kurulum (5 Dakika)

### 1. PythonAnywhere'de Projeyi Yükleyin

```bash
cd ~
git clone https://github.com/username/repo-name.git courseapp
cd courseapp
```

### 2. Virtual Environment ve Bağımlılıklar

```bash
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. .env Dosyası Oluşturun

```bash
nano .env
```

Aşağıdaki içeriği ekleyin (kendi değerlerinizle değiştirin):

```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=username.pythonanywhere.com
SITE_URL=https://username.pythonanywhere.com
```

**SECRET_KEY oluşturma:**
```bash
python manage.py shell
>>> from django.core.management.utils import get_random_secret_key
>>> print(get_random_secret_key())
```

### 4. Veritabanı ve Static Files

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

### 5. Web App Yapılandırması

1. PythonAnywhere **Web** sekmesine gidin
2. **Add a new web app** → Domain seçin → **Manual configuration** → Python 3.10
3. **WSGI configuration file** linkine tıklayın
4. `PYTHONANYWHERE_WSGI_TEMPLATE.py` dosyasındaki kodu kopyalayın (username'i değiştirin)
5. **Static files** bölümüne gidin:
   - `/static/` → `/home/username/courseapp/staticfiles`
   - `/media/` → `/home/username/courseapp/media`
6. **Reload** butonuna tıklayın

### 6. Test Edin

Tarayıcıda: `https://username.pythonanywhere.com`

## 📚 Detaylı Dokümantasyon

- **DEPLOYMENT_README.md** - Tam deployment rehberi
- **DEPLOYMENT_SUMMARY.md** - Hazırlık özeti
- **DEPLOYMENT_CHECKLIST.md** - Kontrol listesi
- **ALLOWED_HOSTS_REHBERI.md** - ALLOWED_HOSTS ayarlama

## ⚠️ Önemli Notlar

1. `username` kısmını kendi PythonAnywhere kullanıcı adınızla değiştirin
2. `SECRET_KEY` için güçlü bir değer kullanın
3. Production'da `DEBUG=False` olmalı
4. Her güncellemeden sonra `collectstatic` çalıştırın

## 🆘 Sorun mu Yaşıyorsunuz?

- Log dosyalarını kontrol edin: `tail -n 50 ~/logs/username.pythonanywhere.com.error.log`
- **DEPLOYMENT_README.md** dosyasındaki "Sorun Giderme" bölümüne bakın

