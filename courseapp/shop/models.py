# shop/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from anahtarlik.models import EvcilHayvan

class Kategori(models.Model):
    ad = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    aciklama = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, help_text="FontAwesome icon class")
    sira = models.IntegerField(default=0, help_text="Kategori sıralaması")
    aktif = models.BooleanField(default=True)
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        verbose_name = "Kategori"
        verbose_name_plural = "Kategoriler"
        ordering = ['sira', 'ad']

    def __str__(self):
        if self.parent:
            return f"{self.parent.ad} > {self.ad}"
        return self.ad
    
    @property
    def full_path(self):
        """Kategori tam yolu"""
        if self.parent:
            return f"{self.parent.full_path} > {self.ad}"
        return self.ad
    
    @property
    def level(self):
        """Kategori seviyesi"""
        level = 0
        parent = self.parent
        while parent:
            level += 1
            parent = parent.parent
        return level
    
    def get_children(self):
        """Alt kategorileri getir"""
        return self.children.filter(aktif=True).order_by('sira', 'ad')
    
    def get_all_children(self):
        """Tüm alt kategorileri getir (recursive)"""
        children = list(self.get_children())
        for child in self.get_children():
            children.extend(child.get_all_children())
        return children

class Urun(models.Model):
    # Ürün tipi seçenekleri
    URUN_TIPI_CHOICES = [
        ('normal', 'Normal Ürün (Petshop)'),
        ('etiket', 'Etiket Ürünü'),
    ]
    
    ad = models.CharField(max_length=200)
    kisa_aciklama = models.CharField(max_length=200, blank=True, null=True)
    aciklama = models.TextField()
    fiyat = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Normal Müşteri Fiyatı")
    indirimli_fiyat = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stok = models.IntegerField(default=0)
    
    # Bayi (Petshop/Veteriner) fiyatları
    petshop_veteriner_fiyat_aktif = models.BooleanField(
        default=False,
        verbose_name="Bayi Fiyatını Kullan",
        help_text="Aktif edilirse petshop ve veteriner kullanıcıları için özel fiyat gösterilir"
    )
    petshop_veteriner_fiyat = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Petshop/Veteriner Fiyatı",
        help_text="Boş bırakılırsa normal müşteri fiyatı kullanılır"
    )
    petshop_veteriner_indirimli_fiyat = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Petshop/Veteriner İndirimli Fiyat"
    )
    
    # Ürün tipi - HİBRİT MAĞAZA İÇİN
    urun_tipi = models.CharField(
        max_length=20, 
        choices=URUN_TIPI_CHOICES, 
        default='normal',
        verbose_name="Ürün Tipi"
    )
    
    # Normal ürün kategorileri (birden fazla kategori olabilir)
    kategoriler = models.ManyToManyField(
        Kategori, 
        blank=True,
        verbose_name="Petshop Kategorileri",
        related_name='urunler'
    )
    
    # Etiket kategorisi - mevcut etiket app'ten
    etiket_kategori = models.ForeignKey(
        'etiket.EtiketKategori', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Etiket Kategorisi"
    )
    
    # Hayvan türü - her iki ürün tipi için (ManyToManyField - birden fazla seçilebilir)
    hayvan_turu = models.ManyToManyField(
        'anahtarlik.Tur',
        blank=True,
        verbose_name="Hayvan Türü",
        help_text="Ürünün hangi hayvan türleri için uygun olduğunu seçin (birden fazla seçilebilir)",
        related_name='urunler'
    )
    
    # Gelişmiş özellikler
    marka = models.CharField(max_length=100, blank=True, verbose_name="Marka")
    model = models.CharField(max_length=100, blank=True, verbose_name="Model")
    renk = models.CharField(max_length=50, blank=True, verbose_name="Renk")
    boyut = models.CharField(max_length=50, blank=True, verbose_name="Boyut")
    agirlik = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Ağırlık (kg)")
    yas_araligi = models.CharField(max_length=50, blank=True, verbose_name="Yaş Aralığı")
    
    # SEO ve pazarlama
    meta_aciklama = models.CharField(max_length=160, blank=True, verbose_name="Meta Açıklama")
    anahtar_kelimeler = models.TextField(blank=True, verbose_name="Anahtar Kelimeler")
    ozellikler = models.JSONField(default=dict, blank=True, verbose_name="Ürün Özellikleri")
    
    # Satış istatistikleri
    goruntulenme_sayisi = models.PositiveIntegerField(default=0, verbose_name="Görüntülenme Sayısı")
    satis_sayisi = models.PositiveIntegerField(default=0, verbose_name="Satış Sayısı")
    begeni_sayisi = models.PositiveIntegerField(default=0, verbose_name="Beğeni Sayısı")
    
    # Öne çıkarma
    one_cikan = models.BooleanField(default=False, verbose_name="Öne Çıkan")
    yeni_urun = models.BooleanField(default=False, verbose_name="Yeni Ürün")
    indirimli = models.BooleanField(default=False, verbose_name="İndirimli")
    
    # Tavsiye edilen hayvan türü - ManyToManyField (birden fazla seçilebilir)
    tavsiye_edilen_tur = models.ManyToManyField(
        'anahtarlik.Tur',
        blank=True,
        verbose_name="Tavsiye Edilen Hayvan Türü",
        help_text="Bu ürünün özellikle hangi hayvan türleri için tavsiye edildiğini seçin (birden fazla seçilebilir)",
        related_name='tavsiye_edilen_urunler'
    )
    
    # Etiket özel alanları
    qr_kod_ornegi = models.ImageField(
        upload_to='etiket_ornekleri/', 
        blank=True, 
        null=True,
        verbose_name="QR Kod Örneği"
    )
    kullanim_suresi = models.IntegerField(
        default=365, 
        help_text="Gün cinsinden",
        verbose_name="Kullanım Süresi"
    )
    etiket_ozellikler = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name="Etiket Özellikleri"
    )
    
    # Kargo özel ayarları
    kargo_ozel = models.BooleanField(
        default=False,
        help_text='Bu ürün için özel kargo ayarları kullan',
        verbose_name='Özel Kargo Ayarları'
    )
    kargo_firmasi = models.ForeignKey(
        'KargoFirma',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Bu ürün için özel kargo firması seç',
        verbose_name='Kargo Firması'
    )
    kargo_ucreti = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Bu ürün için özel kargo ücreti (boş bırakılırsa kargo firmasının sabit ücreti kullanılır)',
        verbose_name='Kargo Ücreti'
    )
    kargo_teslimat_suresi = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Bu ürün için özel teslimat süresi (boş bırakılırsa kargo firmasının süresi kullanılır)',
        verbose_name='Teslimat Süresi (Gün)'
    )
    ucretsiz_kargo_limiti = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Bu ürün için özel ücretsiz kargo limiti (boş bırakılırsa kargo firmasının limiti kullanılır)',
        verbose_name='Ücretsiz Kargo Limiti'
    )
    
    # Genel alanlar
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Ürün"
        verbose_name_plural = "Ürünler"
        ordering = ['-olusturulma_tarihi']

    def __str__(self):
        return self.ad

    @property
    def indirim_orani(self):
        if self.indirimli_fiyat and self.fiyat:
            from decimal import Decimal
            return ((self.fiyat - self.indirimli_fiyat) / self.fiyat * 100).quantize(Decimal('1'))
        return 0
    
    def get_kullanici_fiyati(self, user=None):
        """
        Kullanıcı tipine göre fiyat döndürür
        
        Args:
            user: Django User objesi (opsiyonel)
            
        Returns:
            dict: {
                'fiyat': float,  # Ana fiyat
                'indirimli_fiyat': float veya None,  # İndirimli fiyat
                'fiyat_tipi': str  # 'normal' veya 'bayi'
            }
        """
        # Kullanıcı tipi kontrolü
        is_bayi = False
        if user and user.is_authenticated:
            # Petshop veya Veteriner kontrolü
            if hasattr(user, 'veteriner_profili') or hasattr(user, 'petshop_profili'):
                is_bayi = True
        
        # Bayi fiyatı aktif ve kullanıcı bayi ise
        if is_bayi and self.petshop_veteriner_fiyat_aktif and self.petshop_veteriner_fiyat:
            return {
                'fiyat': float(self.petshop_veteriner_fiyat),
                'indirimli_fiyat': float(self.petshop_veteriner_indirimli_fiyat) if self.petshop_veteriner_indirimli_fiyat else None,
                'fiyat_tipi': 'bayi'
            }
        
        # Normal müşteri fiyatı
        return {
            'fiyat': float(self.fiyat),
            'indirimli_fiyat': float(self.indirimli_fiyat) if self.indirimli_fiyat else None,
            'fiyat_tipi': 'normal'
        }
    
    @property
    def kategori_display(self):
        """Kategori görünümü - ürün tipine göre"""
        if self.urun_tipi == 'etiket' and self.etiket_kategori:
            return f"🏷️ {self.etiket_kategori.ad}"
        elif self.kategoriler.exists():
            kategoriler_list = ", ".join([k.ad for k in self.kategoriler.all()[:3]])
            if self.kategoriler.count() > 3:
                kategoriler_list += "..."
            return f"📦 {kategoriler_list}"
        return "-"
    
    def clean(self):
        """Model validasyonu"""
        from django.core.exceptions import ValidationError
        
        if self.urun_tipi == 'etiket' and not self.etiket_kategori:
            raise ValidationError("Etiket ürünleri için etiket kategorisi seçilmelidir.")
        
        # ManyToManyField için ID kontrolü gerekli
        if self.urun_tipi == 'normal' and self.pk and not self.kategoriler.exists():
            raise ValidationError("Normal ürünler için en az bir kategori seçilmelidir.")
    
    def stok_azalt(self, miktar):
        """Stok azalt ve uyarı kontrolü yap"""
        if self.stok >= miktar:
            self.stok -= miktar
            self.save()
            
            # Stok uyarı kontrolü
            self.check_stock_warning()
            return True
        return False
    
    def stok_artir(self, miktar):
        """Stok artır"""
        self.stok += miktar
        self.save()
        return True
    
    def check_stock_warning(self):
        """Stok uyarı kontrolü yap"""
        try:
            from .email_utils import send_stock_warning_email
            
            min_stok = 5
            uyari_stok = 10
            
            # Stok uyarı seviyesinde mi kontrol et
            if self.stok <= uyari_stok and self.stok > 0:
                send_stock_warning_email(self, min_stok, uyari_stok)
            elif self.stok == 0:
                send_stock_warning_email(self, min_stok, uyari_stok)
        except Exception as e:
            # Email hatası stok işlemini etkilemesin
            print(f"Stok uyarı email hatası: {str(e)}")
    
    @property
    def stok_durumu(self):
        """Stok durumu string'i"""
        if self.stok == 0:
            return "Tükendi"
        elif self.stok <= 5:
            return "Kritik"
        elif self.stok <= 10:
            return "Azalıyor"
        else:
            return "Yeterli"

