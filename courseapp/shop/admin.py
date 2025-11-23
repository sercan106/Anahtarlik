# shop/admin.py (Hibrit Mağaza Sistemi - Etiket + Petshop Ürünleri)

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Kategori, Urun, UrunResim, Siparis, SiparisKalemi, MagazaKarti, MagazaKartiResim,
    UrunVaryant, Sepet, SepetKalemi, Adres, UrunYorum, Favori,
    Kupon, KuponKullanim, KargoFirma, SiparisDurum
)

# ============================================
# INLINE CLASSES
# ============================================

# Inline için UrunResim (birden fazla resim ekleme)
class UrunResimInline(admin.TabularInline):
    model = UrunResim
    extra = 1  # Varsayılan 1 boş form göster
    fields = ('resim',)  # Sadece resim alanı

# Inline için UrunVaryant (ürün varyantları)
class UrunVaryantInline(admin.TabularInline):
    model = UrunVaryant
    extra = 1
    fields = ('varyant_tipi', 'deger', 'stok', 'fiyat_farki', 'sku', 'aktif')
    list_editable = ('aktif',)

@admin.register(Kategori)
class KategoriAdmin(admin.ModelAdmin):
    list_display = ('ad', 'slug')  # Listede gösterilecek alanlar
    search_fields = ('ad',)  # Arama için
    prepopulated_fields = {'slug': ('ad',)}  # Slug otomatik doldur

