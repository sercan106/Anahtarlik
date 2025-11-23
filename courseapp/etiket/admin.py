from django.contrib import admin, messages
from django import forms
from django.core.exceptions import ValidationError
from django.template.response import TemplateResponse
from django.urls import path
from django.shortcuts import redirect
from django.utils.html import format_html
from django.utils import timezone
from .models import Etiket, EtiketKategori, EtiketKategoriFotografi, EtiketTarama, EtiketYenileme, EtiketYenilemeFiyati, KANAL_SECENEKLERI
from veteriner.models import Veteriner
from petshop.models import PetShop
import qrcode
from io import BytesIO
import base64

@admin.register(Etiket)
class EtiketAdmin(admin.ModelAdmin):
    list_display = (
        'seri_numarasi', 'evcil_hayvan', 'aktif',
        'kanal', 'kategori', 'satici_veteriner', 'satici_petshop', 'tahsis_tarihi',
        'son_kullanma_tarihi', 'qr_kod_url_link', 'olusturulma_tarihi'
    )
    readonly_fields = ('etiket_id', 'seri_numarasi', 'qr_gorsel_onizleme', 'qr_kod_url', 'tahsis_tarihi')
    search_fields = ('seri_numarasi',)
    list_filter = ('aktif', 'kilitli', 'kanal', 'kategori', 'satici_veteriner', 'satici_petshop')
    actions = ['tahsis_aksiyonu']

    def get_fieldsets(self, request, obj=None):
        if obj:  # Mevcut etiket düzenleniyor
            return (
                ('Temel', {'fields': ('seri_numarasi', 'evcil_hayvan', 'aktif', 'kilitli')}),
                ('Kategori', {'fields': ('kategori',)}),
                ('QR', {'fields': ('etiket_id', 'qr_kod_url', 'qr_gorsel_onizleme')}),
                ('Tahsis', {'fields': ('kanal', 'satici_veteriner', 'satici_petshop', 'tahsis_tarihi')}),
                ('Süre', {'fields': ('son_kullanma_tarihi',)}),
                ('Adres Bilgileri', {'fields': ('adres_bayi', 'adres_kullanici')}),
            )
        else:  # Yeni etiket oluşturuluyor
            return (
                ('Temel', {'fields': ('evcil_hayvan', 'aktif', 'kilitli')}),
                ('Kategori', {'fields': ('kategori',)}),
                ('QR', {'fields': ('etiket_id', 'qr_kod_url', 'qr_gorsel_onizleme')}),
                ('Tahsis', {'fields': ('kanal', 'satici_veteriner', 'satici_petshop', 'tahsis_tarihi')}),
                ('Süre', {'fields': ('son_kullanma_tarihi',)}),
                ('Adres Bilgileri', {'fields': ('adres_bayi', 'adres_kullanici')}),
            )

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        # Tahsis yapıldıysa kanal ve partnerler kilitlensin (taşıma yasak)
        if obj and obj.tahsis_tarihi:
            ro += ['kanal', 'satici_veteriner', 'satici_petshop']
        return ro
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Yeni etiket oluşturuluyorsa seri numarası alanını tamamen kaldır
        if not obj:  # Yeni etiket oluşturuluyor
            if 'seri_numarasi' in form.base_fields:
                del form.base_fields['seri_numarasi']
        return form

    def save_model(self, request, obj, form, change):
        """Admin ekranında etiket oluşturma ve tahsis işlemleri."""
        if not change:
            # Yeni etiket oluşturuluyor - seri numarası otomatik atanacak
            super().save_model(request, obj, form, change)
            return

        prev = Etiket.objects.get(pk=obj.pk)
        super().save_model(request, obj, form, change)

        # İlk kez tahsis girildiyse (önceden yoktu, şimdi var)
        if prev.tahsis_tarihi is None and obj.kanal:
            obj.tahsis_tarihi = timezone.now()
            obj.save(update_fields=['tahsis_tarihi'])
            obj._increase_allocation_counter()

    # ---- QR yardımcıları ----
    def qr_kod_url_link(self, obj):
        if obj.qr_kod_url:
            return format_html('<a href="{}" target="_blank">QR Link</a>', obj.qr_kod_url)
        return "Yok"
    qr_kod_url_link.short_description = "QR Kod URL"

    def qr_gorsel_onizleme(self, obj):
        if not obj.qr_kod_url:
            return "Henüz QR URL oluşturulmamış."
        qr = qrcode.make(obj.qr_kod_url)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        base64_image = base64.b64encode(buffer.getvalue()).decode()
        img_html = f'<img src="data:image/png;base64,{base64_image}" width="200" height="200" /><br>'
        download_link = (
            f'<a download="qr_{obj.seri_numarasi}.png" '
            f'href="data:image/png;base64,{base64_image}" '
            f'class="button btn btn-sm btn-success mt-2">İndir</a>'
        )
        return format_html(img_html + download_link)
    qr_gorsel_onizleme.short_description = "QR Önizleme & İndir"

    # ---- Toplu tahsis ----
    def get_urls(self):
        urls = super().get_urls()
        my = [
            path('tahsis/', self.admin_site.admin_view(self.tahsis_view), name='etiket_tahsis'),
            path('toplu-olustur/', self.admin_site.admin_view(self.toplu_olustur_view), name='etiket_toplu_olustur')
        ]
        return my + urls

    def tahsis_aksiyonu(self, request, queryset):
        selected = request.POST.getlist('_selected_action')
        if not selected:
            self.message_user(request, "Etiket seçmediniz.", level=messages.WARNING)
            return
        return redirect(f"{request.path}tahsis/?ids={','.join(selected)}")
    tahsis_aksiyonu.short_description = "Seçili etiketleri tahsis et"


    def tahsis_view(self, request):
        class TahsisForm(forms.Form):
            kanal = forms.ChoiceField(choices=KANAL_SECENEKLERI, label="Kanal")
            veteriner = forms.ModelChoiceField(
                queryset=Veteriner.objects.filter(aktif=True),
                required=False,
                label="Veteriner"
            )
            petshop = forms.ModelChoiceField(
                queryset=PetShop.objects.filter(aktif=True),
                required=False,
                label="Petshop"
            )

            def clean(self):
                c = super().clean()
                k = c.get('kanal')
                v = c.get('veteriner')
                p = c.get('petshop')
                if k == 'VET' and not v:
                    self.add_error('veteriner', "Veteriner seçin.")
                if k == 'SHOP' and not p:
                    self.add_error('petshop', "Petshop seçin.")
                if k == 'ONLINE' and (v or p):
                    raise forms.ValidationError("Online tahsiste partner seçmeyin.")
                return c

        ids = request.GET.get('ids') or request.POST.get('ids')
        if not ids:
            self.message_user(request, "Seçim yok.", level=messages.ERROR)
            return redirect('..')

        id_list = [int(x) for x in ids.split(',') if x]
        qs = Etiket.objects.filter(pk__in=id_list)

        if request.method == 'POST':
            form = TahsisForm(request.POST)
            if form.is_valid():
                k = form.cleaned_data['kanal']
                v = form.cleaned_data.get('veteriner')
                p = form.cleaned_data.get('petshop')

                done = 0
                skipped = 0
                for e in qs:
                    try:
                        e.tahsis_et(k, veteriner=v, petshop=p)
                        done += 1
                    except ValidationError as ve:
                        # Zaten tahsisli olanlar için
                        skipped += 1
                    except Exception as ex:
                        # Diğer hatalar için
                        skipped += 1

                if done > 0:
                    self.message_user(
                        request,
                        f"{done} etiket başarıyla tahsis edildi/güncellendi.",
                        level=messages.SUCCESS
                    )
                if skipped > 0:
                    self.message_user(
                        request,
                        f"{skipped} etiket işlenirken hata oluştu.",
                        level=messages.WARNING
                    )
                return redirect('../')
        else:
            form = TahsisForm()

        ctx = dict(
            self.admin_site.each_context(request),
            title="Etiket Tahsis",
            form=form,
            ids=ids,
            queryset_display=qs[:50],
            total_count=qs.count(),
        )
        return TemplateResponse(request, 'admin/etiket_tahsis.html', ctx)

    def toplu_olustur_view(self, request):
        class TopluOlusturForm(forms.Form):
            adet = forms.IntegerField(
                min_value=1, 
                max_value=100, 
                label="Oluşturulacak Etiket Sayısı",
                help_text="1-100 arası sayı girin"
            )
            kanal = forms.ChoiceField(
                choices=KANAL_SECENEKLERI, 
                label="Kanal",
                initial='TAHSISSIZ'
            )
            veteriner = forms.ModelChoiceField(
                queryset=Veteriner.objects.filter(aktif=True),
                required=False,
                label="Veteriner"
            )
            petshop = forms.ModelChoiceField(
                queryset=PetShop.objects.filter(aktif=True),
                required=False,
                label="Petshop"
            )

            def clean(self):
                c = super().clean()
                k = c.get('kanal')
                v = c.get('veteriner')
                p = c.get('petshop')
                if k == 'VET' and not v:
                    self.add_error('veteriner', "Veteriner seçin.")
                if k == 'SHOP' and not p:
                    self.add_error('petshop', "Petshop seçin.")
                if k in ['ONLINE', 'TAHSISSIZ'] and (v or p):
                    raise forms.ValidationError("Online/Tahsissiz kanalda partner seçmeyin.")
                return c

        if request.method == 'POST':
            form = TopluOlusturForm(request.POST)
            if form.is_valid():
                adet = form.cleaned_data['adet']
                kanal = form.cleaned_data['kanal']
                veteriner = form.cleaned_data.get('veteriner')
                petshop = form.cleaned_data.get('petshop')
                
                olusturulan = 0
                for i in range(adet):
                    try:
                        etiket = Etiket.objects.create(
                            kanal=kanal,
                            satici_veteriner=veteriner,
                            satici_petshop=petshop
                        )
                        olusturulan += 1
                    except Exception as e:
                        messages.error(request, f"Etiket {i+1} oluşturulurken hata: {e}")
                        break

                self.message_user(
                    request,
                    f"{olusturulan} adet etiket başarıyla oluşturuldu.",
                    level=messages.SUCCESS
                )
                return redirect('../')
        else:
            form = TopluOlusturForm()

        ctx = dict(
            self.admin_site.each_context(request),
            title="Toplu Etiket Oluştur",
            form=form,
        )
        return TemplateResponse(request, 'admin/etiket_toplu_olustur.html', ctx)
    
    def changelist_view(self, request, extra_context=None):
        """Admin listesine toplu oluşturma butonu ekle"""
        extra_context = extra_context or {}
        extra_context['toplu_olustur_url'] = f"{request.path}toplu-olustur/"
        return super().changelist_view(request, extra_context)


