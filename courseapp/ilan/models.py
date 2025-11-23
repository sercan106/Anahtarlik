from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# İlan türleri
ILAN_SAHIPLENDIRME = 'SAHIPLENDIRME'
ILAN_SATIS = 'SATIS'
ILAN_KAYIP = 'KAYIP'
ILAN_BULUNTU = 'BULUNTU'

ILAN_TUR_SECENEKLERI = [
    (ILAN_SAHIPLENDIRME, 'Sahiplendirme'),
    (ILAN_SATIS, 'Satış'),
    (ILAN_KAYIP, 'Kayıp'),
    (ILAN_BULUNTU, 'Buluntu'),
]


# Cinsiyet seçenekleri
CINSIYET_ERKEK = 'ERKEK'
CINSIYET_DISI = 'DISI'
CINSIYET_BILINMIYOR = 'BILINMIYOR'

CINSIYET_SECENEKLERI = [
    (CINSIYET_ERKEK, 'Erkek'),
    (CINSIYET_DISI, 'Dişi'),
    (CINSIYET_BILINMIYOR, 'Bilinmiyor'),
]

# Evet/Hayır seçenekleri
EVET_HAYIR_SECENEKLERI = [
    (True, 'Var'),
    (False, 'Yok'),
]


class HayvanProfili(models.Model):
    """Hayvan profili modeli - tüm kullanıcı tipleri için"""
    
    # Kullanıcı bilgileri
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hayvan_profilleri')
    evcil_hayvan = models.ForeignKey(
        'anahtarlik.EvcilHayvan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hayvan_profilleri',
        verbose_name="Evcil Hayvan"
    )
    
    # Temel bilgiler
    hayvan_adi = models.CharField(max_length=100, verbose_name="Hayvan Adı")
    tur = models.ForeignKey('anahtarlik.Tur', on_delete=models.CASCADE, related_name='hayvan_profilleri', verbose_name="Tür")
    irk = models.ForeignKey('anahtarlik.Irk', on_delete=models.CASCADE, related_name='hayvan_profilleri', verbose_name="Irk")
    dogum_tarihi = models.DateField(verbose_name="Doğum Tarihi", help_text="Hayvanın doğum tarihi")
    cinsiyet = models.CharField(max_length=20, choices=CINSIYET_SECENEKLERI, verbose_name="Cinsiyet")
    
    # Sağlık bilgileri
    asi_durumu = models.BooleanField(choices=EVET_HAYIR_SECENEKLERI, default=False, verbose_name="Aşı Durumu")
    ic_parazit = models.BooleanField(choices=EVET_HAYIR_SECENEKLERI, default=False, verbose_name="İç Parazit")
    dis_parazit = models.BooleanField(choices=EVET_HAYIR_SECENEKLERI, default=False, verbose_name="Dış Parazit")
    
    # Gönderim
    sehir_disi_gonderim = models.BooleanField(choices=EVET_HAYIR_SECENEKLERI, default=False, verbose_name="Şehir Dışına Gönderim")
    
    # Konum bilgileri
    il = models.ForeignKey('anahtarlik.Il', on_delete=models.CASCADE, related_name='hayvan_profilleri', verbose_name="İl")
    ilce = models.ForeignKey('anahtarlik.Ilce', on_delete=models.CASCADE, related_name='hayvan_profilleri', verbose_name="İlçe")
    mahalle = models.ForeignKey('anahtarlik.Mahalle', on_delete=models.SET_NULL, related_name='hayvan_profilleri', verbose_name="Mahalle", null=True, blank=True)
    mahalle_diger = models.CharField(max_length=200, blank=True, verbose_name="Mahalle (Manuel)", help_text="Mahalle listede yoksa buraya yazınız")
    
    # İletişim bilgileri (Snapshot)
    telefon = models.CharField(
        max_length=15, 
        blank=False,
        verbose_name="Telefon Numarası",
        help_text="İlan için iletişim telefon numarası (05XX XXX XX XX formatında)"
    )
    
    # Açıklama ve medya
    aciklama = models.TextField(verbose_name="Açıklama", blank=True)
    profil_fotografi = models.ImageField(upload_to='hayvan_profilleri/', verbose_name="Profil Fotoğrafı")
    
    # Sistem bilgileri
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    
    class Meta:
        verbose_name = "Hayvan Profili"
        verbose_name_plural = "Hayvan Profilleri"
        ordering = ['-olusturulma_tarihi']
    
    def yas_hesapla(self):
        """Doğum tarihinden yaş hesapla - Snapshot mantığı: sadece kendi dogum_tarihi'ne bak"""
        # İlan onaylandıktan sonra evcil_hayvan değişikliklerinden etkilenmemek için
        # sadece kendi dogum_tarihi'ne bak (evcil_hayvan'a bakma)
        if not self.dogum_tarihi:
            return "Bilinmiyor"
        
        from datetime import date
        today = date.today()
        birth_date = self.dogum_tarihi
        
        # Yaş hesapla
        age_years = today.year - birth_date.year
        age_months = today.month - birth_date.month
        
        # Ay hesaplaması için düzeltme
        if age_months < 0:
            age_years -= 1
            age_months += 12
        
        # Yaş formatını belirle
        if age_years == 0:
            if age_months == 0:
                return "Yeni doğan"
            elif age_months == 1:
                return "1 Aylık"
            else:
                return f"{age_months} Aylık"
        elif age_years == 1:
            if age_months == 0:
                return "1 Yaşında"
            else:
                return f"1 Yaş {age_months} Aylık"
        else:
            if age_months == 0:
                return f"{age_years} Yaşında"
            else:
                return f"{age_years} Yaş {age_months} Aylık"
    
    @property
    def yas(self):
        """Yaş property - geriye dönük uyumluluk için"""
        return self.yas_hesapla()
    
    def __str__(self):
        return f"{self.hayvan_adi} ({self.tur.ad}) - {self.kullanici.username}"