@admin.register(Urun)
class UrunAdmin(admin.ModelAdmin):
    list_display = ('ad', 'urun_tipi_badge', 'kategoriler_display', 'hayvan_turu_display', 'marka', 'fiyat', 'petshop_veteriner_fiyat_badge', 'stok', 'one_cikan', 'yeni_urun', 'indirimli', 'aktif', 'olusturulma_tarihi')
    search_fields = ('ad', 'aciklama', 'kisa_aciklama', 'marka', 'model')
    list_filter = ('urun_tipi', 'kategoriler', 'etiket_kategori', 'hayvan_turu', 'tavsiye_edilen_tur', 'marka', 'renk', 'one_cikan', 'yeni_urun', 'indirimli', 'aktif', 'olusturulma_tarihi')
    filter_horizontal = ('kategoriler', 'hayvan_turu', 'tavsiye_edilen_tur')
    inlines = [UrunResimInline, UrunVaryantInline]
    list_editable = ('one_cikan', 'yeni_urun', 'indirimli', 'aktif')
    
    # Fieldsets - Sofistike hibrit mağaza için organize edilmiş form
    fieldsets = (
        ('Genel Bilgiler', {
            'fields': ('ad', 'kisa_aciklama', 'aciklama', 'urun_tipi', 'aktif')
        }),
        ('Kategori Seçimi', {
            'fields': ('kategoriler', 'etiket_kategori'),
            'description': 'Pet ürünleri için birden fazla kategori seçebilirsiniz. Etiket ürünleri için etiket kategorisi.'
        }),
        ('Hayvan Türü', {
            'fields': ('hayvan_turu', 'tavsiye_edilen_tur'),
            'description': 'Hayvan Türü: Ürünün hangi hayvan türleri için uygun olduğunu seçin. Tavsiye Edilen Tür: Bu ürünün özellikle hangi hayvan türleri için önerildiğini seçin (birden fazla seçilebilir)'
        }),
        ('Ürün Özellikleri', {
            'fields': ('marka', 'model', 'renk', 'boyut', 'agirlik', 'yas_araligi'),
            'description': 'Petshop ürünleri için detaylı özellikler'
        }),
        ('Fiyat ve Stok', {
            'fields': ('fiyat', 'indirimli_fiyat', 'stok')
        }),
        ('Bayi Fiyatları (Petshop/Veteriner)', {
            'fields': ('petshop_veteriner_fiyat_aktif', 'petshop_veteriner_fiyat', 'petshop_veteriner_indirimli_fiyat'),
            'classes': ('collapse',),
            'description': 'Petshop ve Veteriner kullanıcıları için özel fiyatlandırma'
        }),
        ('Pazarlama ve SEO', {
            'fields': ('meta_aciklama', 'anahtar_kelimeler', 'ozellikler'),
            'classes': ('collapse',),
            'description': 'SEO ve pazarlama bilgileri'
        }),
        ('Öne Çıkarma', {
            'fields': ('one_cikan', 'yeni_urun', 'indirimli'),
            'description': 'Ürünü öne çıkarmak için kullanın'
        }),
        ('Etiket Özellikleri', {
            'fields': ('qr_kod_ornegi', 'kullanim_suresi', 'etiket_ozellikler'),
            'classes': ('collapse',),
            'description': 'Sadece etiket ürünleri için'
        }),
    )
    
    # Özel metodlar
    def urun_tipi_badge(self, obj):
        """Ürün tipi için renkli badge"""
        if obj.urun_tipi == 'etiket':
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 2px 8px; border-radius: 3px;">🏷️ Etiket</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #007bff; color: white; padding: 2px 8px; border-radius: 3px;">📦 Petshop</span>'
            )
    urun_tipi_badge.short_description = "Tip"
    
    def kategoriler_display(self, obj):
        """Kategoriler görünümü"""
        kategoriler = obj.kategoriler.all()
        if kategoriler:
            return ', '.join([k.ad for k in kategoriler[:3]])
        return "-"
    kategoriler_display.short_description = "Kategoriler"
    
    def hayvan_turu_display(self, obj):
        """Hayvan türleri görünümü"""
        turler = obj.hayvan_turu.all()
        if turler:
            return ', '.join([t.ad for t in turler[:3]])
        return "-"
    hayvan_turu_display.short_description = "Hayvan Türü"
    
    def tavsiye_edilen_tur_display(self, obj):
        """Tavsiye edilen hayvan türleri görünümü"""
        turler = obj.tavsiye_edilen_tur.all()
        if turler:
            return ', '.join([t.ad for t in turler[:3]])
        return "-"
    tavsiye_edilen_tur_display.short_description = "Tavsiye Edilen Tür"
    
    def petshop_veteriner_fiyat_badge(self, obj):
        """Bayi fiyat badge"""
        if obj.petshop_veteriner_fiyat_aktif and obj.petshop_veteriner_fiyat:
            from django.utils.html import format_html
            return format_html(
                '<span style="background-color: #ff6b6b; color: white; padding: 2px 8px; border-radius: 3px; font-weight: bold;">₺{}</span>',
                obj.petshop_veteriner_fiyat
            )
        return "-"
    petshop_veteriner_fiyat_badge.short_description = "Bayi Fiyat"
    
    def get_form(self, request, obj=None, **kwargs):
        """Form'u dinamik olarak düzenle"""
        form = super().get_form(request, obj, **kwargs)
        
        # Etiket kategorilerini sadece aktif olanlardan seç
        if hasattr(form.base_fields, 'etiket_kategori'):
            from etiket.models import EtiketKategori
            form.base_fields['etiket_kategori'].queryset = EtiketKategori.objects.filter(aktif=True)
        
        return form

@admin.register(Siparis)
class SiparisAdmin(admin.ModelAdmin):
    list_display = ('kullanici', 'olusturulma_tarihi', 'toplam_fiyat', 'durum')  # Listede göster
    search_fields = ('kullanici__username',)  # Arama
    list_filter = ('durum', 'olusturulma_tarihi')  # Filtre

# Inline için SiparisKalemi (sipariş kalemleri)
class SiparisKalemiInline(admin.TabularInline):
    model = SiparisKalemi
    extra = 0  # Boş form yok
    fields = ('urun', 'miktar', 'fiyat')

# SiparisAdmin'e inline ekle (sipariş detaylarını göster)
SiparisAdmin.inlines = [SiparisKalemiInline]