class EtiketKategoriFotografiInline(admin.TabularInline):
    model = EtiketKategoriFotografi
    extra = 1
    fields = ('fotograf', 'baslik', 'sira', 'aktif')
    ordering = ('sira',)


@admin.register(EtiketKategori)
class EtiketKategoriAdmin(admin.ModelAdmin):
    list_display = ('ad', 'renk_goster', 'aktif', 'etiket_sayisi', 'fotograf_sayisi', 'olusturulma_tarihi')
    list_filter = ('aktif', 'olusturulma_tarihi')
    search_fields = ('ad', 'aciklama')
    ordering = ('ad',)
    inlines = [EtiketKategoriFotografiInline]
    
    fieldsets = (
        ('Genel Bilgiler', {
            'fields': ('ad', 'aciklama', 'aktif')
        }),
        ('Görünüm', {
            'fields': ('renk',),
            'description': 'Kategori rengi (hex format: #ff0000)'
        }),
    )
    
    def renk_goster(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            obj.renk, obj.renk
        )
    renk_goster.short_description = "Renk"
    renk_goster.admin_order_field = "renk"
    
    def etiket_sayisi(self, obj):
        return obj.etiketler.count()
    etiket_sayisi.short_description = "Etiket Sayısı"
    etiket_sayisi.admin_order_field = None
    
    def fotograf_sayisi(self, obj):
        return obj.fotograflar.count()
    fotograf_sayisi.short_description = "Fotoğraf Sayısı"
    fotograf_sayisi.admin_order_field = None


