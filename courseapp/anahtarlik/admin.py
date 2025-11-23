# anahtarlik/admin.py

from django.contrib import admin, messages
from django import forms
from django.template.response import TemplateResponse
from django.urls import path
from django.shortcuts import redirect
from django.utils.html import format_html
from django.utils import timezone

from .models import (
    Sahip, EvcilHayvan, Alerji, SaglikKaydi, AsiTakvimi,
    IlacKaydi, AmeliyatKaydi, BeslenmeKaydi, KiloKaydi,
    SahipProPaket, SahipProAbonelik, Bildirim,
    HeroSlide, HizmetKarti, AnaSayfaAyar
)
from .dictionaries import Tur, Irk, Il, Ilce

from veteriner.models import Veteriner
from petshop.models import PetShop

import qrcode
from io import BytesIO
import base64




# ---------- Inline Modeller ----------
class AlerjiInline(admin.TabularInline):
    model = Alerji
    extra = 1
    fields = ('alerji_turu', 'aciklama', 'kaydedilme_tarihi')
    readonly_fields = ('kaydedilme_tarihi',)


class SaglikKaydiInline(admin.TabularInline):
    model = SaglikKaydi
    extra = 1
    fields = ('asi_turu', 'asi_tarihi', 'notlar')


class AsiTakvimiInline(admin.TabularInline):
    model = AsiTakvimi
    extra = 1
    fields = ('asi_turu', 'planlanan_tarih', 'tamamlandi', 'tamamlanma_tarihi', 'notlar')


class IlacKaydiInline(admin.TabularInline):
    model = IlacKaydi
    extra = 1
    fields = ('ilac_adi', 'baslangic_tarihi', 'bitis_tarihi', 'dozaj', 'notlar')


class AmeliyatKaydiInline(admin.TabularInline):
    model = AmeliyatKaydi
    extra = 1
    fields = ('ameliyat_turu', 'tarih', 'veteriner', 'notlar')


class BeslenmeKaydiInline(admin.TabularInline):
    model = BeslenmeKaydi
    extra = 1
    fields = ('besin_turu', 'tarih', 'miktar', 'notlar')


class KiloKaydiInline(admin.TabularInline):
    model = KiloKaydi
    extra = 1
    fields = ('kilo', 'tarih', 'notlar')


# ---------- Sözlükler: Tür, Cins, İl, İlçe ----------
class IrkInline(admin.TabularInline):
    model = Irk
    extra = 1
    fields = ('ad',)
    ordering = ('ad',)


@admin.register(Tur)
class TurAdmin(admin.ModelAdmin):
    search_fields = ("ad",)
    list_display = ("ad", "irk_sayisi", "evcil_hayvan_sayisi")
    inlines = [IrkInline]
    
    def irk_sayisi(self, obj):
        return obj.irklari.count()
    irk_sayisi.short_description = "Irk Sayısı"
    irk_sayisi.admin_order_field = None
    
    def evcil_hayvan_sayisi(self, obj):
        return obj.evcil_hayvanlar.count()
    evcil_hayvan_sayisi.short_description = "Evcil Hayvan Sayısı"
    evcil_hayvan_sayisi.admin_order_field = None


@admin.register(Irk)
class IrkAdmin(admin.ModelAdmin):
    list_display = ("ad", "tur", "evcil_hayvan_sayisi")
    list_filter = ("tur",)
    search_fields = ("ad", "tur__ad")
    ordering = ("tur__ad", "ad")
    
    def evcil_hayvan_sayisi(self, obj):
        return obj.evcil_hayvanlar.count()
    evcil_hayvan_sayisi.short_description = "Evcil Hayvan Sayısı"
    evcil_hayvan_sayisi.admin_order_field = None


class IlceInline(admin.TabularInline):
    model = Ilce
    extra = 1
    fields = ('ad',)
    ordering = ('ad',)


@admin.register(Il)
class IlAdmin(admin.ModelAdmin):
    search_fields = ("ad",)
    list_display = ("ad", "ilce_sayisi")
    inlines = [IlceInline]
    
    def ilce_sayisi(self, obj):
        return obj.ilceler.count()
    ilce_sayisi.short_description = "İlçe Sayısı"
    ilce_sayisi.admin_order_field = None