@admin.register(SiparisKalemi)
class SiparisKalemiAdmin(admin.ModelAdmin):
    list_display = ('siparis', 'urun', 'miktar', 'fiyat')  # Listede göster
    search_fields = ('urun__ad',)  # Arama

@admin.register(UrunResim)
class UrunResimAdmin(admin.ModelAdmin):
    list_display = ('urun', 'resim')  # Listede göster
    search_fields = ('urun__ad',)  # Arama


# Inline için MagazaKartiResim
class MagazaKartiResimInline(admin.TabularInline):
    model = MagazaKartiResim
    extra = 3
    fields = ('resim', 'alt_metin', 'sira', 'aktif')

@admin.register(MagazaKarti)
class MagazaKartiAdmin(admin.ModelAdmin):
    list_display = ('icon_display', 'baslik', 'sira', 'urun_sayisi', 'aktif')
    list_editable = ('sira', 'aktif')
    list_filter = ('aktif',)
    search_fields = ('baslik', 'alt_baslik', 'aciklama')
    inlines = [MagazaKartiResimInline]

    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('baslik', 'alt_baslik', 'aciklama', 'sira', 'aktif')
        }),
        ('Görsel', {
            'fields': ('icon', 'renk'),
        }),
        ('Link Bilgileri', {
            'fields': ('link_url', 'buton_metni'),
        }),
        ('İstatistik', {
            'fields': ('urun_sayisi',),
            'description': 'Ürün sayısını manuel olarak girebilirsiniz'
        }),
    )

    def icon_display(self, obj):
        """İcon gösterimi"""
        return format_html(
            '<span style="font-size: 2rem;">{}</span>',
            obj.icon
        )
    icon_display.short_description = "İkon"



# ============================================
# YENİ E-TİCARET MODELLERİ - ADMIN KAYITLARI
# ============================================

@admin.register(UrunVaryant)
class UrunVaryantAdmin(admin.ModelAdmin):
    list_display = ('urun', 'varyant_tipi', 'deger', 'stok', 'fiyat_badge', 'final_fiyat_badge', 'sku', 'aktif')
    list_filter = ('varyant_tipi', 'aktif')
    search_fields = ('urun__ad', 'deger', 'sku')
    list_editable = ('stok', 'aktif')

    fieldsets = (
        ('Varyant Bilgileri', {
            'fields': ('urun', 'varyant_tipi', 'deger', 'sku')
        }),
        ('Stok ve Fiyat', {
            'fields': ('stok', 'fiyat_farki', 'aktif')
        }),
    )

    def fiyat_badge(self, obj):
        """Fiyat farkı gösterimi"""
        if obj.fiyat_farki > 0:
            return format_html(
                '<span style="color: green;">+₺{}</span>',
                obj.fiyat_farki
            )
        elif obj.fiyat_farki < 0:
            return format_html(
                '<span style="color: red;">₺{}</span>',
                obj.fiyat_farki
            )
        return "₺0"
    fiyat_badge.short_description = "Fiyat Farkı"

    def final_fiyat_badge(self, obj):
        """Final fiyat gösterimi"""
        return format_html(
            '<strong>₺{}</strong>',
            obj.final_fiyat
        )
    final_fiyat_badge.short_description = "Final Fiyat"


# Sepet Kalemleri Inline
class SepetKalemiInline(admin.TabularInline):
    model = SepetKalemi
    extra = 0
    fields = ('urun', 'varyant', 'miktar', 'subtotal_display')
    readonly_fields = ('subtotal_display',)

    def subtotal_display(self, obj):
        """Subtotal gösterimi"""
        return format_html('<strong>₺{}</strong>', obj.subtotal)
    subtotal_display.short_description = "Ara Toplam"