@admin.register(EtiketKategoriFotografi)
class EtiketKategoriFotografiAdmin(admin.ModelAdmin):
    list_display = ('kategori', 'fotograf_onizleme', 'baslik', 'sira', 'aktif', 'olusturulma_tarihi')
    list_filter = ('kategori', 'aktif', 'olusturulma_tarihi')
    search_fields = ('kategori__ad', 'baslik', 'aciklama')
    ordering = ('kategori__ad', 'sira', '-olusturulma_tarihi')
    
    fieldsets = (
        ('Genel Bilgiler', {
            'fields': ('kategori', 'baslik', 'aciklama', 'aktif')
        }),
        ('Fotoğraf', {
            'fields': ('fotograf', 'sira'),
            'description': 'Fotoğraf yükleyin ve görüntüleme sırasını belirleyin'
        }),
    )
    
    def fotograf_onizleme(self, obj):
        if obj.fotograf:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px; border-radius: 5px;" />',
                obj.fotograf.url
            )
        return "-"
    fotograf_onizleme.short_description = "Fotoğraf Önizleme"
    fotograf_onizleme.admin_order_field = None


@admin.register(EtiketTarama)
class EtiketTaramaAdmin(admin.ModelAdmin):
    list_display = ('etiket', 'tarama_zamani', 'lokasyon_badge', 'bulan_badge', 'email_badge')
    list_filter = ('email_gonderildi', 'tarama_zamani')
    search_fields = ('etiket__seri_numarasi', 'bulan_isim', 'bulan_telefon', 'bulan_email', 'ip_sehir')
    readonly_fields = ('tarama_zamani', 'email_gonderim_zamani', 'harita_link')
    ordering = ('-tarama_zamani',)
    
    fieldsets = (
        ('Etiket Bilgisi', {
            'fields': ('etiket', 'tarama_zamani')
        }),
        ('GPS Lokasyon', {
            'fields': ('gps_latitude', 'gps_longitude', 'gps_dogruluk', 'harita_link'),
            'classes': ('collapse',)
        }),
        ('IP Lokasyon', {
            'fields': ('ip_adresi', 'ip_sehir', 'ip_ulke', 'ip_lokasyon_text'),
            'classes': ('collapse',)
        }),
        ('Bulan Kişi Bilgileri', {
            'fields': ('bulan_isim', 'bulan_telefon', 'bulan_email', 'bulan_mesaj')
        }),
        ('Teknik Detaylar', {
            'fields': ('user_agent', 'referrer', 'tarayici_dili'),
            'classes': ('collapse',)
        }),
        ('Bildirim Durumu', {
            'fields': ('email_gonderildi', 'email_gonderim_zamani')
        }),
    )
    
    def lokasyon_badge(self, obj):
        """Renkli lokasyon badge'i"""
        if obj.gps_latitude and obj.gps_longitude:
            dogruluk = f"±{obj.gps_dogruluk:.0f}m" if obj.gps_dogruluk else ""
            return format_html(
                '<span style="background:#28a745;color:white;padding:4px 10px;border-radius:4px;font-weight:bold;">🛰️ GPS</span> '
                '<small style="color:#666;">{:.4f}, {:.4f} {}</small>',
                obj.gps_latitude, obj.gps_longitude, dogruluk
            )
        elif obj.ip_sehir:
            return format_html(
                '<span style="background:#ffc107;color:black;padding:4px 10px;border-radius:4px;font-weight:bold;">🌐 IP</span> '
                '<small style="color:#666;">{}, {}</small>',
                obj.ip_sehir, obj.ip_ulke
            )
        return format_html(
            '<span style="background:#dc3545;color:white;padding:4px 10px;border-radius:4px;">❌ Yok</span>'
        )
    lokasyon_badge.short_description = "Lokasyon"
    
    def bulan_badge(self, obj):
        """Bulan kişi badge'i"""
        if obj.has_bulan_bilgisi():
            return format_html(
                '<span style="background:#17a2b8;color:white;padding:4px 10px;border-radius:4px;font-weight:bold;">👤 {}</span>',
                obj.bulan_isim or obj.bulan_telefon or obj.bulan_email
            )
        return format_html(
            '<span style="background:#6c757d;color:white;padding:4px 10px;border-radius:4px;">-</span>'
        )
    bulan_badge.short_description = "Bulan Kişi"
    
    def email_badge(self, obj):
        """E-posta durumu badge'i"""
        if obj.email_gonderildi:
            return format_html(
                '<span style="background:#28a745;color:white;padding:4px 10px;border-radius:4px;font-weight:bold;">✅ Gönderildi</span> '
                '<small style="color:#666;">{}</small>',
                obj.email_gonderim_zamani.strftime('%H:%M') if obj.email_gonderim_zamani else ''
            )
        return format_html(
            '<span style="background:#dc3545;color:white;padding:4px 10px;border-radius:4px;">❌ Bekliyor</span>'
        )
    email_badge.short_description = "E-posta Durumu"
    
    def harita_link(self, obj):
        url = obj.get_google_maps_url()
        if url:
            return format_html(
                '<a href="{}" target="_blank" class="button">🗺️ Google Maps\'te Aç</a>',
                url
            )
        return "Lokasyon bilgisi yok"
    harita_link.short_description = "Harita"