class UrunResim(models.Model):
    urun = models.ForeignKey(Urun, on_delete=models.CASCADE, related_name='resimler')
    resim = models.ImageField(upload_to='urunler/', null=True, blank=True)

    def __str__(self):
        return f"{self.urun.ad} - Resim"

class Siparis(models.Model):
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, help_text="Misafir siparişler için boş bırakılabilir")
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)
    toplam_fiyat = models.DecimalField(max_digits=10, decimal_places=2)
    durum = models.CharField(
        max_length=20,
        choices=[
            ('bekliyor', 'Ödeme Bekleniyor'),
            ('odendi', 'Ödeme Alındı'),
            ('hazirlaniyor', 'Hazırlanıyor'),
            ('kargoda', 'Kargoya Verildi'),
            ('teslim_edildi', 'Teslim Edildi'),
            ('iptal', 'İptal Edildi'),
            ('iade', 'İade Edildi'),
        ],
        default='bekliyor'
    )
    adres = models.TextField()
    
    # Misafir kullanıcı bilgileri
    misafir_email = models.EmailField(null=True, blank=True, verbose_name="Misafir Email")
    misafir_telefon = models.CharField(max_length=20, null=True, blank=True, verbose_name="Misafir Telefon")
    misafir_ad_soyad = models.CharField(max_length=200, null=True, blank=True, verbose_name="Misafir Ad Soyad")
    
    # Kargo bilgileri
    kargo_firma = models.ForeignKey('KargoFirma', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kargo Firması")
    kargo_takip_no = models.CharField(max_length=100, blank=True, verbose_name="Kargo Takip No")

    def __str__(self):
        if self.kullanici:
            return f"Sipariş {self.id} - {self.kullanici.username}"
        else:
            return f"Misafir Sipariş {self.id} - {self.misafir_ad_soyad or 'Bilinmeyen'}"

class SiparisKalemi(models.Model):
    siparis = models.ForeignKey(Siparis, on_delete=models.CASCADE, related_name='kalemler')
    urun = models.ForeignKey(Urun, on_delete=models.CASCADE)
    miktar = models.IntegerField(default=1)
    fiyat = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.miktar} x {self.urun.ad}"
    
    def get_total(self):
        """Kalemin toplam fiyatı (miktar * birim fiyat)"""
        return self.miktar * self.fiyat
    
    @property
    def toplam_fiyat(self):
        """Kalemin toplam fiyatı (property olarak)"""
        return self.get_total()