@admin.register(Ilce)
class IlceAdmin(admin.ModelAdmin):
    list_display = ("ad", "il", "sahip_sayisi")
    list_filter = ("il",)
    search_fields = ("ad", "il__ad")
    ordering = ("il__ad", "ad")
    
    def sahip_sayisi(self, obj):
        return obj.sahipleri.count()
    sahip_sayisi.short_description = "Sahip Sayısı"
    sahip_sayisi.admin_order_field = None


# ---------- Sahip ----------
@admin.register(Sahip)
class SahipAdmin(admin.ModelAdmin):
    list_display = (
        'kullanici', 'ad', 'soyad', 'il', 'ilce', 'telefon',
        'danisman_veteriner', 'danisman_atanma_tarihi', 'danisman_atanma_sebebi'
    )
    search_fields = (
        'kullanici__username', 'ad', 'soyad', 'telefon', 'il__ad', 'ilce__ad',
        'danisman_veteriner__ad'
    )
    list_filter = (
        'kullanici__is_active', 'il', 'ilce', 'danisman_atanma_sebebi',
        'danisman_atanma_tarihi'
    )
    readonly_fields = ('kullanici', 'danisman_atanma_tarihi')
    
    class Media:
        js = ('admin/js/veteriner_admin.js',)  # Aynı JavaScript dosyasını kullan
    
    fieldsets = (
        ('Genel Bilgiler', {
            'fields': ('kullanici', 'ad', 'soyad', 'telefon', 'yedek_telefon')
        }),
        ('Adres Bilgileri', {
            'fields': ('il', 'ilce', 'adres')
        }),
        ('Danışman Veteriner', {
            'fields': ('danisman_veteriner', 'danisman_atanma_tarihi', 'danisman_atanma_sebebi')
        }),
    )
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        İlçe alanını seçilen ile göre filtrele.
        """
        if db_field.name == "ilce":
            il_id = None
            
            # Edit modunda: mevcut nesnenin il'ini kullan
            if request.resolver_match.kwargs.get('object_id'):
                try:
                    obj_id = request.resolver_match.kwargs['object_id']
                    obj = Sahip.objects.get(pk=obj_id)
                    if obj.il:
                        il_id = obj.il.id
                except (Sahip.DoesNotExist, ValueError, KeyError):
                    pass
            
            # POST data'dan il_id al
            if not il_id and request.method == 'POST':
                il_id = request.POST.get('il')
            
            # İlçeleri filtrele
            if il_id:
                kwargs["queryset"] = Ilce.objects.filter(il_id=il_id).order_by('ad')
            else:
                kwargs["queryset"] = Ilce.objects.none()
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ---------- Evcil Hayvan ----------
@admin.register(EvcilHayvan)
class EvcilHayvanAdmin(admin.ModelAdmin):
    list_display = ('ad', 'tur', 'irk', 'sahip', 'kayip_durumu_colored', 'resim_preview')
    search_fields = ('ad', 'sahip__kullanici__username', 'tur__ad', 'irk__ad')
    list_filter = ('kayip_durumu', 'cinsiyet', 'tur', 'irk')
    inlines = [
        AlerjiInline, SaglikKaydiInline, AsiTakvimiInline,
        IlacKaydiInline, AmeliyatKaydiInline, BeslenmeKaydiInline, KiloKaydiInline
    ]
    fieldsets = (
        ('Genel Bilgiler', {
            'fields': ('ad', 'tur', 'irk', 'cinsiyet', 'dogum_tarihi', 'sahip', 'resim', 'resim_preview')
        }),
        ('Ek Bilgiler', {
            'fields': ('saglik_notu', 'beslenme_notu', 'genel_not', 'davranis_notu')
        }),
        ('Kayıp Durumu', {
            'fields': ('kayip_durumu', 'kayip_bildirim_tarihi', 'odul_miktari')
        }),
    )
    readonly_fields = ('kayip_bildirim_tarihi', 'resim_preview')

    def kayip_durumu_colored(self, obj):
        color = 'red' if obj.kayip_durumu else 'green'
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            'Kayıp' if obj.kayip_durumu else 'Güvende'
        )
    kayip_durumu_colored.short_description = 'Kayıp Durumu'

    def resim_preview(self, obj):
        if obj.resim:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover; border-radius: 50%;" />',
                obj.resim.url
            )
        return 'Resim Yok'
    resim_preview.short_description = 'Resim Önizleme'


# ---------- Diğer Basit Modeller ----------
@admin.register(Alerji)
class AlerjiAdmin(admin.ModelAdmin):
    list_display = ('evcil_hayvan', 'alerji_turu', 'kaydedilme_tarihi')
    search_fields = ('evcil_hayvan__ad', 'alerji_turu')
    list_filter = ('kaydedilme_tarihi',)


@admin.register(SaglikKaydi)
class SaglikKaydiAdmin(admin.ModelAdmin):
    list_display = ('evcil_hayvan', 'asi_turu', 'asi_tarihi')
    search_fields = ('evcil_hayvan__ad', 'asi_turu')
    list_filter = ('asi_tarihi',)


@admin.register(AsiTakvimi)
class AsiTakvimiAdmin(admin.ModelAdmin):
    list_display = ('evcil_hayvan', 'asi_turu', 'planlanan_tarih', 'tamamlandi')
    search_fields = ('evcil_hayvan__ad', 'asi_turu')
    list_filter = ('tamamlandi', 'planlanan_tarih')


@admin.register(IlacKaydi)
class IlacKaydiAdmin(admin.ModelAdmin):
    list_display = ('evcil_hayvan', 'ilac_adi', 'baslangic_tarihi', 'bitis_tarihi')
    search_fields = ('evcil_hayvan__ad', 'ilac_adi')
    list_filter = ('baslangic_tarihi',)


@admin.register(AmeliyatKaydi)
class AmeliyatKaydiAdmin(admin.ModelAdmin):
    list_display = ('evcil_hayvan', 'ameliyat_turu', 'tarih')
    search_fields = ('evcil_hayvan__ad', 'ameliyat_turu')
    list_filter = ('tarih',)


@admin.register(BeslenmeKaydi)
class BeslenmeKaydiAdmin(admin.ModelAdmin):
    list_display = ('evcil_hayvan', 'besin_turu', 'tarih', 'miktar')
    search_fields = ('evcil_hayvan__ad', 'besin_turu')
    list_filter = ('tarih',)


@admin.register(KiloKaydi)
class KiloKaydiAdmin(admin.ModelAdmin):
    list_display = ('evcil_hayvan', 'kilo', 'tarih')
    search_fields = ('evcil_hayvan__ad',)
    list_filter = ('tarih',)






























# --- Kullanıcı Admini: tür sütunu + filtre ---
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class KullaniciTuruFilter(SimpleListFilter):
    title = "kullanıcı türü"
    parameter_name = "kullanici_turu"

    def lookups(self, request, model_admin):
        return (
            ("sahip", "QR Sahibi"),
            ("veteriner", "Veteriner"),
            ("petshop", "Petshop"),
            ("yok", "Profil yok"),
        )

    def queryset(self, request, queryset):
        v = self.value()
        if v == "sahip":
            return queryset.filter(sahip__isnull=False)  # OneToOneField (reverse adı: sahip)
        if v == "veteriner":
            return queryset.filter(veteriner_profili__isnull=False)  # related_name
        if v == "petshop":
            return queryset.filter(petshop_profili__isnull=False)     # related_name
        if v == "yok":
            return queryset.filter(
                sahip__isnull=True,
                veteriner_profili__isnull=True,
                petshop_profili__isnull=True,
            )
        return queryset

def kullanici_turu(obj: User):
    if hasattr(obj, "veteriner_profili"):
        return "Veteriner"
    if hasattr(obj, "petshop_profili"):
        return "Petshop"
    if hasattr(obj, "sahip"):
        return "QR Sahibi"
    return "—"
kullanici_turu.short_description = "Tür"
kullanici_turu.admin_order_field = None

# Varsayılan User adminini kaldırıp kendi sürümümüzü kaydediyoruz
admin.site.unregister(User)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # mevcut sütunlara "kullanici_turu" ekle
    list_display = BaseUserAdmin.list_display + ("kullanici_turu",)
    # mevcut filtrelere özel filtreyi ekle
    list_filter = BaseUserAdmin.list_filter + (KullaniciTuruFilter,)

    def kullanici_turu(self, obj):
        return kullanici_turu(obj)


@admin.register(SahipProPaket)
class SahipProPaketAdmin(admin.ModelAdmin):
    list_display = ['paket_adi', 'fiyat', 'ilan_hakki', 'sure_gun', 'aktif', 'siralama']
    list_filter = ['aktif', 'asi_hatirlatma', 'veteriner_randevu', 'ilac_takibi']
    search_fields = ['paket_adi', 'aciklama']
    ordering = ['siralama', 'fiyat']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('paket_adi', 'aciklama', 'fiyat', 'sure_gun', 'ilan_hakki', 'siralama', 'renk', 'aktif')
        }),
        ('Pro Özellikler', {
            'fields': (
                'asi_hatirlatma', 'veteriner_randevu', 'ilac_takibi', 
                'beslenme_programi', 'finansal_takip', 'egitim_programi'
            ),
            'classes': ('collapse',)
        }),
        ('Fotoğraf Ayarları', {
            'fields': ('foto_galeri_limit',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(SahipProAbonelik)
class SahipProAbonelikAdmin(admin.ModelAdmin):
    list_display = ['sahip', 'paket', 'baslangic_tarihi', 'bitis_tarihi', 'kalan_gun', 'aktif_mi', 'aktif']
    list_filter = ['aktif', 'paket', 'baslangic_tarihi', 'bitis_tarihi']
    search_fields = ['sahip__user__first_name', 'sahip__user__last_name', 'sahip__user__email']
    readonly_fields = ['olusturulma_tarihi', 'kalan_gun', 'aktif_mi']
    date_hierarchy = 'baslangic_tarihi'
    
    fieldsets = (
        ('Abonelik Bilgileri', {
            'fields': ('sahip', 'paket', 'baslangic_tarihi', 'bitis_tarihi', 'aktif')
        }),
        ('Durum Bilgileri', {
            'fields': ('kalan_gun', 'aktif_mi', 'olusturulma_tarihi'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sahip__kullanici', 'paket')
    
    def kalan_gun(self, obj):
        return f"{obj.kalan_gun} gün"
    kalan_gun.short_description = "Kalan Gün"
    
    def aktif_mi(self, obj):
        if obj.aktif_mi:
            return "✅ Aktif"
        return "❌ Pasif"
    aktif_mi.short_description = "Durum"


@admin.register(Bildirim)
class BildirimAdmin(admin.ModelAdmin):
    list_display = ('sahip', 'baslik', 'tur', 'oncelik', 'okundu_badge', 'saklama_badge', 'olusturma_zamani')
    list_filter = ('tur', 'oncelik', 'okundu', 'olusturma_zamani')
    search_fields = ('sahip__kullanici__username', 'sahip__kullanici__first_name', 'baslik', 'mesaj')
    readonly_fields = ('olusturma_zamani', 'tarama_link', 'saklama_bilgisi')
    ordering = ('-olusturma_zamani',)
    
    def okundu_badge(self, obj):
        if obj.okundu:
            return format_html('<span style="background:#28a745;color:white;padding:4px 10px;border-radius:4px;font-weight:bold;">✅ Okundu</span>')
        return format_html('<span style="background:#dc3545;color:white;padding:4px 10px;border-radius:4px;font-weight:bold;">❌ Okunmadı</span>')
    okundu_badge.short_description = "Durum"
    
    def saklama_badge(self, obj):
        from django.utils import timezone
        from datetime import timedelta
        
        kalan_gun = obj.saklama_suresi - (timezone.now() - obj.olusturma_zamani).days
        
        if kalan_gun <= 0:
            return format_html('<span style="background:#dc3545;color:white;padding:4px 10px;border-radius:4px;font-weight:bold;">🗑️ Silinecek</span>')
        elif kalan_gun <= 3:
            return format_html('<span style="background:#ffc107;color:black;padding:4px 10px;border-radius:4px;font-weight:bold;">⚠️ {0} gün</span>', kalan_gun)
        else:
            return format_html('<span style="background:#17a2b8;color:white;padding:4px 10px;border-radius:4px;font-weight:bold;">📅 {0} gün</span>', kalan_gun)
    saklama_badge.short_description = "Saklama"
    
    def saklama_bilgisi(self, obj):
        return format_html(
            '<strong>Saklama Süresi:</strong> {} gün<br>'
            '<strong>Silinme Tarihi:</strong> {}<br>'
            '<strong>Durum:</strong> {}',
            obj.saklama_suresi,
            (obj.olusturma_zamani + timedelta(days=obj.saklama_suresi)).strftime('%d.%m.%Y %H:%M'),
            'Silinecek' if obj.silinecek_mi else 'Güvende'
        )
    saklama_bilgisi.short_description = "Saklama Bilgileri"
    
    def tarama_link(self, obj):
        if obj.tarama:
            return format_html(
                '<a href="/admin/etiket/etikettarama/{}/change/" target="_blank">📊 Tarama Detayı</a>',
                obj.tarama.id
            )
        return "-"
    tarama_link.short_description = "İlgili Tarama"


# ========== Ana Sayfa İçerik Yönetimi ==========

@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ('baslik', 'sira', 'aktif', 'resim_preview', 'buton_bilgisi', 'olusturma_tarihi')
    list_filter = ('aktif', 'olusturma_tarihi')
    search_fields = ('baslik', 'aciklama')
    ordering = ('sira', '-olusturma_tarihi')
    list_editable = ('sira', 'aktif')
    readonly_fields = ('resim_preview_large', 'olusturma_tarihi', 'guncelleme_tarihi')
    
    actions = ['aktif_et_action', 'pasif_et_action']
    
    def aktif_et_action(self, request, queryset):
        """Seçili slide'ları aktif et"""
        updated = queryset.update(aktif=True)
        self.message_user(request, f'✅ {updated} slide aktif edildi.', messages.SUCCESS)
    aktif_et_action.short_description = "✅ Aktif et"
    
    def pasif_et_action(self, request, queryset):
        """Seçili slide'ları pasif et"""
        updated = queryset.update(aktif=False)
        self.message_user(request, f'❌ {updated} slide pasif edildi.', messages.WARNING)
    pasif_et_action.short_description = "❌ Pasif et"

    fieldsets = (
        ('İçerik', {
            'fields': ('baslik', 'aciklama', 'sira', 'aktif')
        }),
        ('Görsel', {
            'fields': ('arka_plan_resim', 'arka_plan_resim_mobil', 'resim_preview_large', 'arka_plan_renk'),
            'description': '🖥️ Masaüstü için yatay görsel (1920x1080) | 📱 Mobil için dikey görsel (1080x1920) yükleyin'
        }),
        ('Butonlar', {
            'fields': ('buton_1_metin', 'buton_1_url', 'buton_2_metin', 'buton_2_url'),
            'classes': ('collapse',)
        }),
        ('Tarihler', {
            'fields': ('olusturma_tarihi', 'guncelleme_tarihi'),
            'classes': ('collapse',)
        }),
    )

    def resim_preview(self, obj):
        if obj.arka_plan_resim:
            return format_html(
                '<img src="{}" width="80" height="45" style="object-fit: cover; border-radius: 6px;" />',
                obj.arka_plan_resim.url
            )
        return format_html('<span style="color: #999;">📷 Resim Yok</span>')
    resim_preview.short_description = 'Resim'

    def resim_preview_large(self, obj):
        html = '<div style="display: flex; gap: 20px; flex-wrap: wrap;">'

        # Masaüstü görsel
        if obj.arka_plan_resim:
            html += '''
                <div style="flex: 1; min-width: 300px;">
                    <h4 style="margin-bottom: 10px; color: #5B9BD5;">🖥️ Masaüstü Görseli</h4>
                    <img src="{}" style="max-width: 100%; height: auto; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" />
                </div>
            '''.format(obj.arka_plan_resim.url)
        else:
            html += '<div style="flex: 1; min-width: 300px;"><h4 style="color: #999;">🖥️ Masaüstü görseli yok</h4></div>'

        # Mobil görsel
        if obj.arka_plan_resim_mobil:
            html += '''
                <div style="flex: 1; min-width: 300px;">
                    <h4 style="margin-bottom: 10px; color: #70C1B3;">📱 Mobil Görseli</h4>
                    <img src="{}" style="max-width: 100%; height: auto; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" />
                </div>
            '''.format(obj.arka_plan_resim_mobil.url)
        else:
            html += '<div style="flex: 1; min-width: 300px;"><h4 style="color: #999;">📱 Mobil görseli yok</h4></div>'

        html += '</div>'

        if not obj.arka_plan_resim and not obj.arka_plan_resim_mobil:
            return format_html('<span style="color: #999;">Henüz resim yüklenmemiş</span>')

        return format_html(html)
    resim_preview_large.short_description = 'Resim Önizleme'

    def buton_bilgisi(self, obj):
        butonlar = []
        if obj.buton_1_metin:
            butonlar.append(f'🔵 {obj.buton_1_metin}')
        if obj.buton_2_metin:
            butonlar.append(f'🔵 {obj.buton_2_metin}')
        return ' | '.join(butonlar) if butonlar else '—'
    buton_bilgisi.short_description = 'Butonlar'


