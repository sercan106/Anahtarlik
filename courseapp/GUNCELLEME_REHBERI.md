# 🔄 PythonAnywhere Dosya Güncelleme Rehberi

Bu rehber, PythonAnywhere'de zaten kurulu olan projenizi GitHub'dan güncellemek için adım adım talimatlar içerir.

## 📋 Ön Koşullar

- ✅ PythonAnywhere hesabınız var (serco.pythonanywhere.com)
- ✅ Proje zaten kurulu
- ✅ Sanal ortam (venv) hazır
- ✅ GitHub'da güncel kodlarınız var

## 🚀 Adım Adım Güncelleme

### Adım 1: Bash Konsolu Açın

1. PythonAnywhere dashboard'undan **"Consoles"** sekmesine gidin
2. **"Bash"** konsolu açın (veya mevcut bir konsolu kullanın)

### Adım 2: Proje Dizinine Gidin

```bash
cd ~/Anahtarlik/courseapp
```

**Not:** Eğer projeniz farklı bir dizindeyse, o dizine gidin.

### Adım 3: Sanal Ortamı Aktif Edin

```bash
source venv/bin/activate
```

**veya** virtualenvwrapper kullanıyorsanız:

```bash
source ~/.virtualenvs/venv/bin/activate
```

Aktif olduğunda komut satırının başında `(venv)` görünecek.

### Adım 4: GitHub'dan Güncellemeleri Çekin

```bash
git pull origin master
```

**veya** main branch kullanıyorsanız:

```bash
git pull origin main
```

Bu komut GitHub'daki son değişiklikleri indirecek.

### Adım 5: Yeni Bağımlılıkları Yükleyin (Gerekirse)

```bash
pip install -r requirements.txt
```

Bu komut yeni eklenen paketleri yükleyecek.

### Adım 6: Veritabanı Migration'larını Uygulayın

```bash
python manage.py migrate
```

Bu komut yeni veritabanı değişikliklerini uygulayacak.

### Adım 7: Static Dosyaları Güncelleyin

```bash
python manage.py collectstatic --noinput
```

Bu komut static dosyaları `staticfiles/` klasörüne toplayacak.

### Adım 8: Web App'i Yeniden Yükleyin

1. PythonAnywhere dashboard'undan **"Web"** sekmesine gidin
2. Yeşil **"Reload"** butonuna tıklayın

Bu işlem web uygulamanızı yeniden başlatacak ve güncellemeler aktif olacak.

## ✅ Tamamlandı!

Artık siteniz güncel! Tarayıcıda kontrol edin:
```
https://serco.pythonanywhere.com
```

## 📝 Hızlı Komut Özeti

Tüm işlemleri tek seferde yapmak için:

```bash
cd ~/Anahtarlik/courseapp
source venv/bin/activate
git pull origin master
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Sonra Web sekmesinden **Reload** butonuna tıklayın.

## ⚠️ Önemli Notlar

1. **Git pull yapmadan önce** değişikliklerinizi commit ettiğinizden emin olun
2. **Migration hataları** alırsanız, önce mevcut migration'ları kontrol edin
3. **Static files** her güncellemeden sonra mutlaka toplayın
4. **Reload** butonuna tıklamayı unutmayın, aksi halde değişiklikler aktif olmaz

## 🐛 Sorun Giderme

### "git pull" hatası alırsanız:
- Git repository'nin doğru yapılandırıldığından emin olun
- `git remote -v` ile remote repository'yi kontrol edin

### Migration hatası alırsanız:
- `python manage.py showmigrations` ile durumu kontrol edin
- Gerekirse migration'ları manuel olarak uygulayın

### Static files hatası:
- `staticfiles/` klasörünün yazılabilir olduğundan emin olun
- Disk kotanızı kontrol edin (48% kullanılıyor - yeterli)

## 🔄 Düzenli Güncelleme İçin

Her güncellemede yukarıdaki adımları tekrarlayın. İşlem genellikle 2-3 dakika sürer.