class MagazaKarti(models.Model):
    """
    Ana mağaza sayfasındaki mağaza kartları için model
    Admin panelinden düzenlenebilir
    """
    baslik = models.CharField(max_length=200, verbose_name="Başlık")
    alt_baslik = models.CharField(max_length=300, verbose_name="Alt Başlık", blank=True)
    aciklama = models.TextField(verbose_name="Açıklama", blank=True)

    # Link bilgileri
    link_url = models.CharField(max_length=200, verbose_name="Link URL", blank=True, help_text="Örn: /shop/etiket/ veya #")
    buton_metni = models.CharField(max_length=100, verbose_name="Buton Metni", default="Ürünleri İncele")

    # Görsel ayarlar
    icon = models.CharField(max_length=50, verbose_name="Icon (Emoji)", default="🛍️")
    renk = models.CharField(max_length=50, verbose_name="Renk Kodu", default="#667eea", help_text="Hex renk kodu")

    # Durum ve sıralama
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    sira = models.IntegerField(default=0, verbose_name="Sıra", help_text="Küçük sayı önce gösterilir")

    # İstatistik
    urun_sayisi = models.IntegerField(default=0, verbose_name="Ürün Sayısı (Manuel)")

    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)
    guncellenme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Mağaza Kartı"
        verbose_name_plural = "Mağaza Kartları"
        ordering = ['sira', 'baslik']

    def __str__(self):
        return self.baslik