# ============= KÜNYE YENİLEME ADMIN =============

@admin.register(EtiketYenilemeFiyati)
class EtiketYenilemeFiyatiAdmin(admin.ModelAdmin):
    """Künye yenileme fiyatlandırması admin paneli - Kategori fark etmeksizin genel fiyatlar"""
    
    list_display = (
        'sure_gun_display', 'fiyat', 'veteriner_indirim_yuzde', 
        'petshop_indirim_yuzde', 'aktif', 'sira', 'olusturma_tarihi'
    )
    list_filter = ('aktif', 'sure_gun', 'olusturma_tarihi')
    search_fields = ('sure_gun',)
    ordering = ('sira', 'sure_gun')
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('sure_gun', 'fiyat', 'aktif', 'sira'),
            'description': 'Kategori fark etmeksizin tüm etiketler için geçerli fiyatlar'
        }),
        ('İndirimler', {
            'fields': ('veteriner_indirim_yuzde', 'petshop_indirim_yuzde'),
            'description': 'Kullanıcı tipine göre indirim yüzdeleri'
        }),
    )
    
    def get_fieldsets(self, request, obj=None):
        """Kategori alanını gizle"""
        fieldsets = super().get_fieldsets(request, obj)
        return fieldsets
    
    def get_form(self, request, obj=None, **kwargs):
        """Form'da kategori alanını gizle"""
        form = super().get_form(request, obj, **kwargs)
        if 'etiket_kategori' in form.base_fields:
            form.base_fields['etiket_kategori'].widget = forms.HiddenInput()
        return form
    
    def save_model(self, request, obj, form, change):
        """Kaydetme sırasında kategori'yi None yap"""
        obj.etiket_kategori = None  # Her zaman genel fiyat
        super().save_model(request, obj, form, change)
    
    def sure_gun_display(self, obj):
        """Süre gösterimi - Sınırsız için özel gösterim"""
        if obj.sure_gun == 9999:
            return "Sınırsız"
        return f"{obj.sure_gun} Gün"
    sure_gun_display.short_description = "Süre"
    sure_gun_display.admin_order_field = 'sure_gun'
    
    def get_queryset(self, request):
        # Sadece genel fiyatları göster (kategori=None)
        return super().get_queryset(request).filter(etiket_kategori__isnull=True)


