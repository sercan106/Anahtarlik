# anahtarlik/models.py

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import F
import uuid
# Import additional model modules so Django registers them
from . import dictionaries as _dictionary_models  # noqa: F401




# Telefon numarası validatörü
telefon_validator = RegexValidator(
    regex=r'^(\+90|0)?[5][0-9]{9}$',
    message="Telefon numarası geçerli formatta değil. (05XX XXX XX XX)"
)


class Sahip(models.Model):
    kullanici = models.OneToOneField(User, on_delete=models.CASCADE)
    ad = models.CharField(max_length=50, blank=True)
    soyad = models.CharField(max_length=50, blank=True)
    telefon = models.CharField(
        max_length=15, 
        blank=True,
        validators=[telefon_validator],
        help_text="Telefon numarası (05XX XXX XX XX formatında)"
    )
    yedek_telefon = models.CharField(
        max_length=15, 
        blank=True,
        validators=[telefon_validator],
        help_text="Yedek telefon numarası (05XX XXX XX XX formatında)"
    )
    adres = models.TextField(blank=True)
    acil_durum_kontagi = models.CharField(
        max_length=15, 
        blank=True,
        validators=[telefon_validator],
        help_text="Acil durum kontağı telefon numarası (05XX XXX XX XX formatında)"
    )

    # Konum ve profil alanları (migrasyonlarla ekli)
    il = models.ForeignKey('anahtarlik.Il', on_delete=models.CASCADE, related_name='sahipleri')
    ilce = models.ForeignKey('anahtarlik.Ilce', on_delete=models.CASCADE, related_name='sahipleri')
    mahalle = models.ForeignKey('anahtarlik.Mahalle', on_delete=models.CASCADE, related_name='sahipleri', null=True, blank=True)
    mahalle_diger = models.CharField(max_length=200, blank=True, verbose_name="Mahalle (Manuel)", help_text="Mahalle listede yoksa buraya yazınız")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    profil_fotografi = models.ImageField(upload_to='profil/', null=True, blank=True)

    # Danışman veteriner sistemi
    danisman_veteriner = models.ForeignKey(
        'veteriner.Veteriner', 
        null=True, blank=True, 
        on_delete=models.SET_NULL,
        related_name='danisman_oldugu_sahipler',
        verbose_name="Danışman Veteriner"
    )
    danisman_atanma_tarihi = models.DateTimeField(null=True, blank=True, verbose_name="Danışman Atanma Tarihi")
    danisman_atanma_sebebi = models.CharField(
        max_length=20, 
        choices=[
            ('KUNYE_ALIMI', 'Künye Alımı'),
            ('ILCE_ESLESME', 'İlçe Eşleşmesi'),
            ('IL_ESLESME', 'İl Eşleşmesi'),
        ],
        blank=True,
        verbose_name="Danışman Atanma Sebebi"
    )

    def clean(self):
        """Model doğrulama"""
        from django.core.exceptions import ValidationError
        
        # İl-İlçe uyumsuzluğu kontrolü
        if self.il and self.ilce and self.ilce.il != self.il:
            raise ValidationError({
                'ilce': f"Seçilen ilçe ({self.ilce.ad}) seçilen ile ({self.il.ad}) ait değil."
            })
        
        # Mahalle-İlçe uyumsuzluğu kontrolü
        if self.mahalle and self.ilce and self.mahalle.ilce != self.ilce:
            raise ValidationError({
                'mahalle': f"Seçilen mahalle ({self.mahalle.ad}) seçilen ilçeye ({self.ilce.ad}) ait değil."
            })
    
    def __str__(self):
        return f"{self.ad} {self.soyad}".strip() or self.kullanici.username

    @property
    def aktif_pro_abonelik(self):
        """Aktif pro abonelik - cached"""
        # Cache mekanizması: aynı request içinde tekrar sorgu yapılmasını önler
        if not hasattr(self, '_aktif_pro_abonelik_cache'):
            from django.utils import timezone
            self._aktif_pro_abonelik_cache = self.sahipproabonelik_set.filter(
                aktif=True,
                bitis_tarihi__gt=timezone.now()
            ).select_related('paket').first()
        return self._aktif_pro_abonelik_cache

    @property
    def pro_aktif_mi(self):
        """Pro abonelik aktif mi"""
        return self.aktif_pro_abonelik is not None

    @property
    def pro_paket(self):
        """Aktif pro paket"""
        abonelik = self.aktif_pro_abonelik
        return abonelik.paket if abonelik else None

    def danisman_veteriner_ata(self, force_update=False):
        """
        ADİL VETERİNER ATAMA ALGORİTMASI:
        - Adres uyumlu VET satışta danışman doğrudan o veteriner olur.
        - Online veya petshop ise ilçe bazında aktif veterinerler arasından skor (satış, yük, kapasite bazlı) ile seçim yapılır, ilçe yoksa il bazına iner.
        - Skor formülü: skor = satış * uyum_puani - (yük * katsayi). Eşitse random.
        """
        from django.utils import timezone
        import random
        from veteriner.models import Veteriner
        from etiket.models import KANAL_VET, KANAL_ONLINE, KANAL_SHOP, Etiket
        from django.core.exceptions import ValidationError

        try:
            self.clean()
        except ValidationError:
            return None

        # Evcil hayvanları kontrol et ve EN SON AKTİF EDİLEN veteriner künyesini bul
        # N+1 sorgu problemini önlemek için select_related ve prefetch_related kullan
        etiket = None
        veteriner_etiketleri = []
        
        if hasattr(self, 'evcil_hayvanlar') and self.evcil_hayvanlar.exists():
            # Optimize edilmiş sorgu: select_related ile etiket ve satici_veteriner bilgilerini tek sorguda al
            evcil_hayvanlar = self.evcil_hayvanlar.select_related('etiket', 'etiket__satici_veteriner').all()
            for evcil_hayvan in evcil_hayvanlar:
                if evcil_hayvan.etiket:
                    hayvan_etiketi = evcil_hayvan.etiket
                    # Sadece veterinerden alınmış ve aktif olan etiketleri topla
                    if hayvan_etiketi.kanal == KANAL_VET and hayvan_etiketi.aktif and hayvan_etiketi.satici_veteriner:
                        # Aktivasyon tarihini belirle (first_activated_at öncelikli, yoksa aktiflestirme_tarihi)
                        aktivasyon_tarihi = hayvan_etiketi.first_activated_at or hayvan_etiketi.aktiflestirme_tarihi
                        if aktivasyon_tarihi:
                            veteriner_etiketleri.append({
                                'etiket': hayvan_etiketi,
                                'tarih': aktivasyon_tarihi
                            })
        
        # En son aktif edileni bul (tarihe göre sırala - en yeni önce)
        if veteriner_etiketleri:
            veteriner_etiketleri.sort(key=lambda x: x['tarih'], reverse=True)
            etiket = veteriner_etiketleri[0]['etiket']

        #----------------- 1) ÖNCE: Künyeyi satan veteriner kontrolü (EN YÜKSEK ÖNCELİK) -----------------
        if etiket and etiket.kanal == KANAL_VET and etiket.satici_veteriner:
            satan_vet = etiket.satici_veteriner
            # Künyeyi satan veteriner aktif mi VE aynı ilde mi kontrol et
            if satan_vet.aktif and satan_vet.il == self.il:
                # Veteriner aktifse ve aynı ildeyse, doğrudan atama yap
                self.danisman_veteriner = satan_vet
                self.danisman_atanma_tarihi = timezone.now()
                self.danisman_atanma_sebebi = 'KUNYE_ALIMI'
                self.save(update_fields=['danisman_veteriner', 'danisman_atanma_tarihi', 'danisman_atanma_sebebi'])
                return satan_vet
            # İl farklı ise veya veteriner aktif değilse skor bazlı algoritmaya geç

        #----------------- 2) Künye veterinerden alınmamışsa veya satan veteriner aktif değilse: SKOR BAZLI ALGORİTMA -----------------
        adaylar = []
        
        # İlk önce ilçedeki veterinerler
        ilce_vetler = Veteriner.objects.filter(ilce=self.ilce, aktif=True)
        for vet in ilce_vetler:
            kapasite = getattr(vet, 'dinamik_kapasite', 100)
            yuk = getattr(vet, 'mevcut_yuk', 0)
            if yuk >= kapasite:
                continue
            satis = vet.satis_sayisi_ilce(self.ilce)
            uyum = 1
            skor = satis * uyum - (yuk * 0.2)
            adaylar.append({'vet': vet, 'skor': skor, 'uyum': uyum})

        # İlçede aday yoksa ilde dene
        if not adaylar:
            il_vetler = Veteriner.objects.filter(il=self.il, aktif=True)
            for vet in il_vetler:
                kapasite = getattr(vet, 'dinamik_kapasite', 100)
                yuk = getattr(vet, 'mevcut_yuk', 0)
                if yuk >= kapasite:
                    continue
                satis = vet.satis_sayisi_il(self.il)
                uyum = 0.5
                skor = satis * uyum - (yuk * 0.2)
                adaylar.append({'vet': vet, 'skor': skor, 'uyum': uyum})

        if not adaylar:
            return None

        max_skor = max(a['skor'] for a in adaylar)
        secenekler = [a for a in adaylar if a['skor'] == max_skor]
        secilen_aday = random.choice(secenekler)
        secilen = secilen_aday['vet']
        self.danisman_veteriner = secilen
        self.danisman_atanma_tarihi = timezone.now()
        # Seçilen adayın uyum değerine göre atanma sebebini belirle
        if secilen_aday['uyum'] == 1:
            self.danisman_atanma_sebebi = 'ILCE_ESLESME'
        else:
            self.danisman_atanma_sebebi = 'IL_ESLESME'
        self.save(update_fields=['danisman_veteriner', 'danisman_atanma_tarihi', 'danisman_atanma_sebebi'])
        return secilen

    def _get_ilce_veterinerleri(self):
        """Aynı ilçedeki veterinerleri getir"""
        from veteriner.models import Veteriner
        
        veterinerler = Veteriner.objects.filter(
            ilce=self.ilce,
            aktif=True
        ).order_by('ad')
        
        return veterinerler

    def _get_il_veterinerleri(self):
        """Aynı ildeki veterinerleri getir"""
        from veteriner.models import Veteriner
        
        veterinerler = Veteriner.objects.filter(
            il=self.il,
            aktif=True
        ).order_by('ad')
        
        return veterinerler

    class Meta:
        verbose_name = "Sahip"
        verbose_name_plural = "Sahipler"
        ordering = ['-kullanici__date_joined']
        indexes = [
            models.Index(fields=['il', 'ilce']),
            models.Index(fields=['danisman_veteriner']),
        ]