class MagazaKartiResim(models.Model):
    """
    Mağaza kartları için çoklu resim yükleme
    Admin panelinden mağaza kartına özel resimler eklenebilir
    """
    magaza_karti = models.ForeignKey(MagazaKarti, on_delete=models.CASCADE, related_name='kart_resimleri', verbose_name="Mağaza Kartı")
    resim = models.ImageField(upload_to='magaza_kartlari/slider/', verbose_name="Resim")
    sira = models.IntegerField(default=0, verbose_name="Sıra", help_text="Küçük sayı önce gösterilir")
    alt_metin = models.CharField(max_length=200, blank=True, verbose_name="Alt Metin", help_text="Resim altında gösterilecek metin")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mağaza Kartı Resmi"
        verbose_name_plural = "Mağaza Kartı Resimleri"
        ordering = ['sira', 'olusturulma_tarihi']

    def __str__(self):
        return f"{self.magaza_karti.baslik} - Resim {self.sira}"


# ============= ÜRÜN VARYANT SİSTEMİ =============
class UrunVaryant(models.Model):
    """
    Ürün varyantları (Beden, Renk, vb.)
    Örn: Kedi tasması - S/Kırmızı, M/Mavi
    """
    VARYANT_TIPI_CHOICES = [
        ('beden', 'Beden'),
        ('renk', 'Renk'),
        ('boyut', 'Boyut'),
        ('agirlik', 'Ağırlık'),
    ]

    urun = models.ForeignKey(Urun, on_delete=models.CASCADE, related_name='varyantlar')

    # Varyant özellikleri
    varyant_tipi = models.CharField(max_length=20, choices=VARYANT_TIPI_CHOICES, default='beden')
    deger = models.CharField(max_length=100, verbose_name="Değer", help_text="Örn: S, Kırmızı, 2kg")

    # Stok ve fiyat
    stok = models.IntegerField(default=0, verbose_name="Stok Adedi")
    fiyat_farki = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Fiyat Farkı",
        help_text="Ana fiyata eklenecek/çıkarılacak tutar"
    )

    # SKU (Stok Kodu)
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="Stok Kodu")

    # Görsel
    resim = models.ImageField(upload_to='varyant_resimleri/', blank=True, null=True)

    # Durum
    aktif = models.BooleanField(default=True)
    sira = models.IntegerField(default=0, help_text="Gösterim sırası")

    class Meta:
        verbose_name = "Ürün Varyantı"
        verbose_name_plural = "Ürün Varyantları"
        ordering = ['sira', 'deger']
        unique_together = ['urun', 'varyant_tipi', 'deger']

    def __str__(self):
        return f"{self.urun.ad} - {self.get_varyant_tipi_display()}: {self.deger}"

    @property
    def final_fiyat(self):
        """Varyant için final fiyat"""
        return self.urun.fiyat + self.fiyat_farki