@admin.register(Sepet)
class SepetAdmin(admin.ModelAdmin):
    list_display = ('kullanici', 'toplam_adet_badge', 'toplam_fiyat_badge', 'olusturulma_tarihi')
    search_fields = ('kullanici__username', 'kullanici__email')
    readonly_fields = ('olusturulma_tarihi', 'guncellenme_tarihi')
    inlines = [SepetKalemiInline]

    def toplam_adet_badge(self, obj):
        """Toplam ürün adedi"""
        return format_html(
            '<span style="background-color: #17a2b8; color: white; padding: 3px 10px; border-radius: 15px;">{} Ürün</span>',
            obj.toplam_adet
        )
    toplam_adet_badge.short_description = "Toplam Adet"

    def toplam_fiyat_badge(self, obj):
        """Toplam fiyat"""
        return format_html(
            '<strong style="color: #28a745; font-size: 1.1em;">₺{}</strong>',
            obj.toplam_fiyat
        )
    toplam_fiyat_badge.short_description = "Toplam Fiyat"


@admin.register(SepetKalemi)
class SepetKalemiAdmin(admin.ModelAdmin):
    list_display = ('sepet', 'urun', 'varyant', 'miktar', 'subtotal_badge', 'ekleme_tarihi')
    list_filter = ('ekleme_tarihi',)
    search_fields = ('urun__ad', 'sepet__kullanici__username')

    def subtotal_badge(self, obj):
        """Subtotal gösterimi"""
        return format_html(
            '<strong style="color: #28a745;">₺{}</strong>',
            obj.subtotal
        )
    subtotal_badge.short_description = "Ara Toplam"