class HayvanResmi(models.Model):
    """Hayvan profili için çoklu resim yükleme (maksimum 3 resim)"""
    
    hayvan_profili = models.ForeignKey(HayvanProfili, on_delete=models.CASCADE, related_name='resimler')
    resim = models.ImageField(upload_to='hayvan_resimleri/', verbose_name="Resim")
    sira = models.PositiveIntegerField(default=0, verbose_name="Sıra")
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Hayvan Resmi"
        verbose_name_plural = "Hayvan Resimleri"
        ordering = ['sira', 'olusturulma_tarihi']
    
    def __str__(self):
        return f"{self.hayvan_profili.hayvan_adi} - Resim {self.sira}"
    
    def save(self, *args, **kwargs):
        # Maksimum 3 resim kontrolü
        if self.hayvan_profili and self.hayvan_profili.resimler.count() >= 3:
            raise ValueError("Bir hayvan profili için maksimum 3 resim yüklenebilir.")
        super().save(*args, **kwargs)


class Ilan(models.Model):
    """İlan modeli"""
    
    # Hayvan profili bağlantısı
    hayvan_profili = models.ForeignKey(HayvanProfili, on_delete=models.CASCADE, related_name='ilanlar')
    
    # İlan bilgileri
    baslik = models.CharField(max_length=200, verbose_name="Başlık")
    ilan_turu = models.CharField(max_length=20, choices=ILAN_TUR_SECENEKLERI, verbose_name="İlan Türü")
    aciklama = models.TextField(verbose_name="Açıklama", blank=True)
    
    # Fiyat (sadece satış ilanları için)
    fiyat = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Fiyat (TL)")
    
    # Öne çıkarma
    onemli_mi = models.BooleanField(default=False, verbose_name="Öne Çıkarılsın mı?")
    
    # Durum
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    onaylandi = models.BooleanField(default=False, verbose_name="Onaylandı")
    
    # Tarihler
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    bitis_tarihi = models.DateTimeField(verbose_name="Bitiş Tarihi")
    
    # İstatistikler
    goruntulenme_sayisi = models.PositiveIntegerField(default=0, verbose_name="Görüntülenme Sayısı")
    favori_sayisi = models.PositiveIntegerField(default=0, verbose_name="Favori Sayısı")
    
    class Meta:
        verbose_name = "İlan"
        verbose_name_plural = "İlanlar"
        ordering = ['-onemli_mi', '-olusturulma_tarihi']
    
    def __str__(self):
        return f"{self.baslik} - {self.get_ilan_turu_display()}"
    
    def save(self, *args, **kwargs):
        reset_timer = False
        
        if self.pk:
            previous = Ilan.objects.filter(pk=self.pk).only('onaylandi').first()
            if previous and not previous.onaylandi and self.onaylandi:
                # Admin onayından sonra süre başlıyor
                reset_timer = True
        else:
            if self.onaylandi:
                # Yeni ilan onaylı olarak oluşturuluyorsa
                reset_timer = True
        
        if not self.bitis_tarihi or reset_timer:
            # Admin onayından sonra 30 günlük süre başlar
            self.bitis_tarihi = timezone.now() + timedelta(days=30)
        
        # Süresi dolmuş ilanları otomatik pasif et
        if self.bitis_tarihi and timezone.now() > self.bitis_tarihi:
            self.aktif = False
        
        # İlan onaylandığında HayvanProfili'ni dondur (snapshot)
        hayvan_profili_dondur = False
        if self.pk:
            previous = Ilan.objects.filter(pk=self.pk).only('onaylandi').first()
            if previous and not previous.onaylandi and self.onaylandi:
                hayvan_profili_dondur = True
        else:
            if self.onaylandi:
                hayvan_profili_dondur = True
        
        super().save(*args, **kwargs)
        
        # İlan onaylandığında HayvanProfili'ni dondur (evcil_hayvan bağlantısını kaldır)
        # NOT: Yeni ilanlar için evcil_hayvan zaten None (snapshot alındığı anda kaldırılıyor)
        # Bu kod eski ilanlar için güvenlik amacıyla bırakıldı
        if hayvan_profili_dondur and self.hayvan_profili:
            # EvcilHayvan bağlantısını kaldır - snapshot olarak kalacak
            if self.hayvan_profili.evcil_hayvan:
                self.hayvan_profili.evcil_hayvan = None
                self.hayvan_profili.save(update_fields=['evcil_hayvan'])
    
    @property
    def kalan_sure(self):
        """Kalan süreyi hesapla"""
        if self.bitis_tarihi:
            kalan = self.bitis_tarihi - timezone.now()
            if kalan.total_seconds() > 0:
                return kalan
        return None
    
    @property
    def süresi_doldu_mu(self):
        """İlan süresi doldu mu?"""
        return self.bitis_tarihi and timezone.now() > self.bitis_tarihi