# ============= SEPET SİSTEMİ =============
class Sepet(models.Model):
    """Kullanıcı bazlı sepet"""
    kullanici = models.OneToOneField(User, on_delete=models.CASCADE, related_name='sepet')
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)
    guncellenme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sepet"
        verbose_name_plural = "Sepetler"

    def __str__(self):
        return f"{self.kullanici.username}'in Sepeti"

    @property
    def toplam_fiyat(self):
        """Sepet toplam fiyatı"""
        return sum((item.subtotal for item in self.kalemler.all()), Decimal('0'))

    @property
    def toplam_adet(self):
        """Sepetteki toplam ürün adedi"""
        return sum(item.miktar for item in self.kalemler.all())


class SepetKalemi(models.Model):
    """Sepetteki ürünler"""
    sepet = models.ForeignKey(Sepet, on_delete=models.CASCADE, related_name='kalemler')
    urun = models.ForeignKey(Urun, on_delete=models.CASCADE)
    varyant = models.ForeignKey(UrunVaryant, on_delete=models.CASCADE, null=True, blank=True)
    miktar = models.PositiveIntegerField(default=1)
    birim_fiyat = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Birim Fiyat")
    ekleme_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sepet Kalemi"
        verbose_name_plural = "Sepet Kalemleri"
        unique_together = ['sepet', 'urun', 'varyant']

    def __str__(self):
        if self.varyant:
            return f"{self.miktar}x {self.urun.ad} ({self.varyant.deger})"
        return f"{self.miktar}x {self.urun.ad}"

    def calculate_birim_fiyat(self):
        """Birim fiyat hesapla (varyant dahil, kullanıcı tipine göre)"""
        if self.varyant:
            return self.varyant.final_fiyat
        
        # Kullanıcı tipine göre fiyat
        kullanici_fiyati = self.urun.get_kullanici_fiyati(self.sepet.kullanici)
        
        # İndirimli fiyat varsa onu kullan
        if kullanici_fiyati['indirimli_fiyat']:
            return kullanici_fiyati['indirimli_fiyat']
        
        return kullanici_fiyati['fiyat']

    @property
    def subtotal(self):
        """Alt toplam"""
        return (self.birim_fiyat or Decimal('0')) * self.miktar


