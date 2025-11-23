# ilan/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import HayvanProfili, HayvanResmi, Ilan, IlanKategori, KrediHareketi, KrediPaketi


class HayvanResmiInline(admin.TabularInline):
    model = HayvanResmi
    extra = 1
    fields = ['resim', 'resim_preview', 'sira']
    readonly_fields = ['resim_preview']
    
    def resim_preview(self, obj):
        """Hayvan resmi önizlemesi"""
        if obj.resim:
            return format_html(
                '<img src="{}" width="80" height="80" style="object-fit: cover; border-radius: 8px; border: 1px solid #dee2e6;" />',
                obj.resim.url
            )
        return format_html(
            '<div style="width: 80px; height: 80px; background: #f8f9fa; border: 1px dashed #dee2e6; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #6c757d; font-size: 10px;">Resim Yok</div>'
        )
    resim_preview.short_description = 'Önizleme'
    resim_preview.admin_order_field = None


@admin.register(HayvanProfili)
class HayvanProfiliAdmin(admin.ModelAdmin):
    list_display = ['hayvan_adi', 'kullanici', 'tur', 'irk', 'yas', 'cinsiyet', 'telefon', 'il', 'ilce', 'aktif', 'profil_fotografi_preview', 'olusturulma_tarihi']
    list_filter = ['tur', 'cinsiyet', 'asi_durumu', 'aktif', 'il', 'olusturulma_tarihi']
    search_fields = ['hayvan_adi', 'kullanici__username', 'kullanici__first_name', 'kullanici__last_name', 'irk__ad', 'il__ad', 'ilce__ad', 'telefon', 'aciklama']
    readonly_fields = ['olusturulma_tarihi', 'profil_fotografi_preview', 'yas']
    inlines = [HayvanResmiInline]
    
    # Performans optimizasyonu için select_related ve prefetch_related kullan
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Tüm foreign key ilişkilerini tek sorguda çek
        qs = qs.select_related('kullanici', 'tur', 'irk', 'il', 'ilce', 'mahalle')
        # Resimleri de tek sorguda çek
        qs = qs.prefetch_related('resimler')
        return qs
    
    class Media:
        js = ('admin/js/veteriner_admin.js',)
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('kullanici', 'hayvan_adi', 'tur', 'irk', 'yas', 'cinsiyet', 'dogum_tarihi')
        }),
        ('Sağlık Bilgileri', {
            'fields': ('asi_durumu', 'ic_parazit', 'dis_parazit')
        }),
        ('Gönderim Bilgileri', {
            'fields': ('sehir_disi_gonderim',)
        }),
        ('Konum', {
            'fields': ('il', 'ilce', 'mahalle', 'mahalle_diger')
        }),
        ('İletişim Bilgileri', {
            'fields': ('telefon',)
        }),
        ('Açıklama ve Medya', {
            'fields': ('aciklama', 'profil_fotografi', 'profil_fotografi_preview')
        }),
        ('Sistem', {
            'fields': ('aktif', 'olusturulma_tarihi', 'evcil_hayvan')
        }),
    )
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        İlçe ve mahalle alanlarını seçilen ile göre filtrele.
        """
        if db_field.name == "ilce":
            il_id = None
            
            # Edit modunda: mevcut nesnenin il'ini kullan
            if request.resolver_match.kwargs.get('object_id'):
                try:
                    obj_id = request.resolver_match.kwargs['object_id']
                    # Tek bir sorgu ile il'i çek (select_related sayesinde cached)
                    obj = self.get_queryset(request).get(pk=obj_id)
                    if obj.il:
                        il_id = obj.il.id
                except (HayvanProfili.DoesNotExist, ValueError, KeyError):
                    pass
            
            # POST data'dan il_id al
            if not il_id and request.method == 'POST':
                il_id = request.POST.get('il')
            
            # İlçeleri filtrele
            if il_id:
                from anahtarlik.dictionaries import Ilce
                kwargs["queryset"] = Ilce.objects.filter(il_id=il_id).order_by('ad')
            else:
                from anahtarlik.dictionaries import Ilce
                kwargs["queryset"] = Ilce.objects.none()
        
        # Mahalle için de benzer işlem
        if db_field.name == "mahalle":
            ilce_id = None
            
            # Edit modunda: mevcut nesnenin ilce'ini kullan
            if request.resolver_match.kwargs.get('object_id'):
                try:
                    obj_id = request.resolver_match.kwargs['object_id']
                    # Tek bir sorgu ile ilce'i çek
                    obj = self.get_queryset(request).get(pk=obj_id)
                    if obj.ilce:
                        ilce_id = obj.ilce.id
                except (HayvanProfili.DoesNotExist, ValueError, KeyError):
                    pass
            
            # POST data'dan ilce_id al
            if not ilce_id and request.method == 'POST':
                ilce_id = request.POST.get('ilce')
            
            # Mahalleleri filtrele
            if ilce_id:
                from anahtarlik.dictionaries import Mahalle
                kwargs["queryset"] = Mahalle.objects.filter(ilce_id=ilce_id).order_by('ad')
            else:
                from anahtarlik.dictionaries import Mahalle
                kwargs["queryset"] = Mahalle.objects.none()
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def profil_fotografi_preview(self, obj):
        """Profil fotoğrafı önizlemesi"""
        if obj.profil_fotografi:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover; border-radius: 50%; border: 2px solid #dee2e6;" />',
                obj.profil_fotografi.url
            )
        return format_html(
            '<div style="width: 100px; height: 100px; background: #f8f9fa; border: 2px dashed #dee2e6; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #6c757d; font-size: 12px;">Resim Yok</div>'
        )
    profil_fotografi_preview.short_description = 'Profil Fotoğrafı'
    profil_fotografi_preview.admin_order_field = None


@admin.register(Ilan)
class IlanAdmin(admin.ModelAdmin):
    list_display = [
        'hayvan_resmi_preview', 'baslik', 'kullanici_bilgisi', 'hayvan_tur_irk', 
        'onay_durumu', 'onemli_durumu', 'aktif', 'goruntulenme_sayisi', 
        'olusturulma_tarihi_kisa', 'hizli_islemler'
    ]
    list_filter = [
        'onaylandi', 'aktif', 'onemli_mi', 'ilan_turu', 
        'hayvan_profili__tur', 'hayvan_profili__il', 'olusturulma_tarihi'
    ]
    search_fields = [
        'baslik', 'aciklama', 'hayvan_profili__hayvan_adi', 
        'hayvan_profili__kullanici__username', 'hayvan_profili__kullanici__email',
        'hayvan_profili__kullanici__first_name', 'hayvan_profili__kullanici__last_name'
    ]
    readonly_fields = [
        'olusturulma_tarihi', 'goruntulenme_sayisi', 'favori_sayisi', 
        'hayvan_resmi_buyuk', 'ilan_detay_bilgileri'
    ]
    actions = ['onayla_ilanlar', 'reddet_ilanlar', 'one_cikart', 'aktif_et', 'pasif_et']
    list_per_page = 25
    date_hierarchy = 'olusturulma_tarihi'
    
    # Onaylanmamış ilanları üstte göster
    ordering = ['onaylandi', '-olusturulma_tarihi']
    
    class Media:
        css = {
            'all': ('admin/css/ilan_admin.css',)
        }
    
    fieldsets = (
        ('📋 İlan Önizleme', {
            'fields': ('hayvan_resmi_buyuk', 'ilan_detay_bilgileri'),
            'classes': ('wide',)
        }),
        ('✏️ İlan Bilgileri', {
            'fields': ('hayvan_profili', 'baslik', 'ilan_turu', 'aciklama', 'fiyat')
        }),
        ('⭐ Özellikler', {
            'fields': ('onemli_mi', 'aktif', 'onaylandi'),
            'description': 'İlanın görünürlük ve onay durumunu ayarlayın'
        }),
        ('📅 Tarihler', {
            'fields': ('olusturulma_tarihi', 'bitis_tarihi')
        }),
        ('📊 İstatistikler', {
            'fields': ('goruntulenme_sayisi', 'favori_sayisi'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'hayvan_profili', 
            'hayvan_profili__kullanici',
            'hayvan_profili__tur',
            'hayvan_profili__irk',
            'hayvan_profili__il'
        )
    
    def hayvan_resmi_preview(self, obj):
        """Küçük resim önizlemesi (liste için)"""
        if obj.hayvan_profili and obj.hayvan_profili.profil_fotografi:
            return format_html(
                '<img src="{}" width="60" height="60" style="object-fit: cover; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />',
                obj.hayvan_profili.profil_fotografi.url
            )
        return format_html(
            '<div style="width: 60px; height: 60px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px; display: flex; align-items: center; justify-content: center;"><i class="fas fa-paw" style="color: white; font-size: 24px;"></i></div>'
        )
    hayvan_resmi_preview.short_description = '🖼️'
    
    def hayvan_resmi_buyuk(self, obj):
        """Büyük resim önizlemesi (detay için)"""
        if obj.hayvan_profili and obj.hayvan_profili.profil_fotografi:
            return format_html(
                '''
                <div style="text-align: center; margin: 20px 0;">
                    <img src="{}" style="max-width: 100%; max-height: 400px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" />
                </div>
                ''',
                obj.hayvan_profili.profil_fotografi.url
            )
        return format_html('<p style="text-align: center; color: #999;">Resim yok</p>')
    hayvan_resmi_buyuk.short_description = 'Hayvan Resmi'
    
    def kullanici_bilgisi(self, obj):
        """Kullanıcı bilgilerini göster"""
        user = obj.hayvan_profili.kullanici
        username = user.username
        full_name = f"{user.first_name} {user.last_name}".strip()
        
        # Kullanıcı tipini belirle
        user_type = "👤 Kullanıcı"
        if hasattr(user, 'sahip'):
            user_type = "🏠 Sahip"
        elif hasattr(user, 'veteriner_profili'):
            user_type = "⚕️ Veteriner"
        elif hasattr(user, 'petshop'):
            user_type = "🏪 Pet Shop"
        
        return format_html(
            '''
            <div style="min-width: 150px;">
                <div style="font-weight: bold; color: #2c3e50;">{}</div>
                <div style="font-size: 11px; color: #7f8c8d;">{}</div>
                <div style="font-size: 10px; color: #95a5a6; margin-top: 2px;">{}</div>
            </div>
            ''',
            username,
            full_name if full_name else user.email,
            user_type
        )
    kullanici_bilgisi.short_description = '👤 Kullanıcı'
    
    def hayvan_tur_irk(self, obj):
        """Hayvan tür ve ırk bilgisi"""
        return format_html(
            '''
            <div style="min-width: 100px;">
                <div style="font-weight: bold; color: #3498db;">{}</div>
                <div style="font-size: 11px; color: #7f8c8d;">{}</div>
                <div style="font-size: 10px; color: #95a5a6; margin-top: 2px;">📍 {}</div>
            </div>
            ''',
            obj.hayvan_profili.tur.ad,
            obj.hayvan_profili.irk.ad,
            obj.hayvan_profili.il.ad
        )
    hayvan_tur_irk.short_description = '🐾 Hayvan'
    
    def onay_durumu(self, obj):
        """Renkli onay durumu gösterimi"""
        if obj.onaylandi:
            return format_html(
                '<span style="display: inline-block; padding: 6px 12px; background: #2ecc71; color: white; border-radius: 20px; font-size: 11px; font-weight: bold; box-shadow: 0 2px 4px rgba(46, 204, 113, 0.3);">✓ Onaylandı</span>'
            )
        else:
            return format_html(
                '<span style="display: inline-block; padding: 6px 12px; background: #f39c12; color: white; border-radius: 20px; font-size: 11px; font-weight: bold; box-shadow: 0 2px 4px rgba(243, 156, 18, 0.3); animation: pulse 2s infinite;">⏳ Bekliyor</span>'
            )
    onay_durumu.short_description = '✓ Onay'
    onay_durumu.admin_order_field = 'onaylandi'
    
    def onemli_durumu(self, obj):
        """Öne çıkan durumu"""
        if obj.onemli_mi:
            return format_html(
                '<span style="display: inline-block; padding: 6px 12px; background: #e74c3c; color: white; border-radius: 20px; font-size: 11px; font-weight: bold;">⭐ Öne Çıkan</span>'
            )
        return format_html(
            '<span style="display: inline-block; padding: 6px 12px; background: #ecf0f1; color: #95a5a6; border-radius: 20px; font-size: 11px;">—</span>'
        )
    onemli_durumu.short_description = '⭐'
    onemli_durumu.admin_order_field = 'onemli_mi'
    
    def olusturulma_tarihi_kisa(self, obj):
        """Kısa tarih formatı"""
        from django.utils import timezone as tz
        now = tz.now()
        diff = now - obj.olusturulma_tarihi
        
        if diff.days == 0:
            hours = diff.seconds // 3600
            if hours == 0:
                minutes = diff.seconds // 60
                return format_html(
                    '<span style="color: #e74c3c; font-weight: bold;">{} dk önce</span>',
                    minutes
                )
            return format_html(
                '<span style="color: #e67e22; font-weight: bold;">{} saat önce</span>',
                hours
            )
        elif diff.days == 1:
            return format_html('<span style="color: #f39c12;">Dün</span>')
        elif diff.days < 7:
            return format_html('<span style="color: #3498db;">{} gün önce</span>', diff.days)
        else:
            return obj.olusturulma_tarihi.strftime('%d.%m.%Y')
    olusturulma_tarihi_kisa.short_description = '📅 Tarih'
    olusturulma_tarihi_kisa.admin_order_field = 'olusturulma_tarihi'
    
    def hizli_islemler(self, obj):
        """Hızlı işlem butonları"""
        buttons = []
        
        if not obj.onaylandi:
            buttons.append(
                f'<a href="/admin/ilan/ilan/{obj.id}/change/" '
                f'onclick="document.getElementById(\'id_onaylandi\').checked=true; '
                f'document.querySelector(\'input[name=_save]\').click(); return false;" '
                f'style="display: inline-block; padding: 4px 8px; background: #2ecc71; color: white; '
                f'text-decoration: none; border-radius: 4px; font-size: 11px; margin-right: 4px;">✓ Onayla</a>'
            )
        
        buttons.append(
            f'<a href="/ilanlar/{obj.id}/" target="_blank" '
            f'style="display: inline-block; padding: 4px 8px; background: #3498db; color: white; '
            f'text-decoration: none; border-radius: 4px; font-size: 11px;">👁️ Görüntüle</a>'
        )
        
        return format_html(''.join(buttons))
    hizli_islemler.short_description = '⚡ İşlemler'
    
    def ilan_detay_bilgileri(self, obj):
        """İlan detay bilgileri"""
        return format_html(
            '''
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 10px 0;">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                    <div>
                        <strong style="color: #7f8c8d;">Hayvan Adı:</strong><br/>
                        <span style="font-size: 16px; color: #2c3e50;">{}</span>
                    </div>
                    <div>
                        <strong style="color: #7f8c8d;">Kullanıcı:</strong><br/>
                        <span style="font-size: 16px; color: #2c3e50;">{}</span>
                    </div>
                    <div>
                        <strong style="color: #7f8c8d;">Tür / Irk:</strong><br/>
                        <span style="font-size: 16px; color: #2c3e50;">{} / {}</span>
                    </div>
                    <div>
                        <strong style="color: #7f8c8d;">Konum:</strong><br/>
                        <span style="font-size: 16px; color: #2c3e50;">{} / {}</span>
                    </div>
                    <div>
                        <strong style="color: #7f8c8d;">Görüntülenme:</strong><br/>
                        <span style="font-size: 18px; color: #3498db; font-weight: bold;">{}</span>
                    </div>
                    <div>
                        <strong style="color: #7f8c8d;">Oluşturulma:</strong><br/>
                        <span style="font-size: 14px; color: #2c3e50;">{}</span>
                    </div>
                </div>
                <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #dee2e6;">
                    <strong style="color: #7f8c8d;">Açıklama:</strong><br/>
                    <p style="margin-top: 8px; color: #2c3e50; line-height: 1.6;">{}</p>
                </div>
            </div>
            ''',
            obj.hayvan_profili.hayvan_adi,
            obj.hayvan_profili.kullanici.username,
            obj.hayvan_profili.tur.ad,
            obj.hayvan_profili.irk.ad,
            obj.hayvan_profili.il.ad,
            obj.hayvan_profili.ilce.ad,
            obj.goruntulenme_sayisi,
            obj.olusturulma_tarihi.strftime('%d.%m.%Y %H:%M'),
            obj.aciklama or 'Açıklama yok'
        )
    ilan_detay_bilgileri.short_description = 'Detaylar'
    
    def onayla_ilanlar(self, request, queryset):
        """Seçili ilanları onayla ve kullanıcılara bildirim gönder"""
        from anahtarlik.models import Bildirim
        from django.conf import settings
        from django.core.mail import send_mail
        
        updated_count = 0
        
        for ilan in queryset:
            # İlanı onayla ve aktif et
            ilan.onaylandi = True
            ilan.aktif = True
            ilan.save()
            updated_count += 1
            
            # Kullanıcıya bildirim gönder
            try:
                kullanici = ilan.hayvan_profili.kullanici
                
                # E-posta gönder
                try:
                    subject = f"✅ İlanınız Onaylandı - {ilan.baslik}"
                    message = f"""Merhaba {kullanici.first_name or kullanici.username}, 

