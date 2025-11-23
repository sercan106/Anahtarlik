from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db.models import F
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from courseapp.constants import ETIKET_SATIS_KREDI
import uuid
import random
import string

# --- Kanal sabitleri (modül düzeyi!) ---
KANAL_ONLINE = 'ONLINE'
KANAL_VET = 'VET'
KANAL_SHOP = 'SHOP'
KANAL_TAHSISSIZ = 'TAHSISSIZ'
KANAL_SECENEKLERI = [
    (KANAL_ONLINE, 'Online'),
    (KANAL_VET, 'Veteriner'),
    (KANAL_SHOP, 'Petshop'),
    (KANAL_TAHSISSIZ, 'Tahsissiz'),
]

# Etiket Kategorileri
class EtiketKategori(models.Model):
    ad = models.CharField(max_length=100, unique=True, verbose_name="Kategori Adı")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    renk = models.CharField(max_length=7, default='#007bff', verbose_name="Renk Kodu", 
                           help_text="Hex renk kodu (örn: #ff0000)")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    
    class Meta:
        verbose_name = "Etiket Kategorisi"
        verbose_name_plural = "Etiket Kategorileri"
        ordering = ['ad']
    
    def __str__(self):
        return self.ad
    
    @property
    def ilk_fotograf(self):
        """Kategorinin ilk aktif fotoğrafını döndürür"""
        return self.fotograflar.filter(aktif=True).first()


class EtiketKategoriFotografi(models.Model):
    kategori = models.ForeignKey(EtiketKategori, on_delete=models.CASCADE, related_name='fotograflar', verbose_name="Kategori")
    fotograf = models.ImageField(upload_to='etiket_kategori_fotograflari/', verbose_name="Fotoğraf")
    baslik = models.CharField(max_length=200, blank=True, verbose_name="Başlık")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    sira = models.PositiveIntegerField(default=0, verbose_name="Sıra", help_text="Görüntüleme sırası (0 = en üstte)")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    
    class Meta:
        verbose_name = "Etiket Kategori Fotoğrafı"
        verbose_name_plural = "Etiket Kategori Fotoğrafları"
        ordering = ['sira', '-olusturulma_tarihi']
    
    def __str__(self):
        return f"{self.kategori.ad} - {self.baslik or 'Fotoğraf'}"


def generate_serial_number():
    """7 karakterli benzersiz seri numarası üret (karışıklık yaratmayacak karakterler)"""
    # Karışıklık yaratmayacak karakterler: 0, O, I, 1 hariç
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    
    while True:
        serial = ''.join(random.choices(chars, k=7))
        # Benzersizlik kontrolü
        if not Etiket.objects.filter(seri_numarasi=serial).exists():
            return serial


