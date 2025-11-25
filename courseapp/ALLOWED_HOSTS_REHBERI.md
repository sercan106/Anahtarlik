# ALLOWED_HOSTS Nasıl Bulunur ve Ayarlanır?

## 1. PythonAnywhere Kullanıcı Adınızı Bulun

PythonAnywhere konsolunda şu komutu çalıştırın:

```bash
whoami
```

Çıkan sonuç sizin kullanıcı adınızdır. Örnek: `serco`

## 2. Domain'inizi Bulun

PythonAnywhere dashboard'undan **"Web"** sekmesine gidin. Orada domain'iniz görünecektir:

- Ücretsiz hesap için: `kullanıcıadı.pythonanywhere.com`
- Örnek: `serco.pythonanywhere.com`

## 3. .env Dosyasında Ayarlayın

`.env` dosyasında `ALLOWED_HOSTS` şu şekilde olmalı:

```env
ALLOWED_HOSTS=serco.pythonanywhere.com
```

**Önemli:** 
- Sadece domain adını yazın, `https://` veya `/` eklemeyin
- Virgülle ayırarak birden fazla domain ekleyebilirsiniz
- Boşluk bırakmayın

## 4. Örnekler

### Tek domain:
```env
ALLOWED_HOSTS=serco.pythonanywhere.com
```

### Birden fazla domain:
```env
ALLOWED_HOSTS=serco.pythonanywhere.com,www.serco.pythonanywhere.com
```

### Localhost ile birlikte (geliştirme için):
```env
ALLOWED_HOSTS=serco.pythonanywhere.com,127.0.0.1,localhost
```

## 5. Doğrulama

`.env` dosyasını kaydettikten sonra, Django'nun ayarı okuduğunu kontrol edin:

```bash
cd ~/Anahtarlik/courseapp
python manage.py shell
```

Python shell'de:
```python
from django.conf import settings
print(settings.ALLOWED_HOSTS)
```

Çıktı şöyle olmalı:
```
['serco.pythonanywhere.com']
```

## 6. Hata Alırsanız

Eğer "DisallowedHost" hatası alırsanız:

1. `.env` dosyasındaki `ALLOWED_HOSTS` değerini kontrol edin
2. Web app'i reload edin (PythonAnywhere Web sekmesinden)
3. Log dosyalarını kontrol edin:
   ```bash
   tail -n 50 ~/logs/serco.pythonanywhere.com.error.log
   ```

## 7. Web App Domain'i ile Uyumlu Olmalı

**ÇOK ÖNEMLİ:** `.env` dosyasındaki `ALLOWED_HOSTS` değeri, PythonAnywhere Web app'inizin domain'i ile **TAMAMEN AYNI** olmalıdır!

PythonAnywhere Web sekmesinde domain şöyle görünüyorsa:
```
serco.pythonanywhere.com
```

`.env` dosyasında da aynen şöyle olmalı:
```env
ALLOWED_HOSTS=serco.pythonanywhere.com
```