@admin.register(HizmetKarti)
class HizmetKartiAdmin(admin.ModelAdmin):
    list_display = ('baslik', 'ikon_preview', 'sira', 'aktif', 'buton_metin', 'animasyon_gecikmesi', 'olusturma_tarihi')
    list_filter = ('aktif', 'ikon', 'olusturma_tarihi')
    search_fields = ('baslik', 'aciklama', 'buton_metin')
    ordering = ('sira', '-olusturma_tarihi')
    list_editable = ('sira', 'aktif')
    readonly_fields = ('olusturma_tarihi', 'guncelleme_tarihi')
    
    actions = ['aktif_et_action', 'pasif_et_action']
    
    def aktif_et_action(self, request, queryset):
        """Seçili kartları aktif et"""
        updated = queryset.update(aktif=True)
        self.message_user(request, f'✅ {updated} kart aktif edildi.', messages.SUCCESS)
    aktif_et_action.short_description = "✅ Aktif et"
    
    def pasif_et_action(self, request, queryset):
        """Seçili kartları pasif et"""
        updated = queryset.update(aktif=False)
        self.message_user(request, f'❌ {updated} kart pasif edildi.', messages.WARNING)
    pasif_et_action.short_description = "❌ Pasif et"

    fieldsets = (
        ('İçerik', {
            'fields': ('baslik', 'aciklama', 'ikon', 'sira', 'aktif')
        }),
        ('Buton', {
            'fields': ('buton_metin', 'buton_url')
        }),
        ('Animasyon', {
            'fields': ('animasyon_gecikmesi',),
            'classes': ('collapse',)
        }),
        ('Tarihler', {
            'fields': ('olusturma_tarihi', 'guncelleme_tarihi'),
            'classes': ('collapse',)
        }),
    )

    def ikon_preview(self, obj):
        return format_html(
            '<i class="{}" style="font-size: 24px; color: #5B9BD5;"></i>',
            obj.ikon
        )
    ikon_preview.short_description = 'İkon'

    class Media:
        css = {
            'all': ('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css',)
        }


