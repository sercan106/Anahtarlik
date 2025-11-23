# veteriner/models.py

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone

# Ödeme modeli (kurum)
ODEME_PESIN = 'PESIN'
ODEME_KONSINYE = 'KONSINYE'
ODEME_SECENEKLERI = [
    (ODEME_PESIN, 'Peşin Ödeme'),
    (ODEME_KONSINYE, 'Konsinye (Numune) Ödeme'),
]

# Kargo şirketi
KARGO_ARAS = 'ARAS'
KARGO_YURTICI = 'YURTICI'
KARGO_MNG = 'MNG'
KARGO_DHL = 'DHL'
KARGO_SECENEKLERI = [
    (KARGO_ARAS, 'Aras Kargo'),
    (KARGO_YURTICI, 'Yurtiçi Kargo'),
    (KARGO_MNG, 'MNG Kargo'),
    (KARGO_DHL, 'DHL'),
]

# Ödeme durumu (sipariş)
OD_BEKE = 'BEKLEMEDE'
OD_ALIN = 'ALINDI'
OD_IADE = 'IADE'
OD_MUAF = 'MUAF'  # Numune vb. için
ODEME_DURUM_SEC = [
    (OD_BEKE, 'Beklemede'),
    (OD_ALIN, 'Alındı'),
    (OD_IADE, 'İade Edildi'),
    (OD_MUAF, 'Muaf (Numune)'),
]

# Ödeme yöntemi
OY_NAKIT = 'NAKIT'
OY_EFT = 'EFT'
OY_KREDI = 'KREDI'
OY_POS = 'POS'
OY_DIGER = 'DIGER'
ODEME_YONTEM_SEC = [
    (OY_NAKIT, 'Nakit'),
    (OY_EFT, 'EFT/Havale'),
    (OY_KREDI, 'Kredi Kartı'),
    (OY_POS, 'Pos/Link'),
    (OY_DIGER, 'Diğer'),
]

# Hizmet türleri
HIZMET_GENEL = 'GENEL'
HIZMET_ACIL = 'ACIL'
HIZMET_OPERASYON = 'OPERASYON'
HIZMET_KONTROL = 'KONTROL'
HIZMET_TUR_SECENEKLERI = [
    (HIZMET_GENEL, 'Genel Muayene'),
    (HIZMET_ACIL, 'Acil Müdahale'),
    (HIZMET_OPERASYON, 'Operasyon'),
    (HIZMET_KONTROL, 'Kontrol Muayenesi'),
]

# Randevu durumları
RANDEVU_BEKLENIYOR = 'BEKLENIYOR'
RANDEVU_ONAYLANDI = 'ONAYLANDI'
RANDEVU_IPTAL = 'IPTAL'
RANDEVU_TAMAMLANDI = 'TAMAMLANDI'
RANDEVU_DURUM_SECENEKLERI = [
    (RANDEVU_BEKLENIYOR, 'Bekleniyor'),
    (RANDEVU_ONAYLANDI, 'Onaylandı'),
    (RANDEVU_IPTAL, 'İptal'),
    (RANDEVU_TAMAMLANDI, 'Tamamlandı'),
]