# ============= ADRES YÖNETİMİ =============
class Adres(models.Model):
    """Kullanıcı adresleri"""
    ADRES_TIPI_CHOICES = [
        ('ev', 'Ev'),
        ('is', 'İş'),
        ('diger', 'Diğer'),
    ]

    kullanici = models.ForeignKey(User, on_delete=models.CASCADE, related_name='adresler')

    # Adres bilgileri
    baslik = models.CharField(max_length=100, verbose_name="Adres Başlığı", help_text="Örn: Ev Adresim")
    adres_tipi = models.CharField(max_length=20, choices=ADRES_TIPI_CHOICES, default='ev')

    # İletişim
    ad_soyad = models.CharField(max_length=200, verbose_name="Ad Soyad")
    telefon = models.CharField(max_length=20, verbose_name="Telefon")

    # Adres detayları
    il = models.ForeignKey('anahtarlik.Il', on_delete=models.PROTECT, related_name='shop_adresleri', verbose_name="İl")
    ilce = models.ForeignKey('anahtarlik.Ilce', on_delete=models.PROTECT, related_name='shop_adresleri', verbose_name="İlçe")
    mahalle = models.ForeignKey('anahtarlik.Mahalle', on_delete=models.PROTECT, related_name='shop_adresleri', verbose_name="Mahalle", null=True, blank=True)
    mahalle_diger = models.CharField(max_length=200, blank=True, verbose_name="Mahalle (Manuel)", help_text="Mahalle listede yoksa buraya yazınız")
    adres_satiri = models.TextField(verbose_name="Adres")
    posta_kodu = models.CharField(max_length=10, blank=True, verbose_name="Posta Kodu")

    # Notlar
    adres_tarifi = models.TextField(blank=True, verbose_name="Adres Tarifi", help_text="Kolay bulmak için")

    # Varsayılan
    varsayilan = models.BooleanField(default=False, verbose_name="Varsayılan Adres")

    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Adres"
        verbose_name_plural = "Adresler"
        ordering = ['-varsayilan', '-olusturulma_tarihi']

    def __str__(self):
        return f"{self.kullanici.username} - {self.baslik}"

    def save(self, *args, **kwargs):
        # Eğer varsayılan işaretliyse, diğerlerini kaldır
        # SQLite lock sorununu önlemek için mevcut nesneyi exclude et ve sadece değişenleri güncelle
        if self.varsayilan:
            # Sadece mevcut nesne dışındaki varsayılan adresleri güncelle
            queryset = Adres.objects.filter(kullanici=self.kullanici, varsayilan=True)
            if self.pk:  # Eğer nesne veritabanında varsa (güncelleme ise)
                queryset = queryset.exclude(pk=self.pk)
            if queryset.exists():  # Sadece varsa update yap
                queryset.update(varsayilan=False)
        super().save(*args, **kwargs)