İlanınız başarıyla onaylandı ve yayına alındı!

📋 İlan Detayları:
- Hayvan: {ilan.hayvan_profili.hayvan_adi}
- Tür: {ilan.hayvan_profili.tur.ad}
- Başlık: {ilan.baslik}
- İlan Türü: {ilan.get_ilan_turu_display()}

İlanınız artık sitede görünür durumda. Sahiplendirme sürecinde başarılar dileriz!

Sevgiler,
PetSafe Hub Ekibi"""
                    recipient_list = [kullanici.email]
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, fail_silently=True)
                except Exception as e:
                    print(f"E-posta gönderme hatası: {e}")
                
                # Sahip kullanıcısı için bildirim oluştur
                if hasattr(kullanici, 'sahip'):
                    try:
                        bildirim_url = f"/ilanlar/ilan/{ilan.id}/"
                        Bildirim.objects.create(
                            sahip=kullanici.sahip,
                            baslik=f"✅ İlanınız Onaylandı",
                            mesaj=f"{ilan.baslik} başlıklı ilanınız onaylandı ve yayına alındı!",
                            tur='GENEL',
                            oncelik='NORMAL',
                            url=bildirim_url,
                            okundu=False
                        )
                    except Exception as e:
                        print(f"Bildirim oluşturma hatası: {e}")
                
            except Exception as e:
                print(f"Bildirim hatası: {e}")
        
        self.message_user(request, f'✅ {updated_count} ilan onaylandı ve aktif edildi.', 'success')
    onayla_ilanlar.short_description = "✅ Seçili ilanları onayla"
    
    def reddet_ilanlar(self, request, queryset):
        """Seçili ilanları reddet ve kullanıcılara bildirim gönder"""
        from anahtarlik.models import Bildirim
        from django.conf import settings
        from django.core.mail import send_mail
        
        updated_count = 0
        
        for ilan in queryset:
            # İlanı reddet ve pasif et
            ilan.onaylandi = False
            ilan.aktif = False
            ilan.save()
            updated_count += 1
            
            # Kullanıcıya bildirim gönder
            try:
                kullanici = ilan.hayvan_profili.kullanici
                
                # E-posta gönder
                try:
                    subject = f"❌ İlanınız Reddedildi - {ilan.baslik}"
                    message = f"""Merhaba {kullanici.first_name or kullanici.username},