class Veteriner(models.Model):
    ad = models.CharField(max_length=150)
    telefon = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    il = models.ForeignKey('anahtarlik.Il', on_delete=models.CASCADE, related_name='veterinerler', null=True, blank=True)
    ilce = models.ForeignKey('anahtarlik.Ilce', on_delete=models.CASCADE, related_name='veterinerler', null=True, blank=True)
    mahalle = models.ForeignKey('anahtarlik.Mahalle', on_delete=models.CASCADE, related_name='veterinerler', null=True, blank=True)
    mahalle_diger = models.CharField(max_length=200, blank=True, verbose_name="Mahalle (Manuel)", help_text="Mahalle listede yoksa buraya yazınız")
    adres_detay = models.TextField(blank=True)

    kullanici = models.OneToOneField(
        User, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='veteriner_profili'
    )

    aktif = models.BooleanField(default=True)
    olusturulma = models.DateTimeField(auto_now_add=True)
    odeme_modeli = models.CharField(max_length=10, choices=ODEME_SECENEKLERI, default=ODEME_PESIN)
    
    # İlk giriş şifre değiştirme kontrolü
    ilk_giris_sifre_degistirildi = models.BooleanField(
        default=False,
        verbose_name="İlk Giriş Şifre Değiştirildi",
        help_text="Admin tarafından oluşturulan kullanıcının ilk girişte şifresini değiştirdiğini belirtir."
    )

    # sayaçlar
    tahsis_sayisi = models.PositiveIntegerField(default=0)
    satis_sayisi = models.PositiveIntegerField(default=0)

    # Yeni alanlar - Hizmet bilgileri
    uzmanlik_alanlari = models.TextField(blank=True, help_text="Uzmanlık alanları (virgülle ayırın)")
    calisma_saatleri = models.TextField(blank=True, help_text="Çalışma saatleri")
    acil_hizmet = models.BooleanField(default=False, help_text="Acil hizmet veriyor mu?")
    evde_hizmet = models.BooleanField(default=False, help_text="Evde hizmet veriyor mu?")
    hizmet_verilen_ilceler = models.TextField(blank=True, help_text="Hizmet verilen ilçeler (virgülle ayırın)")
    
    # İletişim ve sosyal medya
    website = models.URLField(blank=True)
    instagram = models.CharField(max_length=100, blank=True)
    facebook = models.CharField(max_length=100, blank=True)
    twitter = models.CharField(max_length=100, blank=True)
    linkedin = models.CharField(max_length=100, blank=True)
    youtube = models.CharField(max_length=100, blank=True)
    
    # Web görünüm ayarları
    tema = models.CharField(max_length=20, blank=True, help_text="Tema adı (örn: default, pastel)")
    birincil_renk = models.CharField(max_length=7, blank=True, help_text="#667eea formatında HEX renk")
    logo = models.ImageField(upload_to='veteriner_web/', blank=True, null=True, help_text="Logo")
    cta_metin = models.CharField(max_length=50, blank=True, help_text="Çağrı butonu metni (örn: Randevu Alın)")
    cta_link = models.URLField(blank=True, help_text="Çağrı butonu linki (örn: randevu ya da WhatsApp linki)")
    whatsapp = models.CharField(max_length=20, blank=True, help_text="WhatsApp numarası (örn: 905551112233)")
    
    # Bölüm görünürlükleri
    goster_sosyal = models.BooleanField(default=True)
    goster_hizmetler = models.BooleanField(default=True)
    goster_calisma_saatleri = models.BooleanField(default=True)
    goster_galeri = models.BooleanField(default=True)
    
    # Çalışma saatleri
    pazartesi_baslangic = models.TimeField(blank=True, null=True, help_text="Pazartesi başlangıç saati")
    pazartesi_bitis = models.TimeField(blank=True, null=True, help_text="Pazartesi bitiş saati")
    pazartesi_kapali = models.BooleanField(default=False, help_text="Pazartesi kapalı mı?")
    
    sali_baslangic = models.TimeField(blank=True, null=True, help_text="Salı başlangıç saati")
    sali_bitis = models.TimeField(blank=True, null=True, help_text="Salı bitiş saati")
    sali_kapali = models.BooleanField(default=False, help_text="Salı kapalı mı?")
    
    carsamba_baslangic = models.TimeField(blank=True, null=True, help_text="Çarşamba başlangıç saati")
    carsamba_bitis = models.TimeField(blank=True, null=True, help_text="Çarşamba bitiş saati")
    carsamba_kapali = models.BooleanField(default=False, help_text="Çarşamba kapalı mı?")
    
    persembe_baslangic = models.TimeField(blank=True, null=True, help_text="Perşembe başlangıç saati")
    persembe_bitis = models.TimeField(blank=True, null=True, help_text="Perşembe bitiş saati")
    persembe_kapali = models.BooleanField(default=False, help_text="Perşembe kapalı mı?")
    
    cuma_baslangic = models.TimeField(blank=True, null=True, help_text="Cuma başlangıç saati")
    cuma_bitis = models.TimeField(blank=True, null=True, help_text="Cuma bitiş saati")
    cuma_kapali = models.BooleanField(default=False, help_text="Cuma kapalı mı?")
    
    cumartesi_baslangic = models.TimeField(blank=True, null=True, help_text="Cumartesi başlangıç saati")
    cumartesi_bitis = models.TimeField(blank=True, null=True, help_text="Cumartesi bitiş saati")
    cumartesi_kapali = models.BooleanField(default=False, help_text="Cumartesi kapalı mı?")
    
    pazar_baslangic = models.TimeField(blank=True, null=True, help_text="Pazar başlangıç saati")
    pazar_bitis = models.TimeField(blank=True, null=True, help_text="Pazar bitiş saati")
    pazar_kapali = models.BooleanField(default=True, help_text="Pazar kapalı mı?")
    
    # Değerlendirme
    ortalama_puan = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    degerlendirme_sayisi = models.PositiveIntegerField(default=0)
    
    # Web sayfası alanları
    web_baslik = models.CharField(max_length=200, blank=True, help_text="Ana başlık (örn: Pati Veteriner Kliniği)")
    web_slogan = models.CharField(max_length=300, blank=True, help_text="Alt başlık/slogan (örn: Sevimli Dostlarınız İçin En İyi Bakım)")
    web_aciklama = models.TextField(blank=True, help_text="Hakkımızda metni")
    
    # Hizmetler (3 ana hizmet kartı)
    hizmet1_baslik = models.CharField(max_length=100, blank=True, default="Genel Muayene", help_text="1. Hizmet başlığı")
    hizmet1_aciklama = models.TextField(blank=True, default="Detaylı fiziksel muayene, teşhis ve sağlık kontrolü.", help_text="1. Hizmet açıklaması")
    hizmet1_icon = models.CharField(max_length=20, blank=True, default="🩺", help_text="1. Hizmet ikonu (emoji)")
    
    hizmet2_baslik = models.CharField(max_length=100, blank=True, default="Aşılama & Tedavi", help_text="2. Hizmet başlığı")
    hizmet2_aciklama = models.TextField(blank=True, default="Koruyucu aşı programları ve hastalık tedavileri.", help_text="2. Hizmet açıklaması")
    hizmet2_icon = models.CharField(max_length=20, blank=True, default="💉", help_text="2. Hizmet ikonu (emoji)")
    
    hizmet3_baslik = models.CharField(max_length=100, blank=True, default="Laboratuvar", help_text="3. Hizmet başlığı")
    hizmet3_aciklama = models.TextField(blank=True, default="Kan tahlili, röntgen, ultrason gibi teşhis yöntemleri.", help_text="3. Hizmet açıklaması")
    hizmet3_icon = models.CharField(max_length=20, blank=True, default="🔬", help_text="3. Hizmet ikonu (emoji)")
    
    # Görseller
    web_resim1 = models.ImageField(upload_to='veteriner_web/', blank=True, null=True, help_text="Ana görsel (Hakkımızda bölümü)")
    web_resim2 = models.ImageField(upload_to='veteriner_web/', blank=True, null=True, help_text="Galeri görseli 1")
    web_resim3 = models.ImageField(upload_to='veteriner_web/', blank=True, null=True, help_text="Galeri görseli 2")
    
    # SEO Alanları
    web_seo_baslik = models.CharField(max_length=70, blank=True, help_text="SEO başlık (max 70 karakter)")
    web_seo_aciklama = models.CharField(max_length=160, blank=True, help_text="SEO açıklama (max 160 karakter)")
    web_seo_anahtar_kelimeler = models.CharField(max_length=255, blank=True, help_text="SEO anahtar kelimeler (virgülle ayırın)")
    web_slug = models.SlugField(max_length=200, blank=True, unique=True, null=True, help_text="URL slug (otomatik oluşturulur)")
    
    # Durum
    web_aktif = models.BooleanField(default=False, help_text="Web sayfası aktif mi?")

    # ENLEM-BOYLAM YERINE KOMPOZIT ALAN
    konum_koordinat = models.CharField(
        max_length=40, blank=True, null=True,
        verbose_name="Koordinat",
        help_text="Google Maps formatında: 38.231952, 42.428070"
    )

    def __str__(self):
        return self.ad
    
    def save(self, *args, **kwargs):
        # Slug oluştur (eğer yoksa)
        if not self.web_slug and self.ad:
            from django.utils.text import slugify
            # Türkçe karakterleri İngilizce karşılıklarına çevir
            tr_map = str.maketrans('çğıöşüÇĞIÖŞÜ', 'cgiosuCGIOSU')
            temiz_ad = self.ad.translate(tr_map)
            base_slug = slugify(temiz_ad, allow_unicode=False)
            slug = base_slug
            counter = 1
            while Veteriner.objects.filter(web_slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.web_slug = slug
        
        # SEO başlık ve açıklama otomatik oluştur (eğer yoksa)
        if not self.web_seo_baslik and self.web_baslik:
            self.web_seo_baslik = f"{self.web_baslik} | Veteriner"[:70]
        
        if not self.web_seo_aciklama and self.web_aciklama:
            self.web_seo_aciklama = self.web_aciklama[:160]
        
        super().save(*args, **kwargs)

    @property
    def kalan_envanter(self) -> int:
        return max((self.tahsis_sayisi or 0) - (self.satis_sayisi or 0), 0)
    
    @property
    def danisman_sahip_sayisi(self) -> int:
        """Danışman olduğu sahip sayısı"""
        return self.danisman_oldugu_sahipler.count()
    
    @property
    def dinamik_kapasite(self) -> int:
        """Dinamik kapasite hesapla - Sadece satış başarısına göre"""
        # Temel kapasite
        base_capacity = 50
        
        # Satış başarısı bonusu (daha agresif)
        satis_sayisi = self.satis_sayisi or 0
        if satis_sayisi >= 100:
            satis_bonus = 80  # 100+ satış
        elif satis_sayisi >= 50:
            satis_bonus = 60  # 50-99 satış
        elif satis_sayisi >= 25:
            satis_bonus = 40  # 25-49 satış
        elif satis_sayisi >= 10:
            satis_bonus = 25  # 10-24 satış
        elif satis_sayisi >= 5:
            satis_bonus = 15  # 5-9 satış
        elif satis_sayisi >= 1:
            satis_bonus = 5   # 1-4 satış
        else:
            satis_bonus = 0   # 0 satış
        
        # İlçe içi yüzde bonusu
        yuzde_bonus = 0
        try:
            yuzde_obj = VeterinerYuzde.objects.filter(
                veteriner=self,
                ilce=self.ilce
            ).first()
            if yuzde_obj:
                # Yüzde 20'den fazlaysa bonus
                if yuzde_obj.yuzde >= 20:
                    yuzde_bonus = 30
                elif yuzde_obj.yuzde >= 10:
                    yuzde_bonus = 20
                elif yuzde_obj.yuzde >= 5:
                    yuzde_bonus = 10
        except:
            pass  # Hata durumunda yuzde_bonus = 0 kalır
        
        # Toplam kapasite hesapla
        total_capacity = base_capacity + satis_bonus + yuzde_bonus
        
        # Minimum 30, maksimum 200
        return max(30, min(200, total_capacity))
    
    @property
    def kapasite_durumu(self) -> str:
        """Kapasite durumu - Dinamik kapasiteye göre"""
        max_capacity = self.dinamik_kapasite
        current = self.danisman_sahip_sayisi
        
        if current >= max_capacity:
            return "Dolu"
        elif current >= max_capacity * 0.8:
            return "Doluya Yakın"
        elif current >= max_capacity * 0.5:
            return "Orta"
        else:
            return "Boş"
    
    @property
    def kapasite_yuzdesi(self) -> float:
        """Kapasite yüzdesi"""
        max_capacity = self.dinamik_kapasite
        current = self.danisman_sahip_sayisi
        return (current / max_capacity * 100) if max_capacity > 0 else 0
    
    @property
    def satis_basari_seviyesi(self) -> str:
        """Satış başarı seviyesi"""
        satis = self.satis_sayisi or 0
        
        if satis >= 100:
            return "🏆 Ustası"
        elif satis >= 50:
            return "🥇 Uzman"
        elif satis >= 25:
            return "🥈 Deneyimli"
        elif satis >= 10:
            return "🥉 Gelişen"
        elif satis >= 5:
            return "⭐ Başlangıç"
        else:
            return "🌱 Yeni"
    
    @property
    def aktif_randevular(self):
        return self.randevular.filter(durum__in=[RANDEVU_BEKLENIYOR, RANDEVU_ONAYLANDI])
    
    @property
    def bugun_randevular(self):
        return self.randevular.filter(
            tarih=timezone.now().date(),
            durum__in=[RANDEVU_ONAYLANDI, RANDEVU_TAMAMLANDI]
        )

    @property
    def mevcut_yuk(self):
        """O an danışmanı olan sahip sayısı (yük)!"""
        return self.danisman_oldugu_sahipler.count()

    def satis_sayisi_ilce(self, ilce=None):
        """Belirli bir ilçe için, aktif satış/adet (ilk aktivasyonu yapılanlar sayılır)."""
        if not ilce:
            return 0
        from etiket.models import Etiket
        return Etiket.objects.filter(satici_veteriner=self, kanal='VET', evcil_hayvan__sahip__ilce=ilce, aktif=True, first_activated_at__isnull=False).count()

    def satis_sayisi_il(self, il=None):
        """Belirli bir il için, aktif satış/adet."""
        if not il:
            return 0
        from etiket.models import Etiket
        return Etiket.objects.filter(satici_veteriner=self, kanal='VET', evcil_hayvan__sahip__il=il, aktif=True, first_activated_at__isnull=False).count()


class VeterinerHizmet(models.Model):
    """Veteriner hizmet tanımları"""
    veteriner = models.ForeignKey(Veteriner, on_delete=models.CASCADE, related_name='hizmetler')
    hizmet_adi = models.CharField(max_length=200)
    hizmet_turu = models.CharField(max_length=20, choices=HIZMET_TUR_SECENEKLERI)
    aciklama = models.TextField(blank=True)
    fiyat = models.DecimalField(max_digits=10, decimal_places=2)
    sure_dakika = models.PositiveIntegerField(help_text="Tahmini süre (dakika)")
    aktif = models.BooleanField(default=True)
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        verbose_name = "Veteriner Hizmeti"
        verbose_name_plural = "Veteriner Hizmetleri"
        ordering = ['hizmet_adi']

    def __str__(self):
        return f"{self.veteriner.ad} - {self.hizmet_adi}"


class Randevu(models.Model):
    """Veteriner randevu sistemi"""
    veteriner = models.ForeignKey(Veteriner, on_delete=models.CASCADE, related_name='randevular')
    hizmet = models.ForeignKey(VeterinerHizmet, on_delete=models.CASCADE, related_name='randevular')
    
    # Müşteri bilgileri
    musteri_adi = models.CharField(max_length=100)
    musteri_telefon = models.CharField(max_length=15)
    musteri_email = models.EmailField(blank=True, null=True)
    
    # Hayvan bilgileri
    hayvan_adi = models.CharField(max_length=100)
    hayvan_turu = models.CharField(max_length=50, blank=True)
    hayvan_yasi = models.CharField(max_length=20, blank=True)
    hayvan_cinsiyet = models.CharField(max_length=10, blank=True)
    sorun_aciklamasi = models.TextField(blank=True)
    
    # Randevu detayları
    tarih = models.DateField()
    saat = models.TimeField()
    durum = models.CharField(max_length=20, choices=RANDEVU_DURUM_SECENEKLERI, default=RANDEVU_BEKLENIYOR)
    notlar = models.TextField(blank=True, null=True)
    
    # Fiyatlandırma
    fiyat = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    odeme_durumu = models.CharField(max_length=20, choices=ODEME_DURUM_SEC, default=OD_BEKE)
    odeme_yontemi = models.CharField(max_length=10, choices=ODEME_YONTEM_SEC, blank=True)
    
    # Sistem bilgileri
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Randevu"
        verbose_name_plural = "Randevular"
        ordering = ['-tarih', '-saat']
        unique_together = ['veteriner', 'tarih', 'saat']

    def __str__(self):
        return f"{self.musteri_adi} - {self.hayvan_adi} ({self.tarih} {self.saat})"
    
    @property
    def randevu_tarihi_saati(self):
        return f"{self.tarih} {self.saat}"
    
    @property
    def gecmis_mi(self):
        from django.utils import timezone
        randevu_datetime = timezone.datetime.combine(self.tarih, self.saat)
        return randevu_datetime < timezone.now()


class VeterinerDegerlendirme(models.Model):
    """Veteriner değerlendirme sistemi"""
    veteriner = models.ForeignKey(Veteriner, on_delete=models.CASCADE, related_name='degerlendirmeler')
    randevu = models.ForeignKey(Randevu, on_delete=models.CASCADE, related_name='degerlendirme', null=True, blank=True)
    
    # Değerlendirme
    puan = models.PositiveIntegerField(validators=[MinValueValidator(1)], help_text="1-5 arası puan")
    yorum = models.TextField(blank=True)
    
    # Müşteri bilgileri
    musteri_adi = models.CharField(max_length=100)
    musteri_telefon = models.CharField(max_length=15, blank=True)
    
    # Sistem
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    aktif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Veteriner Değerlendirmesi"
        verbose_name_plural = "Veteriner Değerlendirmeleri"
        ordering = ['-olusturulma_tarihi']

    def __str__(self):
        return f"{self.veteriner.ad} - {self.puan}/5"


class VeterinerYuzde(models.Model):
    """Veteriner yüzde dağılım sistemi - İlçe bazlı danışman atama"""
    veteriner = models.ForeignKey(Veteriner, on_delete=models.CASCADE, related_name='yuzde_dagilimlari')
    ilce = models.ForeignKey('anahtarlik.Ilce', on_delete=models.CASCADE, related_name='veteriner_yuzdeleri')
    yuzde = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name="Yüzde")
    son_guncelleme = models.DateTimeField(auto_now=True, verbose_name="Son Güncelleme")
    
    class Meta:
        verbose_name = "Veteriner Yüzde Dağılımı"
        verbose_name_plural = "Veteriner Yüzde Dağılımları"
        unique_together = ['veteriner', 'ilce']
        ordering = ['-yuzde', 'veteriner__ad']
    
    def __str__(self):
        return f"{self.veteriner.ad} - {self.ilce.ad} (%{self.yuzde})"
    
    @classmethod
    def yuzde_guncelle(cls, ilce):
        """İlçe bazlı yüzde güncelleme - Sadece VET kanalı satışları"""
        from django.db.models import Sum
        from etiket.models import Etiket, KANAL_VET
        
        # İlçedeki aktif veterinerleri al
        veterinerler = Veteriner.objects.filter(ilce=ilce, aktif=True)
        
        if not veterinerler.exists():
            return
        
        # Her veterinerin VET kanalı satış sayısını hesapla
        veteriner_satislari = {}
        toplam_satis = 0
        
        for veteriner in veterinerler:
            # Bu veterinerin VET kanalı satış sayısı (aktif edilen künyeler)
            satis_sayisi = Etiket.objects.filter(
                satici_veteriner=veteriner,
                kanal=KANAL_VET,  # Sadece VET kanalı
                aktif=True
            ).count()
            
            veteriner_satislari[veteriner.id] = satis_sayisi
            toplam_satis += satis_sayisi
        
        # Yüzde hesapla ve kaydet
        for veteriner in veterinerler:
            satis_sayisi = veteriner_satislari.get(veteriner.id, 0)
            yuzde = (satis_sayisi / toplam_satis * 100) if toplam_satis > 0 else 0
            
            cls.objects.update_or_create(
                veteriner=veteriner,
                ilce=ilce,
                defaults={'yuzde': yuzde}
            )