@admin.register(AnaSayfaAyar)
class AnaSayfaAyarAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'slide_gecis_suresi', 'slide_animasyon', 'guncelleme_tarihi')
    readonly_fields = ('olusturma_tarihi', 'guncelleme_tarihi')

    fieldsets = (
        ('Hizmetler Bölümü', {
            'fields': ('hizmetler_baslik', 'hizmetler_aciklama')
        }),
        ('Slider Ayarları', {
            'fields': ('slide_gecis_suresi', 'slide_animasyon')
        }),
        ('Tarihler', {
            'fields': ('olusturma_tarihi', 'guncelleme_tarihi'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        # Singleton - sadece bir kayıt olmalı
        return not AnaSayfaAyar.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Silmeyi engelle
        return False
    
    def changelist_view(self, request, extra_context=None):
        """Ana sayfa ayarlarını listele"""
        extra_context = extra_context or {}
        
        # İstatistikler
        extra_context['istatistikler'] = {
            'toplam_slide': HeroSlide.objects.count(),
            'aktif_slide': HeroSlide.objects.filter(aktif=True).count(),
            'toplam_kart': HizmetKarti.objects.count(),
            'aktif_kart': HizmetKarti.objects.filter(aktif=True).count(),
        }
        
        response = super().changelist_view(request, extra_context)
        return response