@admin.register(EtiketYenileme)
class EtiketYenilemeAdmin(admin.ModelAdmin):
    """Künye yenileme işlemleri admin paneli"""
    
    list_display = (
        'etiket', 'kullanici', 'yenileme_ucreti', 'odeme_durumu', 
        'talep_tarihi', 'odeme_tarihi', 'yeni_bitis_tarihi', 'aktif'
    )
    list_filter = ('odeme_durumu', 'aktif', 'talep_tarihi', 'odeme_tarihi')
    search_fields = ('etiket__seri_numarasi', 'kullanici__username', 'kullanici__email')
    readonly_fields = ('talep_tarihi', 'odeme_tarihi', 'yeni_bitis_tarihi', 'stripe_payment_intent_id', 'stripe_session_id')
    ordering = ('-talep_tarihi',)
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('etiket', 'kullanici', 'aktif')
        }),
        ('Ödeme Bilgileri', {
            'fields': ('yenileme_ucreti', 'odeme_durumu', 'yenileme_suresi_gun')
        }),
        ('Stripe Bilgileri', {
            'fields': ('stripe_payment_intent_id', 'stripe_session_id'),
            'classes': ('collapse',)
        }),
        ('Tarihler', {
            'fields': ('talep_tarihi', 'odeme_tarihi', 'yeni_bitis_tarihi')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('etiket', 'kullanici')
    
    actions = ['odeme_onayla', 'odeme_iptal']
    
    def odeme_onayla(self, request, queryset):
        """Seçili yenilemeleri ödendi olarak işaretle"""
        for yenileme in queryset.filter(odeme_durumu='BEKLEMEDE'):
            yenileme.odeme_durumu = 'ODENDI'
            yenileme.save()
        
        self.message_user(
            request,
            f"{queryset.count()} yenileme ödendi olarak işaretlendi.",
            level=messages.SUCCESS
        )
    odeme_onayla.short_description = "Seçili yenilemeleri ödendi yap"
    
    def odeme_iptal(self, request, queryset):
        """Seçili yenilemeleri iptal et"""
        for yenileme in queryset.filter(odeme_durumu='BEKLEMEDE'):
            yenileme.odeme_durumu = 'IPTAL'
            yenileme.save()
        
        self.message_user(
            request,
            f"{queryset.count()} yenileme iptal edildi.",
            level=messages.SUCCESS
        )
    odeme_iptal.short_description = "Seçili yenilemeleri iptal et"