# ============= YORUM & DEĞERLENDİRME =============
class UrunYorum(models.Model):
    """Ürün yorumları ve değerlendirmeleri"""
    urun = models.ForeignKey(Urun, on_delete=models.CASCADE, related_name='yorumlar')
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE)

    # Değerlendirme
    yildiz = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Yıldız (1-5)"
    )
    baslik = models.CharField(max_length=200, verbose_name="Başlık")
    yorum = models.TextField(verbose_name="Yorum")

    # Fotoğraflar
    resim1 = models.ImageField(upload_to='yorum_resimleri/', blank=True, null=True)
    resim2 = models.ImageField(upload_to='yorum_resimleri/', blank=True, null=True)
    resim3 = models.ImageField(upload_to='yorum_resimleri/', blank=True, null=True)

    # Doğrulama
    dogrulanmis_alisveris = models.BooleanField(default=False, verbose_name="Doğrulanmış Alışveriş")

    # Beğeni sistemi
    faydali_sayisi = models.PositiveIntegerField(default=0)

    # Durum
    onaylandi = models.BooleanField(default=False, verbose_name="Onaylandı")
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ürün Yorumu"
        verbose_name_plural = "Ürün Yorumları"
        ordering = ['-olusturulma_tarihi']
        unique_together = ['urun', 'kullanici']  # Bir kullanıcı bir ürüne bir yorum

    def __str__(self):
        return f"{self.kullanici.username} - {self.urun.ad} ({self.yildiz}⭐)"


# ============= FAVORİ LİSTESİ =============
class Favori(models.Model):
    """Kullanıcı favori ürünleri"""
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favoriler')
    urun = models.ForeignKey(Urun, on_delete=models.CASCADE)
    ekleme_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Favori"
        verbose_name_plural = "Favoriler"
        unique_together = ['kullanici', 'urun']
        ordering = ['-ekleme_tarihi']

    def __str__(self):
        return f"{self.kullanici.username} - {self.urun.ad}"


# ============= KUPON SİSTEMİ =============
class Kupon(models.Model):
    """İndirim kuponları"""
    KUPON_TIPI_CHOICES = [
        ('yuzde', 'Yüzde İndirim'),
        ('tutar', 'Tutar İndirim'),
        ('ucretsiz_kargo', 'Ücretsiz Kargo'),
    ]

    kod = models.CharField(max_length=50, unique=True, verbose_name="Kupon Kodu")
    aciklama = models.CharField(max_length=200, verbose_name="Açıklama")

    # İndirim
    kupon_tipi = models.CharField(max_length=20, choices=KUPON_TIPI_CHOICES, default='yuzde')
    indirim_degeri = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="İndirim Değeri",
        help_text="Yüzde için 1-100 arası, Tutar için TL"
    )

    # Koşullar
    minimum_tutar = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Minimum Sipariş Tutarı"
    )
    maksimum_indirim = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Maksimum İndirim Tutarı"
    )

    # Kullanım limitleri
    kullanim_limiti = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Toplam Kullanım Limiti"
    )
    kullanici_basina_limit = models.PositiveIntegerField(
        default=1,
        verbose_name="Kullanıcı Başına Limit"
    )
    kullanim_sayisi = models.PositiveIntegerField(default=0)

    # Tarih aralığı
    baslangic_tarihi = models.DateTimeField(verbose_name="Başlangıç Tarihi")
    bitis_tarihi = models.DateTimeField(verbose_name="Bitiş Tarihi")

    # Durum
    aktif = models.BooleanField(default=True)

    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kupon"
        verbose_name_plural = "Kuponlar"
        ordering = ['-olusturulma_tarihi']

    def __str__(self):
        return f"{self.kod} - {self.get_kupon_tipi_display()}"

    def kullanilabilir_mi(self, kullanici, siparis_tutari):
        """Kupon kullanılabilir mi kontrol et"""
        from django.utils import timezone

        # Aktif mi?
        if not self.aktif:
            return False, "Kupon aktif değil"

        # Tarih kontrolü
        now = timezone.now()
        if now < self.baslangic_tarihi:
            return False, "Kupon henüz başlamadı"
        if now > self.bitis_tarihi:
            return False, "Kupon süresi dolmuş"

        # Minimum tutar
        if siparis_tutari < self.minimum_tutar:
            return False, f"Minimum {self.minimum_tutar} TL olmalı"

        # Kullanım limiti
        if self.kullanim_limiti and self.kullanim_sayisi >= self.kullanim_limiti:
            return False, "Kupon kullanım limiti dolmuş"

        # Kullanıcı başına limit
        if kullanici:
            kullanici_kullanim = KuponKullanim.objects.filter(
                kupon=self,
                siparis__kullanici=kullanici
            ).count()
            if kullanici_kullanim >= self.kullanici_basina_limit:
                return False, "Bu kuponu daha önce kullandınız"

        return True, "Kupon geçerli"

    def indirim_hesapla(self, siparis_tutari):
        """İndirim tutarını hesapla"""
        if self.kupon_tipi == 'yuzde':
            indirim = siparis_tutari * (self.indirim_degeri / 100)
            if self.maksimum_indirim:
                indirim = min(indirim, self.maksimum_indirim)
        elif self.kupon_tipi == 'tutar':
            indirim = self.indirim_degeri
        else:  # ucretsiz_kargo
            indirim = 0  # Kargo ücreti view'da hesaplanır

        return indirim