class KullaniciAdresi(models.Model):
    """Kullanıcıların kayıtlı adresleri"""
    sahip = models.ForeignKey(Sahip, on_delete=models.CASCADE, related_name='adresler')
    baslik = models.CharField(max_length=100, verbose_name="Adres Başlığı", help_text="Örn: Ev, İş, Yazlık")
    adres_metni = models.TextField(verbose_name="Adres")
    il = models.ForeignKey('anahtarlik.Il', on_delete=models.CASCADE, verbose_name="İl")
    ilce = models.ForeignKey('anahtarlik.Ilce', on_delete=models.CASCADE, verbose_name="İlçe")
    mahalle = models.ForeignKey('anahtarlik.Mahalle', on_delete=models.CASCADE, verbose_name="Mahalle", null=True, blank=True)
    mahalle_diger = models.CharField(max_length=200, blank=True, verbose_name="Mahalle (Manuel)", help_text="Mahalle listede yoksa buraya yazınız")
    posta_kodu = models.CharField(max_length=10, blank=True, verbose_name="Posta Kodu")
    telefon = models.CharField(max_length=15, blank=True, verbose_name="Telefon")
    varsayilan = models.BooleanField(default=False, verbose_name="Varsayılan Adres")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Kullanıcı Adresi"
        verbose_name_plural = "Kullanıcı Adresleri"
        ordering = ['-varsayilan', '-olusturma_tarihi']
    
    def clean(self):
        """Model doğrulama"""
        from django.core.exceptions import ValidationError
        
        # İl-İlçe uyumsuzluğu kontrolü
        if self.il and self.ilce and self.ilce.il != self.il:
            raise ValidationError({
                'ilce': f"Seçilen ilçe ({self.ilce.ad}) seçilen ile ({self.il.ad}) ait değil."
            })
        
        # Varsayılan adres kontrolü
        if self.varsayilan:
            # Aynı sahip için başka varsayılan adres var mı?
            existing_default = KullaniciAdresi.objects.filter(
                sahip=self.sahip,
                varsayilan=True
            ).exclude(pk=self.pk)
            if existing_default.exists():
                # Diğer varsayılan adresleri kaldır
                existing_default.update(varsayilan=False)
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.sahip.kullanici.username} - {self.baslik}"



