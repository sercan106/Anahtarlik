# Cursor Rules - Anahtarlık Projesi

Bu klasör, Cursor AI için proje kurallarını içerir.

## 📁 Dosya Yapısı

```
.cursor/
└── rules/
    ├── anahtarlik-kurallari.md  ← Ana kurallar dosyası
    └── kurallar.mdc             ← Alternatif format
```

## ✅ Kuralların Aktif Edilmesi

### Otomatik Okuma
Cursor, `.cursor/rules/` klasöründeki `.md` ve `.mdc` dosyalarını otomatik olarak okur.

### Manuel Ekleme (Gerekirse)
1. Cursor Settings açın (`Ctrl + ,`)
2. "Rules" veya "Cursor Rules" bölümünü bulun
3. "Add Rule File" butonuna tıklayın
4. `.cursor/rules/anahtarlik-kurallari.md` dosyasını seçin

### Test Etme
Kuralların okunup okunmadığını test etmek için:
- Cursor'a bir görev verin (örn: "Yeni bir Django modeli oluştur")
- Kurallar okunuyorsa, AI önce görevi anlayacak, özet sunacak ve onay bekleyecektir

## 📝 Kurallar İçeriği

Ana kurallar dosyası şunları içerir:
- Django Best Practices
- Güvenlik Kuralları
- Frontend/Template Kuralları
- Proje Özel Kuralları
- Kod Üretim Talimatları

## 🔄 Güncelleme

Kuralları güncellediğinizde:
1. `.cursor/rules/anahtarlik-kurallari.md` dosyasını düzenleyin
2. Cursor'ı yeniden başlatın (gerekirse)
3. Settings'den dosyanın hala seçili olduğunu kontrol edin