class Etiket(models.Model):
    etiket_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    seri_numarasi = models.CharField(max_length=50, unique=True, blank=True)
    evcil_hayvan = models.OneToOneField('anahtarlik.EvcilHayvan', on_delete=models.SET_NULL, null=True, blank=True, related_name='etiket')

    qr_kod_url = models.URLField(blank=True, null=True)
    aktif = models.BooleanField(default=False)
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)
    kilitli = models.BooleanField(default=False)

    # --- Satış kanalı ve partnerler ---
    kanal = models.CharField(max_length=10, choices=KANAL_SECENEKLERI)
    satici_veteriner = models.ForeignKey(
        'veteriner.Veteriner', null=True, blank=True, on_delete=models.SET_NULL, related_name='sattigi_etiketler'
    )
    satici_petshop = models.ForeignKey(
        'petshop.PetShop', null=True, blank=True, on_delete=models.SET_NULL, related_name='sattigi_etiketler'
    )
    tahsis_tarihi = models.DateTimeField(null=True, blank=True)

    # --- Aktivasyon / satış bilgileri ---
    first_activated_at = models.DateTimeField(null=True, blank=True)
    aktiflestiren = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='aktiflestirdigi_etiketler'
    )
    aktiflestirme_tarihi = models.DateTimeField(null=True, blank=True)

    # Etiket kaç kere pasiften aktife geçti? (sadece False→True)
    aktivasyon_sayisi = models.PositiveIntegerField(default=0)

    # --- Künye satış takibi ---
    satis_veteriner = models.ForeignKey(
        'veteriner.Veteriner', 
        null=True, blank=True, 
        on_delete=models.SET_NULL, 
        related_name='sattigi_kunyalar',
        verbose_name="Künyeyi Satan Veteriner"
    )
    satis_tarihi = models.DateTimeField(null=True, blank=True, verbose_name="Satış Tarihi")
    musteri_adi = models.CharField(max_length=100, blank=True, verbose_name="Müşteri Adı")
    musteri_telefon = models.CharField(max_length=15, blank=True, verbose_name="Müşteri Telefon")
    
    # Yeni alanlar
    adres_bayi = models.TextField(blank=True, verbose_name="Adres Bayi")
    adres_kullanici = models.TextField(blank=True, verbose_name="Adres Kullanıcı")
    son_kullanma_tarihi = models.DateTimeField(null=True, blank=True, verbose_name="Son Kullanma Tarihi")
    kategori = models.ForeignKey(EtiketKategori, on_delete=models.SET_NULL, null=True, blank=True, 
                                verbose_name="Etiket Kategorisi", related_name='etiketler')

    class Meta:
        constraints = [
            # VET ise veteriner zorunlu
            models.CheckConstraint(
                name='etiket_vet_icin_veteriner_zorunlu',
                check=(models.Q(kanal__isnull=True) | ~models.Q(kanal=KANAL_VET) | models.Q(satici_veteriner__isnull=False))
            ),
            # SHOP ise petshop zorunlu
            models.CheckConstraint(
                name='etiket_shop_icin_petshop_zorunlu',
                check=(models.Q(kanal__isnull=True) | ~models.Q(kanal=KANAL_SHOP) | models.Q(satici_petshop__isnull=False))
            ),
            # ONLINE ise partnerler boş olmalı
            models.CheckConstraint(
                name='etiket_online_icin_partner_bos',
                check=(
                    models.Q(kanal__isnull=True)
                    | ~models.Q(kanal=KANAL_ONLINE)
                    | (models.Q(satici_veteriner__isnull=True) & models.Q(satici_petshop__isnull=True))
                )
            ),
            # TAHSISSIZ ise partnerler boş olmalı
            models.CheckConstraint(
                name='etiket_tahsissiz_icin_partner_bos',
                check=(
                    models.Q(kanal__isnull=True)
                    | ~models.Q(kanal=KANAL_TAHSISSIZ)
                    | (models.Q(satici_veteriner__isnull=True) & models.Q(satici_petshop__isnull=True))
                )
            ),
        ]

    def __str__(self):
        return f"Etiket {self.seri_numarasi} - {self.evcil_hayvan.ad if self.evcil_hayvan else 'Tanımlanmamış'}"

    # --- QR linkini doğru named URL ile üret ---
    def _build_qr_url(self) -> str:
        # Önceden 'etiket:public' adına reverse deneniyordu (yanlış). Doğrusu 'etiket:qr_landing'
        path = reverse('etiket:qr_landing', kwargs={'tag_id': self.etiket_id})
        site = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
        return f"{site}{path}"

    def clean(self):
        # partner-kanal tutarlılığı
        if self.kanal == KANAL_VET and not self.satici_veteriner:
            raise ValidationError("Veteriner kanalı için veteriner seçilmelidir.")
        if self.kanal == KANAL_SHOP and not self.satici_petshop:
            raise ValidationError("Petshop kanalı için petshop seçilmelidir.")
        if self.kanal == KANAL_ONLINE and (self.satici_veteriner or self.satici_petshop):
            raise ValidationError("Online kanalda veteriner/petshop seçmeyin.")
        if self.kanal == KANAL_TAHSISSIZ and (self.satici_veteriner or self.satici_petshop):
            raise ValidationError("Tahsissiz kanalda veteriner/petshop seçmeyin.")
        
        # Tahsis değiştirme artık mümkün - bu kontrol kaldırıldı
        # if self.pk:
        #     prev = Etiket.objects.get(pk=self.pk)
        #     if prev.tahsis_tarihi:
        #         if (prev.kanal != self.kanal or
        #             prev.satici_veteriner_id != self.satici_veteriner_id or
        #             prev.satici_petshop_id != self.satici_petshop_id):
        #             raise ValidationError("Bu etiket tahsis edilmiş. Tahsis değiştirilemez.")

    def save(self, *args, **kwargs):
        is_new_object = not self.pk
        prev_data = None
        if not is_new_object:
            prev_data = Etiket.objects.filter(pk=self.pk).only(
                'aktif', 'first_activated_at',
                'satici_veteriner_id', 'satici_petshop_id', 'kanal',
                'tahsis_tarihi'
            ).first()

        # Yeni etiket oluşturuluyorsa otomatik seri numarası ata
        if is_new_object and not self.seri_numarasi:
            self.seri_numarasi = generate_serial_number()

        super().save(*args, **kwargs)

        # QR URL oluşturma (bir kereye mahsus)
        if not self.qr_kod_url:
            self.qr_kod_url = self._build_qr_url()
            self.save(update_fields=['qr_kod_url'])
        
        # --- Tahsis Sayaç Kontrolü ---
        is_new_allocation = (
            not prev_data or
            (prev_data and (prev_data.kanal != self.kanal or
                             prev_data.satici_veteriner_id != self.satici_veteriner_id or
                             prev_data.satici_petshop_id != self.satici_petshop_id) and
             (self.kanal and (self.satici_veteriner_id or self.satici_petshop_id)))
        )

        if is_new_allocation:
            # Eski tahsis varsa, eski sahibin sayacını azalt
            if prev_data and (prev_data.satici_veteriner_id or prev_data.satici_petshop_id):
                self._decrease_allocation_counter(prev_data)

            # Yeni tahsis varsa, yeni sahibin sayacını artır
            self._increase_allocation_counter()

            # Tahsis tarihi boşsa şimdi doldur (sadece gerçek tahsis için)
            if not self.tahsis_tarihi and self.kanal and self.kanal != KANAL_TAHSISSIZ:
                self.tahsis_tarihi = timezone.now()
                self.save(update_fields=['tahsis_tarihi'])

        # --- Satış kontrolü: Pasif -> Aktif geçişi ---
        transitioning_to_active = (prev_data and prev_data.aktif is False and self.aktif is True)
        if transitioning_to_active:
            # Her geçişte aktivasyon_sayisi +1 (yarış güvenli)
            Etiket.objects.filter(pk=self.pk).update(aktivasyon_sayisi=F('aktivasyon_sayisi') + 1)

            # İlk aktivasyonsa satış sayacı +1 (yalnızca 1 kez)
            if not prev_data.first_activated_at:
                if not self.first_activated_at:
                    self.first_activated_at = timezone.now()
                    self.save(update_fields=['first_activated_at'])
                self._increase_sales_counter()
            
            # Son kullanma tarihi otomatik set et (manuel girilmediyse)
            if not self.son_kullanma_tarihi:
                from datetime import timedelta
                self.son_kullanma_tarihi = timezone.now() + timedelta(days=365)
                self.save(update_fields=['son_kullanma_tarihi'])
    
    # --- İş mantığı (manuel tahsis istersen) ---
    def tahsis_et(self, kanal: str, veteriner=None, petshop=None):
        # Tahsis değiştirme izni - artık zaten tahsisli olanları da değiştirebiliriz
        # if self.tahsis_tarihi:
        #     raise ValidationError("Bu etiket zaten tahsis edilmiş.")
        
        # Önceki tahsis bilgilerini kaydet (sayaç güncellemesi için)
        prev_kanal = self.kanal
        prev_veteriner = self.satici_veteriner
        prev_petshop = self.satici_petshop
        
        self.kanal = kanal
        if kanal == KANAL_VET:
            self.satici_veteriner = veteriner
            self.satici_petshop = None
        elif kanal == KANAL_SHOP:
            self.satici_petshop = petshop
            self.satici_veteriner = None
        elif kanal == KANAL_TAHSISSIZ:
            self.satici_veteriner = None
            self.satici_petshop = None
        else:
            self.satici_veteriner = None
            self.satici_petshop = None
        self.full_clean()
        self.tahsis_tarihi = timezone.now()
        super().save(update_fields=['kanal', 'satici_veteriner', 'satici_petshop', 'tahsis_tarihi'])
        
        # Sayaç güncellemesi - önceki tahsis varsa azalt, yeni tahsis varsa artır
        if prev_kanal and prev_kanal != KANAL_TAHSISSIZ:
            # Önceki tahsis için sayaç azaltma
            if prev_kanal == KANAL_VET and prev_veteriner:
                from veteriner.models import Veteriner
                Veteriner.objects.filter(pk=prev_veteriner.pk).update(tahsis_sayisi=F('tahsis_sayisi') - 1)
            elif prev_kanal == KANAL_SHOP and prev_petshop:
                from petshop.models import PetShop
                PetShop.objects.filter(pk=prev_petshop.pk).update(tahsis_sayisi=F('tahsis_sayisi') - 1)
        
        if kanal and kanal != KANAL_TAHSISSIZ:
            self._increase_allocation_counter()

    def aktiflestir(self, user):
        """Etiketi aktif yapar; sayaçlar save() içinde yönetilir."""
        self.aktif = True
        self.aktiflestiren = user
        self.aktiflestirme_tarihi = timezone.now()
        
        # Son kullanma tarihi: aktivasyon tarihinden 1 yıl sonra
        from datetime import timedelta
        self.son_kullanma_tarihi = self.aktiflestirme_tarihi + timedelta(days=365)
        
        self.save(update_fields=['aktif', 'aktiflestiren', 'aktiflestirme_tarihi', 'son_kullanma_tarihi'])

    def pasiflestir(self, user=None):
        """Etiketi pasif yapar. Sayaç artmaz."""
        if not self.pk:
            self.aktif = False
            self.aktiflestiren = user or self.aktiflestiren
            super().save(update_fields=['aktif', 'aktiflestiren'])
            return

        if Etiket.objects.filter(pk=self.pk, aktif=False).exists():
            return

        self.aktif = False
        self.aktiflestiren = user or self.aktiflestiren
        self.aktiflestirme_tarihi = timezone.now()
        super().save(update_fields=['aktif', 'aktiflestiren', 'aktiflestirme_tarihi'])
    
    @classmethod
    def pasiflestir_suresi_dolanlar(cls):
        """Son kullanma tarihi geçen etiketleri pasif yapar."""
        from django.utils import timezone
        now = timezone.now()
        
        # Son kullanma tarihi geçen aktif etiketleri bul
        expired_etiketler = cls.objects.filter(
            aktif=True,
            son_kullanma_tarihi__lt=now
        )
        
        pasiflestirilen_sayisi = 0
        for etiket in expired_etiketler:
            etiket.pasiflestir(user=None)  # Sistem tarafından pasifleştirildi
            pasiflestirilen_sayisi += 1
        
        return pasiflestirilen_sayisi

    # --- Sayaçlar ---
    def _increase_allocation_counter(self):
        if self.kanal == KANAL_VET and self.satici_veteriner_id:
            from veteriner.models import Veteriner
            Veteriner.objects.filter(pk=self.satici_veteriner_id).update(tahsis_sayisi=F('tahsis_sayisi') + 1)
        elif self.kanal == KANAL_SHOP and self.satici_petshop_id:
            from petshop.models import PetShop
            PetShop.objects.filter(pk=self.satici_petshop_id).update(tahsis_sayisi=F('tahsis_sayisi') + 1)
            
    def _decrease_allocation_counter(self, prev_data):
        if prev_data.kanal == KANAL_VET and prev_data.satici_veteriner_id:
            from veteriner.models import Veteriner
            Veteriner.objects.filter(pk=prev_data.satici_veteriner_id).update(tahsis_sayisi=F('tahsis_sayisi') - 1)
        elif prev_data.kanal == KANAL_SHOP and prev_data.satici_petshop_id:
            from petshop.models import PetShop
            PetShop.objects.filter(pk=prev_data.satici_petshop_id).update(tahsis_sayisi=F('tahsis_sayisi') - 1)

    def _increase_sales_counter(self):
        if self.kanal == KANAL_VET and self.satici_veteriner_id:
            from veteriner.models import Veteriner
            Veteriner.objects.filter(pk=self.satici_veteriner_id).update(satis_sayisi=F('satis_sayisi') + 1)
            
            # Veteriner'e kredi ver
            try:
                from ilan.models import KrediHareketi
                veteriner = Veteriner.objects.get(pk=self.satici_veteriner_id)
                KrediHareketi.objects.create(
                    kullanici=veteriner.kullanici,
                    hareket_turu=KrediHareketi.HAREKET_ETIKET_SATIS,
                    miktar=ETIKET_SATIS_KREDI,
                    aciklama=f"Etiket satışı: {self.seri_numarasi}",
                    etiket=self
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Kredi verme hatası (veteriner): {e}", exc_info=True)
                
        elif self.kanal == KANAL_SHOP and self.satici_petshop_id:
            from petshop.models import PetShop
            PetShop.objects.filter(pk=self.satici_petshop_id).update(satis_sayisi=F('satis_sayisi') + 1)
            
            # Petshop'a kredi ver
            try:
                from ilan.models import KrediHareketi
                petshop = PetShop.objects.get(pk=self.satici_petshop_id)
                KrediHareketi.objects.create(
                    kullanici=petshop.kullanici,
                    hareket_turu=KrediHareketi.HAREKET_ETIKET_SATIS,
                    miktar=ETIKET_SATIS_KREDI,
                    aciklama=f"Etiket satışı: {self.seri_numarasi}",
                    etiket=self
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Kredi verme hatası (petshop): {e}", exc_info=True)
                
        elif self.kanal == KANAL_ONLINE:
            from core.models import OnlineSatis
            OnlineSatis.objects.get_or_create(id=1) 
            OnlineSatis.objects.filter(id=1).update(satis_sayisi=F('satis_sayisi') + 1)


# Konum kaynağı seçenekleri
KONUM_KAYNAGI_GPS = 'GPS'
KONUM_KAYNAGI_IP = 'IP'
KONUM_KAYNAGI_MANUEL = 'MANUEL'
KONUM_KAYNAGI_SECENEKLERI = [
    (KONUM_KAYNAGI_GPS, 'GPS (Gerçek Konum)'),
    (KONUM_KAYNAGI_IP, 'IP (Tahmini Konum)'),
    (KONUM_KAYNAGI_MANUEL, 'Manuel (Kullanıcı Girdi)'),
]

class EtiketTarama(models.Model):
    """QR Etiket tarama kayıtları - Bulunan hayvan takibi için"""
    
    etiket = models.ForeignKey(Etiket, on_delete=models.CASCADE, related_name='taramalar', verbose_name="Etiket")
    tarama_zamani = models.DateTimeField(auto_now_add=True, verbose_name="Tarama Zamanı")
    
    # Konum kaynağı - ÖNEMLİ: Sahibin yanlış anlamaması için
    konum_kaynagi = models.CharField(
        max_length=10, 
        choices=KONUM_KAYNAGI_SECENEKLERI, 
        default=KONUM_KAYNAGI_IP,
        verbose_name="Konum Kaynağı",
        help_text="Konumun nasıl alındığı (GPS=Gerçek, IP=Tahmini, MANUEL=Kullanıcı girdi)"
    )
    
    # GPS Lokasyon (JavaScript Geolocation API'den)
    gps_latitude = models.FloatField(null=True, blank=True, verbose_name="GPS Enlem")
    gps_longitude = models.FloatField(null=True, blank=True, verbose_name="GPS Boylam")
    gps_dogruluk = models.FloatField(null=True, blank=True, verbose_name="GPS Doğruluk (metre)", 
                                      help_text="Koordinatların doğruluk yarıçapı")
    
    # IP-based lokasyon (yedek - şu anda kullanılan)
    ip_adresi = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Adresi")
    ip_sehir = models.CharField(max_length=100, blank=True, verbose_name="IP Şehir")
    ip_ulke = models.CharField(max_length=100, blank=True, verbose_name="IP Ülke")
    ip_lokasyon_text = models.CharField(max_length=255, blank=True, verbose_name="IP Lokasyon Metni")
    
    # Bulan kişi bilgileri
    bulan_isim = models.CharField(max_length=100, blank=True, verbose_name="Bulan Kişi İsmi")
    bulan_telefon = models.CharField(max_length=20, blank=True, verbose_name="Bulan Kişi Telefonu")
    bulan_email = models.EmailField(blank=True, verbose_name="Bulan Kişi E-postası")
    bulan_mesaj = models.TextField(blank=True, verbose_name="Bulan Kişi Mesajı")
    
    # Teknik detaylar
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    referrer = models.CharField(max_length=500, blank=True, verbose_name="Referrer")
    tarayici_dili = models.CharField(max_length=10, blank=True, verbose_name="Tarayıcı Dili")
    
    # Bildirim durumu
    email_gonderildi = models.BooleanField(default=False, verbose_name="E-posta Gönderildi")
    email_gonderim_zamani = models.DateTimeField(null=True, blank=True, verbose_name="E-posta Gönderim Zamanı")
    
    class Meta:
        verbose_name = "Etiket Tarama"
        verbose_name_plural = "Etiket Taramaları"
        ordering = ['-tarama_zamani']
        indexes = [
            models.Index(fields=['etiket', '-tarama_zamani']),  # Etiket bazlı sorgular için
            models.Index(fields=['-tarama_zamani']),             # Tarih sıralaması için
            models.Index(fields=['email_gonderildi']),           # E-posta durumu sorguları için
            models.Index(fields=['gps_latitude', 'gps_longitude']), # GPS sorguları için
        ]
    
    def __str__(self):
        lokasyon = self.get_lokasyon_kisa()
        return f"{self.etiket.seri_numarasi} - {self.tarama_zamani.strftime('%d.%m.%Y %H:%M')} ({lokasyon})"
    
    def get_lokasyon_kisa(self):
        """Kısa lokasyon metni"""
        if self.gps_latitude and self.gps_longitude:
            kaynak_etiketi = "📍" if self.konum_kaynagi == KONUM_KAYNAGI_GPS else "⚠️"
            return f"{kaynak_etiketi} {self.gps_latitude:.4f}, {self.gps_longitude:.4f}"
        elif self.ip_sehir:
            return f"⚠️ {self.ip_sehir}, {self.ip_ulke} (Tahmini)"
        else:
            return "Bilinmiyor"
    
    def get_konum_kaynagi_aciklama(self):
        """Konum kaynağı açıklaması"""
        if self.konum_kaynagi == KONUM_KAYNAGI_GPS:
            return "📍 GPS (Gerçek Konum) - Yüksek doğruluk"
        elif self.konum_kaynagi == KONUM_KAYNAGI_IP:
            return "⚠️ IP (Tahmini Konum) - PC'lerde GPS olmadığı için IP tabanlı tahmin, yanlış olabilir"
        elif self.konum_kaynagi == KONUM_KAYNAGI_MANUEL:
            return "✏️ Manuel (Kullanıcı Girdi) - Kullanıcı tarafından manuel olarak girildi"
        return "Bilinmiyor"
    
    def get_google_maps_url(self):
        """Google Maps URL'i"""
        if self.gps_latitude and self.gps_longitude:
            return f"https://www.google.com/maps?q={self.gps_latitude},{self.gps_longitude}"
        return None
    
    def has_bulan_bilgisi(self):
        """Bulan kişi bilgisi var mı?"""
        return bool(self.bulan_isim or self.bulan_telefon or self.bulan_email)


# ============= KÜNYE YENİLEME SİSTEMİ =============

class EtiketYenilemeFiyati(models.Model):
    """Künye yenileme fiyatlandırması - Admin panelinden yönetilir"""
    
    # Fiyat bilgileri
    fiyat = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Yenileme Fiyatı (TL)")
    sure_gun = models.IntegerField(default=365, verbose_name="Süre (Gün)")
    
    # Kategori bazlı fiyatlandırma
    etiket_kategori = models.ForeignKey(
        EtiketKategori, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name="Etiket Kategorisi",
        help_text="Boş bırakılırsa genel fiyat olur"
    )
    
    # Kullanıcı tipi bazlı indirimler
    veteriner_indirim_yuzde = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0, 
        verbose_name="Veteriner İndirimi (%)"
    )
    petshop_indirim_yuzde = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0, 
        verbose_name="PetShop İndirimi (%)"
    )
    
    # Durum
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    sira = models.IntegerField(default=0, verbose_name="Sıra")
    
    # Tarihler
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Etiket Yenileme Fiyatı"
        verbose_name_plural = "Etiket Yenileme Fiyatları"
        ordering = ['sira', 'fiyat']
        unique_together = ['etiket_kategori', 'sure_gun']
    
    def __str__(self):
        kategori = self.etiket_kategori.ad if self.etiket_kategori else "Genel"
        return f"{kategori} - {self.sure_gun} gün (₺{self.fiyat})"
    
    def get_kullanici_fiyati(self, user=None):
        """Kullanıcı tipine göre fiyat hesapla"""
        base_fiyat = float(self.fiyat)
        
        if not user or not user.is_authenticated:
            return base_fiyat
        
        # Veteriner indirimi
        if hasattr(user, 'veteriner_profili') and self.veteriner_indirim_yuzde > 0:
            indirim = base_fiyat * (float(self.veteriner_indirim_yuzde) / 100)
            return base_fiyat - indirim
        
        # PetShop indirimi
        if hasattr(user, 'petshop_profili') and self.petshop_indirim_yuzde > 0:
            indirim = base_fiyat * (float(self.petshop_indirim_yuzde) / 100)
            return base_fiyat - indirim
        
        return base_fiyat