class EvcilHayvan(models.Model):
    CINSIYET_SECENEKLERI = [
        ('erkek', 'Erkek'),
        ('disi', 'Dişi'),
        ('bilinmiyor', 'Bilinmiyor'),
    ]
    ad = models.CharField(max_length=100)
    tur = models.ForeignKey('anahtarlik.Tur', on_delete=models.CASCADE, related_name='evcil_hayvanlar')
    irk = models.ForeignKey('anahtarlik.Irk', on_delete=models.CASCADE, related_name='evcil_hayvanlar')
    cinsiyet = models.CharField(max_length=20, choices=CINSIYET_SECENEKLERI, default='bilinmiyor')
    dogum_tarihi = models.DateField(null=True, blank=True)
    sahip = models.ForeignKey(Sahip, on_delete=models.CASCADE, related_name='evcil_hayvanlar')
    saglik_notu = models.TextField(blank=True)
    beslenme_notu = models.TextField(blank=True)
    genel_not = models.TextField(blank=True)
    davranis_notu = models.TextField(blank=True)
    kayip_durumu = models.BooleanField(default=False)
    kayip_bildirim_tarihi = models.DateTimeField(null=True, blank=True)
    odul_miktari = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    resim = models.ImageField(upload_to='evcil_hayvanlar/', null=True, blank=True)

    def resim_varsa_url(self):
        return self.resim.url if self.resim else None

    def yas_hesapla(self):
        """Doğum tarihinden yaş hesapla"""
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

    def __str__(self):
        tur_ad = self.tur.ad if self.tur else "Bilinmiyor"
        return f"{self.ad} ({tur_ad})"