class KuponKullanim(models.Model):
    """Kupon kullanım kayıtları"""
    kupon = models.ForeignKey(Kupon, on_delete=models.CASCADE)
    siparis = models.ForeignKey(Siparis, on_delete=models.CASCADE)
    indirim_tutari = models.DecimalField(max_digits=10, decimal_places=2)
    kullanim_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kupon Kullanımı"
        verbose_name_plural = "Kupon Kullanımları"

    def __str__(self):
        return f"{self.kupon.kod} - Sipariş #{self.siparis.id}"


# ============= KARGO SİSTEMİ =============
class KargoFirma(models.Model):
    """Kargo firmala"""
    ad = models.CharField(max_length=100, verbose_name="Firma Adı")
    logo = models.ImageField(upload_to='kargo_logolar/', blank=True, null=True)

    # Fiyatlandırma
    sabit_ucret = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sabit Ücret")
    ucretsiz_kargo_limiti = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Ücretsiz Kargo Limiti",
        help_text="Bu tutarın üzerinde ücretsiz kargo"
    )

    # Teslimat süresi
    tahmini_sure_gun = models.IntegerField(default=3, verbose_name="Tahmini Teslimat (Gün)")

    # Durum
    aktif = models.BooleanField(default=True)
    sira = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Kargo Firması"
        verbose_name_plural = "Kargo Firmaları"
        ordering = ['sira', 'ad']

    def __str__(self):
        return self.ad

    def kargo_ucreti_hesapla(self, siparis_tutari):
        """Kargo ücretini hesapla"""
        if self.ucretsiz_kargo_limiti and siparis_tutari >= self.ucretsiz_kargo_limiti:
            return 0
        return self.sabit_ucret


# ============= GELİŞMİŞ SİPARİŞ YÖNETİMİ =============
class SiparisDurum(models.Model):
    """Sipariş durum geçmişi"""
    DURUM_CHOICES = [
        ('bekliyor', 'Ödeme Bekleniyor'),
        ('odendi', 'Ödeme Alındı'),
        ('hazirlaniyor', 'Hazırlanıyor'),
        ('kargoda', 'Kargoya Verildi'),
        ('teslim_edildi', 'Teslim Edildi'),
        ('iptal', 'İptal Edildi'),
        ('iade', 'İade Edildi'),
    ]

    siparis = models.ForeignKey(Siparis, on_delete=models.CASCADE, related_name='durum_gecmisi')
    durum = models.CharField(max_length=20, choices=DURUM_CHOICES)
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    kargo_takip_no = models.CharField(max_length=100, blank=True, verbose_name="Kargo Takip No")
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sipariş Durumu"
        verbose_name_plural = "Sipariş Durumları"
        ordering = ['-olusturulma_tarihi']

    def __str__(self):
        return f"Sipariş #{self.siparis.id} - {self.get_durum_display()}"