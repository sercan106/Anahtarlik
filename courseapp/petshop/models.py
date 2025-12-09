# petshop/models.py

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

# Mağaza tipleri
MAGAZA_FIZIKSEL = 'FIZIKSEL'
MAGAZA_ONLINE = 'ONLINE'
MAGAZA_HER_IKISI = 'HER_IKISI'
MAGAZA_TIP_SECENEKLERI = [
    (MAGAZA_FIZIKSEL, 'Sadece Fiziksel Mağaza'),
    (MAGAZA_ONLINE, 'Sadece Online'),
    (MAGAZA_HER_IKISI, 'Hem Fiziksel Hem Online'),
]

# Mağaza büyüklüğü
MAGAZA_KUCUK = 'KUCUK'
MAGAZA_ORTA = 'ORTA'
MAGAZA_BUYUK = 'BUYUK'
MAGAZA_BUYUKLUK_SECENEKLERI = [
    (MAGAZA_KUCUK, 'Küçük İşletme (0-50m²)'),
    (MAGAZA_ORTA, 'Orta Boy (50-150m²)'),
    (MAGAZA_BUYUK, 'Büyük Mağaza (150m²+)'),
]


class PetShop(models.Model):
    # Temel Bilgiler
    ad = models.CharField(max_length=150)
    telefon = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    il = models.ForeignKey('anahtarlik.Il', on_delete=models.CASCADE, related_name='petshoplar', null=True, blank=True)
    ilce = models.ForeignKey('anahtarlik.Ilce', on_delete=models.CASCADE, related_name='petshoplar', null=True, blank=True)
    mahalle = models.ForeignKey('anahtarlik.Mahalle', on_delete=models.CASCADE, related_name='petshoplar', null=True, blank=True)
    mahalle_diger = models.CharField(max_length=200, blank=True, verbose_name="Mahalle (Manuel)", help_text="Mahalle listede yoksa buraya yazınız")
    adres_detay = models.TextField(blank=True)

    kullanici = models.OneToOneField(
        User, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='petshop_profili'
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

    # Sayaçlar
    tahsis_sayisi = models.PositiveIntegerField(default=0)
    satis_sayisi = models.PositiveIntegerField(default=0)

    # Mağaza Bilgileri (PetShop'a özel)
    magaza_tipi = models.CharField(max_length=10, choices=MAGAZA_TIP_SECENEKLERI, blank=True, help_text="Mağaza tipi")
    magaza_buyuklugu = models.CharField(max_length=10, choices=MAGAZA_BUYUKLUK_SECENEKLERI, blank=True, help_text="Mağaza büyüklüğü")
    calisan_sayisi = models.PositiveIntegerField(null=True, blank=True, help_text="Çalışan sayısı (opsiyonel)")
    kurulus_yili = models.PositiveIntegerField(null=True, blank=True, help_text="Kuruluş yılı (opsiyonel)")

    # Hizmetler (PetShop'a özel)
    pet_kuafor = models.BooleanField(default=False, help_text="Pet kuaför hizmeti veriyor mu?")
    pet_hotel = models.BooleanField(default=False, help_text="Pet otel hizmeti veriyor mu?")
    pet_taksi = models.BooleanField(default=False, help_text="Pet taksi hizmeti veriyor mu?")
    pet_egitim = models.BooleanField(default=False, help_text="Eğitim hizmeti veriyor mu?")
    pet_bakim = models.BooleanField(default=False, help_text="Pet bakım hizmeti veriyor mu?")
    
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
    logo = models.ImageField(upload_to='petshop_web/', blank=True, null=True, help_text="Logo")
    cta_metin = models.CharField(max_length=50, blank=True, help_text="Çağrı butonu metni (örn: Mağazayı Ziyaret Et)")
    cta_link = models.URLField(blank=True, help_text="Çağrı butonu linki (örn: WhatsApp linki veya Google Maps)")
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
    
    
    # Web sayfası alanları
    web_baslik = models.CharField(max_length=200, blank=True, help_text="Ana başlık (örn: Pati PetShop)")
    web_slogan = models.CharField(max_length=300, blank=True, help_text="Alt başlık/slogan (örn: Sevimli Dostlarınız İçin Her Şey)")
    web_aciklama = models.TextField(blank=True, help_text="Hakkımızda metni")
    
    # Hizmetler (3 ana hizmet kartı)
    hizmet1_baslik = models.CharField(max_length=100, blank=True, default="QR Künyeler", help_text="1. Hizmet başlığı")
    hizmet1_aciklama = models.TextField(blank=True, default="Kayıp evcil hayvanınızı bulmak için teknolojik çözüm.", help_text="1. Hizmet açıklaması")
    hizmet1_icon = models.CharField(max_length=50, blank=True, default="fa-qrcode", help_text="1. Hizmet ikonu (Font Awesome)")
    
    hizmet2_baslik = models.CharField(max_length=100, blank=True, default="Pet Kuaför", help_text="2. Hizmet başlığı")
    hizmet2_aciklama = models.TextField(blank=True, default="Profesyonel tüy bakımı ve tımar hizmetleri.", help_text="2. Hizmet açıklaması")
    hizmet2_icon = models.CharField(max_length=50, blank=True, default="fa-cut", help_text="2. Hizmet ikonu (Font Awesome)")
    
    hizmet3_baslik = models.CharField(max_length=100, blank=True, default="Pet Otel", help_text="3. Hizmet başlığı")
    hizmet3_aciklama = models.TextField(blank=True, default="Sevimli dostlarınız için güvenli konaklama.", help_text="3. Hizmet açıklaması")
    hizmet3_icon = models.CharField(max_length=50, blank=True, default="fa-hotel", help_text="3. Hizmet ikonu (Font Awesome)")
    
    # Görseller
    web_resim1 = models.ImageField(upload_to='petshop_web/', blank=True, null=True, help_text="Ana görsel (Hakkımızda bölümü)")
    web_resim2 = models.ImageField(upload_to='petshop_web/', blank=True, null=True, help_text="Galeri görseli 1")
    web_resim3 = models.ImageField(upload_to='petshop_web/', blank=True, null=True, help_text="Galeri görseli 2")
    
    # SEO Alanları
    web_seo_baslik = models.CharField(max_length=70, blank=True, help_text="SEO başlık (max 70 karakter)")
    web_seo_aciklama = models.CharField(max_length=160, blank=True, help_text="SEO açıklama (max 160 karakter)")
    web_seo_anahtar_kelimeler = models.CharField(max_length=255, blank=True, help_text="SEO anahtar kelimeler (virgülle ayırın)")
    web_slug = models.SlugField(max_length=200, blank=True, unique=True, null=True, help_text="URL slug (otomatik oluşturulur)")
    
    # Durum
    web_aktif = models.BooleanField(default=False, help_text="Web sayfası aktif mi?")

    def __str__(self):
        return self.ad
    
    def save(self, *args, **kwargs):
        # NOT: web_slug artık otomatik oluşturulmuyor
        # Kullanıcı "Web Sayfamı Düzenle" sayfasından manuel oluşturur
        
        # SEO başlık ve açıklama otomatik oluştur (eğer yoksa)
        if not self.web_seo_baslik and self.web_baslik:
            self.web_seo_baslik = f"{self.web_baslik} | PetShop"[:70]
        
        if not self.web_seo_aciklama and self.web_aciklama:
            self.web_seo_aciklama = self.web_aciklama[:160]
        
        super().save(*args, **kwargs)

    @property
    def kalan_envanter(self) -> int:
        return max((self.tahsis_sayisi or 0) - (self.satis_sayisi or 0), 0)
    
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




class SiparisIstemi(models.Model):
    petshop = models.ForeignKey(PetShop, on_delete=models.CASCADE, related_name='siparis_istekleri')

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
    il = models.ForeignKey('anahtarlik.Il', on_delete=models.CASCADE, related_name='petshop_siparis_istekleri', null=True, blank=True)
    ilce = models.ForeignKey('anahtarlik.Ilce', on_delete=models.CASCADE, related_name='petshop_siparis_istekleri', null=True, blank=True)
    adres_detay = models.TextField(blank=True)

    # Numune / Ödeme takibi
    numune_mi = models.BooleanField(default=False)
    odeme_durumu = models.CharField(max_length=12, choices=ODEME_DURUM_SEC, default=OD_BEKE)
    odeme_tutari = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    odeme_para_birimi = models.CharField(max_length=6, default='TRY')
    odeme_yontemi = models.CharField(max_length=10, choices=ODEME_YONTEM_SEC, blank=True)
    odeme_alinma_tarihi = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.petshop.ad} - {self.talep_edilen_adet} adet"

    @property
    def gonderim_adresi(self) -> str:
        if self.farkli_adres_kullan and self.il and self.ilce and self.adres_detay:
            return f"{self.adres_detay}, {self.ilce}/{self.il}"
        p = self.petshop
        return f"{p.adres_detay}, {p.ilce}/{p.il}".strip(", /")

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
        
        # Ödeme alındı ise tarih otomatik set
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
        
        # Kargo işaretlendiğinde etiketleri petshop'a tahsis et
        if self.kargolandimi and not old_kargolandimi:
            self.kargo_tarihi = timezone.now()
            self._tahsis_etiketler()
        
        super().save(*args, **kwargs)
    
    def _olustur_etiketler(self):
        """Sipariş onaylandığında otomatik etiket oluştur"""
        from etiket.models import Etiket, KANAL_SHOP
        
        olusturulan_etiketler = []
        
        for i in range(self.talep_edilen_adet):
            # Etiket oluştur (seri_numarasi ve etiket_id otomatik oluşturulur)
            etiket = Etiket.objects.create(
                kanal=KANAL_SHOP,  # PetShop kanalı
                satici_petshop=self.petshop,  # PetShop'a tahsis et
                evcil_hayvan=None,  # Hayvan bilgileri boş, petshop sonra dolduracak
                aktif=False,  # Başlangıçta pasif, petshop aktif edecek
            )
            olusturulan_etiketler.append(etiket)
        
        return olusturulan_etiketler
    
    def _tahsis_etiketler(self):
        """Kargo işaretlendiğinde etiketleri petshop'a tahsis et"""
        from etiket.models import Etiket, KANAL_SHOP
        
        # Bu sipariş için oluşturulan etiketleri al
        etiketler = self.olusturulan_etiketler
        
        for etiket in etiketler:
            # Etiketleri petshop'a tahsis et
            etiket.tahsis_et(
                kanal=KANAL_SHOP,
                petshop=self.petshop
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
            satici_petshop=self.petshop,
            olusturulma_tarihi__gte=self.onay_tarihi,
            olusturulma_tarihi__lte=self.onay_tarihi + timezone.timedelta(minutes=1)
        ).order_by('olusturulma_tarihi')