class Alerji(models.Model):
    evcil_hayvan = models.ForeignKey(EvcilHayvan, on_delete=models.CASCADE, related_name='alerjiler')
    alerji_turu = models.CharField(max_length=100)
    aciklama = models.TextField(blank=True)
    kaydedilme_tarihi = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.evcil_hayvan.ad} - {self.alerji_turu}"


class SaglikKaydi(models.Model):
    evcil_hayvan = models.ForeignKey(EvcilHayvan, on_delete=models.CASCADE, related_name='saglik_kayitlari')
    asi_turu = models.CharField(max_length=100)
    asi_tarihi = models.DateField()
    notlar = models.TextField(blank=True)

    def __str__(self):
        return f"{self.evcil_hayvan.ad} - {self.asi_turu}"


class AsiTakvimi(models.Model):
    evcil_hayvan = models.ForeignKey(EvcilHayvan, on_delete=models.CASCADE, related_name='asi_takvimi')
    asi_turu = models.CharField(max_length=100)
    planlanan_tarih = models.DateField()
    tamamlandi = models.BooleanField(default=False)
    tamamlanma_tarihi = models.DateField(null=True, blank=True)
    notlar = models.TextField(blank=True)

    def __str__(self):
        return f"{self.evcil_hayvan.ad} - {self.asi_turu} (Plan: {self.planlanan_tarih})"


class IlacKaydi(models.Model):
    evcil_hayvan = models.ForeignKey(EvcilHayvan, on_delete=models.CASCADE, related_name='ilac_kayitlari')
    ilac_adi = models.CharField(max_length=100)
    baslangic_tarihi = models.DateField()
    bitis_tarihi = models.DateField(null=True, blank=True)
    dozaj = models.CharField(max_length=50, blank=True)
    notlar = models.TextField(blank=True)

    def __str__(self):
        return f"{self.evcil_hayvan.ad} - {self.ilac_adi}"


class AmeliyatKaydi(models.Model):
    evcil_hayvan = models.ForeignKey(EvcilHayvan, on_delete=models.CASCADE, related_name='ameliyat_kayitlari')
    ameliyat_turu = models.CharField(max_length=100)
    tarih = models.DateField()
    veteriner = models.CharField(max_length=100, blank=True)
    notlar = models.TextField(blank=True)

    def __str__(self):
        return f"{self.evcil_hayvan.ad} - {self.ameliyat_turu}"