class EtiketYenileme(models.Model):
    """Künye yenileme ödemeleri için model"""
    
    # Temel bilgiler
    etiket = models.ForeignKey(Etiket, on_delete=models.CASCADE, related_name='yenilemeler')
    kullanici = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='etiket_yenilemeleri')
    
    # Ödeme bilgileri
    yenileme_ucreti = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Yenileme Ücreti")
    odeme_durumu = models.CharField(
        max_length=20,
        choices=[
            ('BEKLEMEDE', 'Beklemede'),
            ('ODENDI', 'Ödendi'),
            ('IPTAL', 'İptal'),
            ('IADE', 'İade'),
        ],
        default='BEKLEMEDE',
        verbose_name="Ödeme Durumu"
    )
    
    # Stripe ödeme bilgileri
    stripe_payment_intent_id = models.CharField(max_length=200, blank=True, verbose_name="Stripe Payment Intent ID")
    stripe_session_id = models.CharField(max_length=200, blank=True, verbose_name="Stripe Session ID")
    
    # Tarihler
    talep_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Talep Tarihi")
    odeme_tarihi = models.DateTimeField(null=True, blank=True, verbose_name="Ödeme Tarihi")
    
    # Yenileme detayları
    yeni_bitis_tarihi = models.DateTimeField(null=True, blank=True, verbose_name="Yeni Bitiş Tarihi")
    yenileme_suresi_gun = models.IntegerField(default=365, verbose_name="Yenileme Süresi (Gün)")
    
    # Durum
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    
    class Meta:
        verbose_name = "Etiket Yenileme"
        verbose_name_plural = "Etiket Yenilemeleri"
        ordering = ['-talep_tarihi']
    
    def __str__(self):
        return f"{self.etiket.seri_numarasi} - {self.get_odeme_durumu_display()}"
    
    def save(self, *args, **kwargs):
        # Ödeme tamamlandığında etiket süresini uzat
        if self.odeme_durumu == 'ODENDI' and not self.yeni_bitis_tarihi:
            from datetime import timedelta
            self.yeni_bitis_tarihi = timezone.now() + timedelta(days=self.yenileme_suresi_gun)
            
            # Etiket süresini güncelle
            self.etiket.son_kullanma_tarihi = self.yeni_bitis_tarihi
            self.etiket.aktif = True  # Yeniden aktif et
            self.etiket.save()
            
            # Ödeme tarihini set et
            if not self.odeme_tarihi:
                self.odeme_tarihi = timezone.now()
        
        super().save(*args, **kwargs)