@admin.register(Adres)
class AdresAdmin(admin.ModelAdmin):
    list_display = ('kullanici', 'baslik', 'il', 'ilce', 'varsayilan_badge')
    list_filter = ('varsayilan', 'il')
    search_fields = ('kullanici__username', 'baslik', 'ad_soyad', 'telefon', 'adres_satiri')
    
    # Performans optimizasyonu: select_related kullan
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('kullanici', 'il', 'ilce', 'mahalle')

    fieldsets = (
        ('Kullanıcı Bilgileri', {
            'fields': ('kullanici', 'baslik', 'adres_tipi', 'ad_soyad', 'telefon')
        }),
        ('Adres Bilgileri', {
            'fields': ('il', 'ilce', 'mahalle', 'mahalle_diger', 'adres_satiri', 'posta_kodu', 'adres_tarifi')
        }),
        ('Ayarlar', {
            'fields': ('varsayilan',)
        }),
    )
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Foreign key alanları için queryset optimizasyonu"""
        from anahtarlik.dictionaries import Il, Ilce, Mahalle
        
        # İl alanı için - tüm iller (sayı az, sorun yok)
        if db_field.name == 'il':
            kwargs['queryset'] = Il.objects.all().order_by('ad')
        
        # İlçe alanı için - başlangıçta boş, obje varsa il'e göre filtrele
        elif db_field.name == 'ilce':
            # Mevcut obje varsa ve il'i seçilmişse
            obj_id = request.resolver_match.kwargs.get('object_id')
            if obj_id:
                try:
                    from .models import Adres
                    obj = Adres.objects.select_related('il', 'ilce').get(pk=obj_id)
                    if obj.il:
                        kwargs['queryset'] = Ilce.objects.filter(il=obj.il).order_by('ad')
                    else:
                        kwargs['queryset'] = Ilce.objects.none()
                except Adres.DoesNotExist:
                    kwargs['queryset'] = Ilce.objects.none()
            else:
                kwargs['queryset'] = Ilce.objects.none()
        
        # Mahalle alanı için - başlangıçta boş, obje varsa ilçe'ye göre filtrele
        elif db_field.name == 'mahalle':
            obj_id = request.resolver_match.kwargs.get('object_id')
            if obj_id:
                try:
                    from .models import Adres
                    obj = Adres.objects.select_related('ilce', 'mahalle').get(pk=obj_id)
                    if obj.ilce:
                        # İlk 500 mahalle (performans için limit)
                        kwargs['queryset'] = Mahalle.objects.filter(ilce=obj.ilce).order_by('ad')[:500]
                    else:
                        kwargs['queryset'] = Mahalle.objects.none()
                except Adres.DoesNotExist:
                    kwargs['queryset'] = Mahalle.objects.none()
            else:
                # Yeni obje oluşturulurken - boş
                kwargs['queryset'] = Mahalle.objects.none()
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def varsayilan_badge(self, obj):
        """Varsayılan adres gösterimi"""
        if obj.varsayilan:
            return format_html(
                '<span style="background-color: #ffc107; color: white; padding: 2px 8px; border-radius: 3px;">⭐ Varsayılan</span>'
            )
        return "-"
    varsayilan_badge.short_description = "Durum"


@admin.register(UrunYorum)
class UrunYorumAdmin(admin.ModelAdmin):
    list_display = ('urun', 'kullanici', 'yildiz_display', 'baslik', 'dogrulanmis_badge', 'onaylandi', 'olusturulma_tarihi')
    list_filter = ('yildiz', 'onaylandi', 'dogrulanmis_alisveris', 'olusturulma_tarihi')
    search_fields = ('urun__ad', 'kullanici__username', 'baslik', 'yorum')
    list_editable = ('onaylandi',)
    readonly_fields = ('olusturulma_tarihi',)

    fieldsets = (
        ('Yorum Bilgileri', {
            'fields': ('urun', 'kullanici', 'yildiz', 'baslik', 'yorum')
        }),
        ('Resimler', {
            'fields': ('resim1', 'resim2', 'resim3'),
            'classes': ('collapse',)
        }),
        ('Durum', {
            'fields': ('dogrulanmis_alisveris', 'onaylandi')
        }),
    )

    def yildiz_display(self, obj):
        """Yıldız gösterimi"""
        stars = '⭐' * obj.yildiz
        return format_html(
            '<span style="color: #ffc107; font-size: 1.2em;">{}</span>',
            stars
        )
    yildiz_display.short_description = "Puan"

    def dogrulanmis_badge(self, obj):
        """Doğrulanmış alışveriş gösterimi"""
        if obj.dogrulanmis_alisveris:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 2px 8px; border-radius: 3px;">✓ Doğrulanmış</span>'
            )
        return "-"
    dogrulanmis_badge.short_description = "Alışveriş"


@admin.register(Favori)
class FavoriAdmin(admin.ModelAdmin):
    list_display = ('kullanici', 'urun', 'ekleme_tarihi')
    list_filter = ('ekleme_tarihi',)
    search_fields = ('kullanici__username', 'urun__ad')


@admin.register(Kupon)
class KuponAdmin(admin.ModelAdmin):
    list_display = ('kod', 'kupon_tipi_badge', 'indirim_display', 'minimum_tutar', 'kullanim_sayisi', 'gecerlilik_display', 'aktif')
    list_filter = ('kupon_tipi', 'aktif', 'baslangic_tarihi', 'bitis_tarihi')
    search_fields = ('kod', 'aciklama')
    list_editable = ('aktif',)

    fieldsets = (
        ('Kupon Bilgileri', {
            'fields': ('kod', 'aciklama', 'kupon_tipi', 'indirim_degeri')
        }),
        ('Kullanım Koşulları', {
            'fields': ('minimum_tutar', 'maksimum_kullanim', 'kullanici_basina_limit')
        }),
        ('Geçerlilik', {
            'fields': ('baslangic_tarihi', 'bitis_tarihi', 'aktif')
        }),
    )

    def kupon_tipi_badge(self, obj):
        """Kupon tipi gösterimi"""
        colors = {
            'yuzde': '#007bff',
            'tutar': '#28a745',
            'ucretsiz_kargo': '#ffc107'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.kupon_tipi, '#6c757d'),
            obj.get_kupon_tipi_display()
        )
    kupon_tipi_badge.short_description = "Tip"

    def indirim_display(self, obj):
        """İndirim gösterimi"""
        if obj.kupon_tipi == 'yuzde':
            return format_html('<strong>%{}</strong>', obj.indirim_degeri)
        elif obj.kupon_tipi == 'tutar':
            return format_html('<strong>₺{}</strong>', obj.indirim_degeri)
        return "Ücretsiz Kargo"
    indirim_display.short_description = "İndirim"

    def gecerlilik_display(self, obj):
        """Geçerlilik gösterimi"""
        from django.utils import timezone
        now = timezone.now()
        if obj.baslangic_tarihi <= now <= obj.bitis_tarihi:
            return format_html(
                '<span style="color: green;">✓ Geçerli</span>'
            )
        elif now < obj.baslangic_tarihi:
            return format_html(
                '<span style="color: orange;">⏳ Başlamadı</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">✗ Süresi Doldu</span>'
            )
    gecerlilik_display.short_description = "Durum"


@admin.register(KuponKullanim)
class KuponKullanimAdmin(admin.ModelAdmin):
    list_display = ('kupon', 'siparis', 'indirim_tutari', 'kullanim_tarihi')
    list_filter = ('kullanim_tarihi',)
    search_fields = ('kupon__kod', 'siparis__kullanici__username')
    readonly_fields = ('kullanim_tarihi',)


@admin.register(KargoFirma)
class KargoFirmaAdmin(admin.ModelAdmin):
    list_display = ('ad', 'fiyat_badge', 'ucretsiz_badge', 'tahmini_sure_gun', 'sira', 'aktif')
    list_filter = ('aktif', 'tahmini_sure_gun')
    list_editable = ('aktif', 'sira')
    search_fields = ('ad',)
    ordering = ('sira', 'ad')

    fieldsets = (
        ('Firma Bilgileri', {
            'fields': ('ad', 'logo'),
            'description': 'Kargo firmasının temel bilgileri'
        }),
        ('Fiyatlandırma', {
            'fields': ('sabit_ucret', 'ucretsiz_kargo_limiti'),
            'description': 'Kargo ücreti ve ücretsiz kargo limiti ayarları'
        }),
        ('Teslimat Bilgileri', {
            'fields': ('tahmini_sure_gun',),
            'description': 'Tahmini teslimat süresi (gün cinsinden)'
        }),
        ('Sıralama ve Durum', {
            'fields': ('sira', 'aktif'),
            'description': 'Kargo firmasının sıralaması ve aktiflik durumu'
        }),
    )

    def fiyat_badge(self, obj):
        """Fiyat gösterimi"""
        return format_html(
            '<strong style="color: #007bff;">₺{}</strong>',
            obj.sabit_ucret
        )
    fiyat_badge.short_description = "Kargo Ücreti"
    fiyat_badge.admin_order_field = 'sabit_ucret'

    def ucretsiz_badge(self, obj):
        """Ücretsiz kargo limiti"""
        if obj.ucretsiz_kargo_limiti:
            return format_html(
                '<span style="color: #28a745;">₺{} üzeri ücretsiz</span>',
                obj.ucretsiz_kargo_limiti
            )
        return "-"
    ucretsiz_badge.short_description = "Ücretsiz Kargo"
    ucretsiz_badge.admin_order_field = 'ucretsiz_kargo_limiti'


@admin.register(SiparisDurum)
class SiparisDurumAdmin(admin.ModelAdmin):
    list_display = ('siparis', 'durum_badge', 'aciklama', 'olusturulma_tarihi')
    list_filter = ('durum', 'olusturulma_tarihi')
    search_fields = ('siparis__id', 'aciklama')
    readonly_fields = ('olusturulma_tarihi',)

    fieldsets = (
        ('Sipariş Bilgileri', {
            'fields': ('siparis', 'durum')
        }),
        ('Detaylar', {
            'fields': ('aciklama', 'kargo_takip_no')
        }),
    )

    def durum_badge(self, obj):
        """Durum gösterimi"""
        colors = {
            'beklemede': '#ffc107',
            'hazirlaniyor': '#17a2b8',
            'kargoda': '#007bff',
            'teslim_edildi': '#28a745',
            'iptal': '#dc3545'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.durum, '#6c757d'),
            obj.get_durum_display()
        )
    durum_badge.short_description = "Durum"