class BeslenmeKaydi(models.Model):
    evcil_hayvan = models.ForeignKey(EvcilHayvan, on_delete=models.CASCADE, related_name='beslenme_kayitlari')
    besin_turu = models.CharField(max_length=100)
    tarih = models.DateField()
    miktar = models.CharField(max_length=50)
    notlar = models.TextField(blank=True)

    def __str__(self):
        return f"{self.evcil_hayvan.ad} - {self.besin_turu}"


class KiloKaydi(models.Model):
    evcil_hayvan = models.ForeignKey(EvcilHayvan, on_delete=models.CASCADE, related_name='kilo_kayitlari')
    kilo = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0.1)],
        null=False,
        blank=False
    )
    tarih = models.DateField()
    notlar = models.TextField(blank=True)

    def __str__(self):
        return f"{self.evcil_hayvan.ad} - {self.kilo} kg ({self.tarih})"

    class Meta:
        verbose_name = "Kilo Kaydı"
        verbose_name_plural = "Kilo Kayıtları"


class SahipProPaket(models.Model):
    """Sahip kullanıcıları için pro paket tanımları"""
    paket_adi = models.CharField(max_length=50, verbose_name="Paket Adı")
    aciklama = models.TextField(verbose_name="Açıklama", blank=True)
    ilan_hakki = models.IntegerField(verbose_name="İlan Hakkı", default=0)
    fiyat = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Fiyat (TL)")
    sure_gun = models.IntegerField(verbose_name="Süre (Gün)", default=30)
    
    # Pro özellikler
    asi_hatirlatma = models.BooleanField(default=False, verbose_name="Aşı Hatırlatmaları")
    veteriner_randevu = models.BooleanField(default=False, verbose_name="Veteriner Randevu Hatırlatmaları")
    ilac_takibi = models.BooleanField(default=False, verbose_name="İlaç Takibi")
    beslenme_programi = models.BooleanField(default=False, verbose_name="Beslenme Programı")
    finansal_takip = models.BooleanField(default=False, verbose_name="Finansal Takip")
    egitim_programi = models.BooleanField(default=False, verbose_name="Eğitim Programları")
    foto_galeri_limit = models.IntegerField(default=50, verbose_name="Fotoğraf Galeri Limiti")
    
    renk = models.CharField(max_length=20, default="#007bff", verbose_name="Renk Kodu")
    siralama = models.IntegerField(default=0, verbose_name="Sıralama")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")

    def __str__(self):
        return f"{self.paket_adi} - {self.fiyat} TL"

    class Meta:
        verbose_name = "Sahip Pro Paket"
        verbose_name_plural = "Sahip Pro Paketleri"
        ordering = ['siralama', 'fiyat']


class SahipProAbonelik(models.Model):
    """Sahip kullanıcılarının pro abonelikleri"""
    sahip = models.ForeignKey(Sahip, on_delete=models.CASCADE, verbose_name="Sahip")
    paket = models.ForeignKey(SahipProPaket, on_delete=models.CASCADE, verbose_name="Paket")
    baslangic_tarihi = models.DateTimeField(verbose_name="Başlangıç Tarihi")
    bitis_tarihi = models.DateTimeField(verbose_name="Bitiş Tarihi")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")

    def __str__(self):
        return f"{self.sahip.kullanici.get_full_name()} - {self.paket.paket_adi}"

    @property
    def kalan_gun(self):
        """Kalan gün sayısı"""
        from django.utils import timezone
        if self.bitis_tarihi > timezone.now():
            return (self.bitis_tarihi - timezone.now()).days
        return 0

    @property
    def aktif_mi(self):
        """Abonelik aktif mi kontrolü"""
        from django.utils import timezone
        return self.aktif and self.bitis_tarihi > timezone.now()

    class Meta:
        verbose_name = "Sahip Pro Abonelik"
        verbose_name_plural = "Sahip Pro Abonelikleri"
        ordering = ['-olusturulma_tarihi']