Maalesef ilanınız yayın kurallarına uymadığı için reddedilmiştir.

📋 İlan Detayları:
- Hayvan: {ilan.hayvan_profili.hayvan_adi}
- Tür: {ilan.hayvan_profili.tur.ad}
- Başlık: {ilan.baslik}
- İlan Türü: {ilan.get_ilan_turu_display()}

İlanınızı düzenleyip tekrar gönderebilirsiniz. Sorularınız için destek ekibimizle iletişime geçebilirsiniz.

Sevgiler,
PetSafe Hub Ekibi"""
                    recipient_list = [kullanici.email]
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, fail_silently=True)
                except Exception as e:
                    print(f"E-posta gönderme hatası: {e}")
                
                # Sahip kullanıcısı için bildirim oluştur
                if hasattr(kullanici, 'sahip'):
                    try:
                        bildirim_url = f"/ilanlar/"
                        Bildirim.objects.create(
                            sahip=kullanici.sahip,
                            baslik=f"❌ İlanınız Reddedildi",
                            mesaj=f"{ilan.baslik} başlıklı ilanınız reddedildi. Lütfen ilanınızı düzenleyip tekrar gönderin.",
                            tur='GENEL',
                            oncelik='NORMAL',
                            url=bildirim_url,
                            okundu=False
                        )
                    except Exception as e:
                        print(f"Bildirim oluşturma hatası: {e}")
                
            except Exception as e:
                print(f"Bildirim hatası: {e}")
        
        self.message_user(request, f'❌ {updated_count} ilan reddedildi ve pasif edildi.', 'warning')
    reddet_ilanlar.short_description = "❌ Seçili ilanları reddet"
    
    def one_cikart(self, request, queryset):
        """Seçili ilanları öne çıkar"""
        updated = queryset.update(onemli_mi=True)
        self.message_user(request, f'⭐ {updated} ilan öne çıkarıldı.', 'success')
    one_cikart.short_description = "⭐ Öne çıkar"
    
    def aktif_et(self, request, queryset):
        """Seçili ilanları aktif et"""
        updated = queryset.update(aktif=True)
        self.message_user(request, f'✓ {updated} ilan aktif edildi.', 'success')
    aktif_et.short_description = "✓ Aktif et"
    
    def pasif_et(self, request, queryset):
        """Seçili ilanları pasif et"""
        updated = queryset.update(aktif=False)
        self.message_user(request, f'○ {updated} ilan pasif edildi.', 'warning')
    pasif_et.short_description = "○ Pasif et"


@admin.register(IlanKategori)
class IlanKategoriAdmin(admin.ModelAdmin):
    list_display = ['ad', 'slug', 'aktif']
    list_filter = ['aktif']
    search_fields = ['ad', 'aciklama']
    prepopulated_fields = {'slug': ('ad',)}


@admin.register(KrediHareketi)
class KrediHareketiAdmin(admin.ModelAdmin):
    list_display = ['kullanici', 'hareket_turu', 'miktar', 'aciklama', 'tarih']
    list_filter = ['hareket_turu', 'tarih']
    search_fields = ['kullanici__username', 'aciklama']
    readonly_fields = ['tarih']
    ordering = ['-tarih']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('kullanici')


@admin.register(KrediPaketi)
class KrediPaketiAdmin(admin.ModelAdmin):
    list_display = ['ad', 'kredi_adet', 'fiyat_display', 'birim_fiyat_display', 'aktif', 'one_cikan', 'etiket', 'sira']
    list_filter = ['aktif', 'one_cikan']
    search_fields = ['ad', 'aciklama']
    list_editable = ['aktif', 'sira']
    ordering = ['sira', 'fiyat']
    
    fieldsets = (
        ('Paket Bilgileri', {
            'fields': ('ad', 'aciklama', 'kredi_adet', 'fiyat')
        }),
        ('Görünüm Ayarları', {
            'fields': ('aktif', 'sira', 'one_cikan', 'etiket')
        }),
        ('Tarihler', {
            'fields': ('olusturma_tarihi', 'guncelleme_tarihi'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['olusturma_tarihi', 'guncelleme_tarihi']
    
    def fiyat_display(self, obj):
        return f"₺{obj.fiyat}"
    fiyat_display.short_description = "Fiyat"
    fiyat_display.admin_order_field = "fiyat"
    
    def birim_fiyat_display(self, obj):
        return f"₺{obj.birim_fiyat():.4f}"
    birim_fiyat_display.short_description = "Kredi Başına"


# Admin panelinde özel ayarlar için
class IlanAyarlariAdmin(admin.ModelAdmin):
    """İlan sistemi ayarları için özel admin"""
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request):
        return False
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'İlan Sistemi Ayarları'
        extra_context['subtitle'] = 'Kredi miktarları ve ilan süreleri'
        return super().changelist_view(request, extra_context)


# Admin panelinde görüntüleme için özel sayfa
# admin.site.register_view('ilan-ayarlari/', IlanAyarlariAdmin, name='ilan_ayarlari')