class IlanKategori(models.Model):
    """İlan kategorileri (Köpek, Kedi, vb.)"""
    
    ad = models.CharField(max_length=100, unique=True, verbose_name="Kategori Adı")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    
    class Meta:
        verbose_name = "İlan Kategorisi"
        verbose_name_plural = "İlan Kategorileri"
        ordering = ['ad']
    
    def __str__(self):
        return self.ad


class KrediHareketi(models.Model):
    """Kredi hareketleri logu"""
    
    HAREKET_PROFIL_OLUSTURMA = 'PROFIL_OLUSTURMA'
    HAREKET_ILAN_VERME = 'ILAN_VERME'
    HAREKET_ONEMLI_ILAN = 'ONEMLI_ILAN'
    HAREKET_BAKIYE_EKLEME = 'BAKIYE_EKLEME'
    HAREKET_ETIKET_SATIS = 'ETIKET_SATIS'
    HAREKET_ETIKET_AKTIVASYON = 'ETIKET_AKTIVASYON'
    HAREKET_SATIN_ALMA = 'SATIN_ALMA'
    
    HAREKET_SECENEKLERI = [
        (HAREKET_PROFIL_OLUSTURMA, 'Profil Oluşturma'),
        (HAREKET_ILAN_VERME, 'İlan Verme'),
        (HAREKET_ONEMLI_ILAN, 'Önemli İlan'),
        (HAREKET_BAKIYE_EKLEME, 'Bakiye Ekleme'),
        (HAREKET_ETIKET_SATIS, 'Etiket Satışı'),
        (HAREKET_ETIKET_AKTIVASYON, 'Etiket Aktivasyonu'),
        (HAREKET_SATIN_ALMA, 'Kredi Satın Alma'),
    ]
    
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kredi_hareketleri')
    hareket_turu = models.CharField(max_length=20, choices=HAREKET_SECENEKLERI, verbose_name="Hareket Türü")
    miktar = models.IntegerField(verbose_name="Miktar")  # Pozitif: ekleme, Negatif: harcama
    aciklama = models.CharField(max_length=200, verbose_name="Açıklama")
    tarih = models.DateTimeField(auto_now_add=True, verbose_name="Tarih")
    
    # İlgili nesneler (opsiyonel)
    hayvan_profili = models.ForeignKey(HayvanProfili, on_delete=models.SET_NULL, null=True, blank=True)
    ilan = models.ForeignKey(Ilan, on_delete=models.SET_NULL, null=True, blank=True)
    etiket = models.ForeignKey('etiket.Etiket', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Kredi Hareketi"
        verbose_name_plural = "Kredi Hareketleri"
        ordering = ['-tarih']
    
    def __str__(self):
        return f"{self.kullanici.username} - {self.get_hareket_turu_display()} ({self.miktar:+d})"


class KrediPaketi(models.Model):
    """Kredi satın alma paketleri"""
    
    ad = models.CharField(max_length=100, verbose_name="Paket Adı")
    aciklama = models.TextField(verbose_name="Açıklama", blank=True)
    kredi_adet = models.IntegerField(verbose_name="Kredi Adedi")
    fiyat = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Fiyat (TL)")
    
    # Görünürlük ve sıralama
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    sira = models.IntegerField(default=0, verbose_name="Sıra")
    
    # Öne çıkarma
    one_cikan = models.BooleanField(default=False, verbose_name="Öne Çıkan Paket")
    etiket = models.CharField(max_length=50, blank=True, verbose_name="Etiket", help_text="Örn: 'En Popüler', 'En Avantajlı'")
    
    # Tarih bilgileri
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")
    guncelleme_tarihi = models.DateTimeField(auto_now=True, verbose_name="Güncelleme Tarihi")
    
    class Meta:
        verbose_name = "Kredi Paketi"
        verbose_name_plural = "Kredi Paketleri"
        ordering = ['sira', 'fiyat']
    
    def __str__(self):
        return f"{self.ad} - {self.kredi_adet} Kredi (₺{self.fiyat})"
    
    def birim_fiyat(self):
        """Kredi başına düşen fiyat"""
        if self.kredi_adet > 0:
            return float(self.fiyat) / self.kredi_adet
        return 0
    
    birim_fiyat.short_description = "Kredi Başına Fiyat"