class Bildirim(models.Model):
    """Sahip kullanıcıları için bildirim sistemi"""
    sahip = models.ForeignKey(Sahip, on_delete=models.CASCADE, related_name='bildirimler', verbose_name="Sahip")
    baslik = models.CharField(max_length=200, verbose_name='Başlık')
    mesaj = models.TextField(verbose_name='Mesaj')
    url = models.URLField(blank=True, null=True, help_text="Bildirimin yönlendireceği URL (örn: tarama detay sayfası)", verbose_name="URL")
    okundu = models.BooleanField(default=False, verbose_name='Okundu')
    olusturma_zamani = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma Zamanı')
    tur = models.CharField(
        choices=[
            ('QR_TARAMA', 'QR Kod Tarama'),
            ('BULAN_BILGI', 'Bulan Kişi Bilgisi'),
            ('KAYIP_HAYVAN', 'Kayıp Hayvan'),
            ('GENEL', 'Genel Bildirim'),
            ('SISTEM', 'Sistem Bildirimi'),
            ('PROMOSYON', 'Promosyon')
        ],
        default='GENEL',
        max_length=20,
        verbose_name='Bildirim Türü'
    )
    tarama = models.ForeignKey(
        'etiket.EtiketTarama',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='bildirimler',
        verbose_name="İlgili Tarama"
    )
    oncelik = models.CharField(
        choices=[
            ('YUKSEK', 'Yüksek'),
            ('NORMAL', 'Normal'),
            ('DUSUK', 'Düşük')
        ],
        default='NORMAL',
        max_length=10,
        verbose_name='Öncelik'
    )

    def __str__(self):
        return f"{self.sahip.kullanici.username} - {self.baslik}"

    @property
    def saklama_suresi(self):
        """Bildirim türüne göre saklama süresi (gün)"""
        if self.tur in ['QR_TARAMA', 'BULAN_BILGI', 'KAYIP_HAYVAN']:
            return 30  # Kritik bildirimler 30 gün
        elif self.tur == 'GENEL':
            return 7   # Genel bildirimler 7 gün
        else:
            return 3   # Sistem/promosyon 3 gün

    @property
    def silinecek_mi(self):
        """Bildirim silinmeli mi kontrol et"""
        from django.utils import timezone
        from datetime import timedelta
        
        silme_tarihi = self.olusturma_zamani + timedelta(days=self.saklama_suresi)
        return timezone.now() > silme_tarihi

    class Meta:
        verbose_name = "Bildirim"
        verbose_name_plural = "Bildirimler"
        ordering = ['-olusturma_zamani']
        indexes = [
            models.Index(fields=['sahip', '-olusturma_zamani']),  # Sahip bazlı sorgular için
            models.Index(fields=['okundu']),  # Okunma durumu sorguları için
            models.Index(fields=['tur']),  # Bildirim türü sorguları için
        ]


# ========== Ana Sayfa İçerik Yönetimi ==========

class HeroSlide(models.Model):
    """Hero section için dinamik slide'lar"""
    baslik = models.CharField(max_length=200, verbose_name="Başlık", help_text="Ana başlık metni")
    aciklama = models.TextField(verbose_name="Açıklama", help_text="Açıklama metni")
    arka_plan_resim = models.ImageField(
        upload_to='hero_slides/',
        null=True,
        blank=True,
        verbose_name="Arka Plan Resmi (Masaüstü)",
        help_text="1920x1080 önerilen (yatay görsel)"
    )
    arka_plan_resim_mobil = models.ImageField(
        upload_to='hero_slides/mobile/',
        null=True,
        blank=True,
        verbose_name="Arka Plan Resmi (Mobil)",
        help_text="1080x1920 önerilen (dikey görsel)"
    )
    arka_plan_renk = models.TextField(
        default='linear-gradient(135deg, rgba(255, 107, 157, 0.95) 0%, rgba(78, 205, 196, 0.85) 100%)',
        verbose_name="Arka Plan Renk/Gradient",
        help_text="CSS gradient veya renk kodu"
    )
    buton_1_metin = models.CharField(max_length=100, blank=True, verbose_name="Buton 1 Metin")
    buton_1_url = models.CharField(max_length=200, blank=True, verbose_name="Buton 1 URL")
    buton_2_metin = models.CharField(max_length=100, blank=True, verbose_name="Buton 2 Metin")
    buton_2_url = models.CharField(max_length=200, blank=True, verbose_name="Buton 2 URL")
    sira = models.IntegerField(default=0, verbose_name="Sıra", help_text="Gösterim sırası (küçükten büyüğe)")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")
    guncelleme_tarihi = models.DateTimeField(auto_now=True, verbose_name="Güncelleme Tarihi")

    class Meta:
        verbose_name = "Hero Slide"
        verbose_name_plural = "Hero Slide'lar"
        ordering = ['sira', '-olusturma_tarihi']

    def __str__(self):
        return f"{self.baslik} (Sıra: {self.sira})"