class SiparisIstemi(models.Model):
    veteriner = models.ForeignKey(Veteriner, on_delete=models.CASCADE, related_name='siparis_istekleri')

    # iş kuralı: min 5
    talep_edilen_adet = models.PositiveIntegerField(default=5, validators=[MinValueValidator(5)])
    talep_tarihi = models.DateTimeField(auto_now_add=True)

    # Onay/kargo
    onaylandi = models.BooleanField(default=False)
    onay_tarihi = models.DateTimeField(null=True, blank=True)
    kargolandimi = models.BooleanField(default=False)
    kargo_tarihi = models.DateTimeField(null=True, blank=True)
    kargo_sirketi = models.CharField(max_length=20, choices=KARGO_SECENEKLERI, blank=True)
    kargo_takip_no = models.CharField(max_length=100, blank=True)

    # Gönderim adresi
    farkli_adres_kullan = models.BooleanField(default=False)
    il = models.ForeignKey('anahtarlik.Il', on_delete=models.CASCADE, related_name='siparis_istekleri', null=True, blank=True)
    ilce = models.ForeignKey('anahtarlik.Ilce', on_delete=models.CASCADE, related_name='siparis_istekleri', null=True, blank=True)
    adres_detay = models.TextField(blank=True)

    # Numune / Ödeme takibi
    numune_mi = models.BooleanField(default=False)
    odeme_durumu = models.CharField(max_length=12, choices=ODEME_DURUM_SEC, default=OD_BEKE)
    odeme_tutari = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    odeme_para_birimi = models.CharField(max_length=6, default='TRY')
    odeme_yontemi = models.CharField(max_length=10, choices=ODEME_YONTEM_SEC, blank=True)
    odeme_alinma_tarihi = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.veteriner.ad} - {self.talep_edilen_adet} adet"

    @property
    def gonderim_adresi(self) -> str:
        if self.farkli_adres_kullan and self.il and self.ilce and self.adres_detay:
            return f"{self.adres_detay}, {self.ilce}/{self.il}"
        v = self.veteriner
        return f"{v.adres_detay}, {v.ilce}/{v.il}".strip(", /")

    @property
    def odeme_alindi_mi(self) -> bool:
        return self.odeme_durumu == OD_ALIN or (self.numune_mi and self.odeme_durumu == OD_MUAF)

    def save(self, *args, **kwargs):
        # Önceki durumu kontrol et (onay ve kargo durumu değişimi için)
        old_onaylandi = False
        old_kargolandimi = False
        if self.pk:
            try:
                old_instance = SiparisIstemi.objects.get(pk=self.pk)
                old_onaylandi = old_instance.onaylandi
                old_kargolandimi = old_instance.kargolandimi
            except SiparisIstemi.DoesNotExist:
                pass
        
        # Ödeme alındı ise tarih otomatİk set
        if self.odeme_durumu == OD_ALIN and not self.odeme_alinma_tarihi:
            self.odeme_alinma_tarihi = timezone.now()
        # Numunede ödeme muaf ise sıfırla
        if self.numune_mi and self.odeme_durumu == OD_MUAF:
            self.odeme_tutari = None
            self.odeme_yontemi = ''
            self.odeme_alinma_tarihi = None
        
        # Sipariş onaylandıysa ve daha önce onaylanmamışsa etiket oluştur
        if self.onaylandi and not old_onaylandi:
            self.onay_tarihi = timezone.now()
            self._olustur_etiketler()
        
        # Kargo işaretlendiğinde etiketleri veteriner'e tahsis et
        if self.kargolandimi and not old_kargolandimi:
            self.kargo_tarihi = timezone.now()
            self._tahsis_etiketler()
        
        super().save(*args, **kwargs)
    
    def _olustur_etiketler(self):
        """Sipariş onaylandığında otomatik etiket oluştur"""
        from etiket.models import Etiket, KANAL_VET
        
        olusturulan_etiketler = []
        
        for i in range(self.talep_edilen_adet):
            # Etiket oluştur (seri_numarasi ve etiket_id otomatik oluşturulur)
            etiket = Etiket.objects.create(
                kanal=KANAL_VET,  # Veteriner kanalı
                satici_veteriner=self.veteriner,  # Veterinere tahsis et
                evcil_hayvan=None,  # Hayvan bilgileri boş, veteriner sonra dolduracak
                aktif=False,  # Başlangıçta pasif, veteriner aktif edecek
            )
            olusturulan_etiketler.append(etiket)
        
        return olusturulan_etiketler
    
    def _tahsis_etiketler(self):
        """Kargo işaretlendiğinde etiketleri veteriner'e tahsis et"""
        from etiket.models import Etiket, KANAL_VET
        
        # Bu sipariş için oluşturulan etiketleri al
        etiketler = self.olusturulan_etiketler
        
        for etiket in etiketler:
            # Etiketleri veteriner'e tahsis et
            etiket.tahsis_et(
                kanal=KANAL_VET,
                veteriner=self.veteriner
            )
        
        return etiketler
    
    @property
    def olusturulan_etiketler(self):
        """Bu sipariş için oluşturulan etiketleri getir"""
        if not self.onaylandi or not self.onay_tarihi:
            return []
        
        from etiket.models import Etiket
        # Sipariş onay tarihinde oluşturulan etiketleri getir
        return Etiket.objects.filter(
            satici_veteriner=self.veteriner,  # Doğru alan adı
            olusturulma_tarihi__gte=self.onay_tarihi,
            olusturulma_tarihi__lte=self.onay_tarihi + timezone.timedelta(minutes=1)
        ).order_by('olusturulma_tarihi')