class HizmetKarti(models.Model):
    """Hizmetler bölümü için kartlar"""
    IKON_SECENEKLERI = [
        ('fas fa-qrcode', 'QR Kod'),
        ('fas fa-calendar-check', 'Takvim/Randevu'),
        ('fas fa-shopping-cart', 'Alışveriş'),
        ('fas fa-paw', 'Pati'),
        ('fas fa-heartbeat', 'Kalp/Sağlık'),
        ('fas fa-user-md', 'Doktor'),
        ('fas fa-hospital', 'Hastane'),
        ('fas fa-notes-medical', 'Medikal Notlar'),
        ('fas fa-ambulance', 'Ambulans'),
        ('fas fa-shield-alt', 'Kalkan/Koruma'),
        ('fas fa-home', 'Ev'),
        ('fas fa-phone', 'Telefon'),
        ('fas fa-envelope', 'E-posta'),
        ('fas fa-map-marker-alt', 'Konum'),
    ]

    baslik = models.CharField(max_length=100, verbose_name="Başlık")
    aciklama = models.TextField(verbose_name="Açıklama", help_text="Kısa açıklama metni")
    ikon = models.CharField(
        max_length=50,
        choices=IKON_SECENEKLERI,
        default='fas fa-paw',
        verbose_name="İkon",
        help_text="Font Awesome ikon sınıfı"
    )
    buton_metin = models.CharField(max_length=50, default="Keşfet", verbose_name="Buton Metni")
    buton_url = models.CharField(max_length=200, verbose_name="Buton URL")
    sira = models.IntegerField(default=0, verbose_name="Sıra")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    animasyon_gecikmesi = models.IntegerField(
        default=100,
        verbose_name="Animasyon Gecikmesi (ms)",
        help_text="AOS animasyon gecikmesi"
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")
    guncelleme_tarihi = models.DateTimeField(auto_now=True, verbose_name="Güncelleme Tarihi")

    class Meta:
        verbose_name = "Hizmet Kartı"
        verbose_name_plural = "Hizmet Kartları"
        ordering = ['sira', '-olusturma_tarihi']

    def __str__(self):
        return f"{self.baslik} (Sıra: {self.sira})"


class AnaSayfaAyar(models.Model):
    """Ana sayfa genel ayarları (Singleton Model)"""
    hizmetler_baslik = models.CharField(
        max_length=200,
        default="Hizmetlerimiz",
        verbose_name="Hizmetler Başlık"
    )
    hizmetler_aciklama = models.TextField(
        default="Evcil dostlarınız için en iyi dijital kimlik ve sağlık takip çözümleri",
        verbose_name="Hizmetler Açıklama"
    )
    slide_gecis_suresi = models.IntegerField(
        default=5000,
        verbose_name="Slide Geçiş Süresi (ms)",
        help_text="Hero slide'ların otomatik geçiş süresi (milisaniye)"
    )
    slide_animasyon = models.CharField(
        max_length=50,
        default='fade',
        choices=[
            ('fade', 'Soluklaşma'),
            ('slide', 'Kaydırma'),
            ('zoom', 'Yakınlaşma'),
        ],
        verbose_name="Slide Animasyon Tipi"
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")
    guncelleme_tarihi = models.DateTimeField(auto_now=True, verbose_name="Güncelleme Tarihi")

    class Meta:
        verbose_name = "Ana Sayfa Ayarı"
        verbose_name_plural = "Ana Sayfa Ayarları"

    def __str__(self):
        return "Ana Sayfa Ayarları"

    def save(self, *args, **kwargs):
        """Singleton pattern - sadece bir kayıt olmasını sağla"""
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Silmeyi engelle"""
        pass

    @classmethod
    def load(cls):
        """Tek kaydı yükle veya oluştur"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
