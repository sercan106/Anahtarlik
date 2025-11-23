# veteriner/admin.py

from django.contrib import admin, messages
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django import forms
import secrets
import string
from .models import (
    Veteriner,
    SiparisIstemi,
    VeterinerYuzde,
    OD_ALIN,
    OD_IADE,
    OD_MUAF,
)

# =========================
# VETERİNER ADMIN
# =========================

class VeterinerAdminForm(forms.ModelForm):
    kullanici_adi = forms.CharField(max_length=150, required=False, label="Kullanıcı Adı")
    sifre = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Boş bırakırsanız otomatik güçlü şifre oluşturulur'}),
        required=False,
        label="Şifre",
        help_text="⚡ Boş bırakırsanız otomatik 16 karakterlik güçlü şifre oluşturulur. Manuel şifre girmek isterseniz güçlü şifre kullanın (en az 8 karakter, büyük/küçük harf, rakam, özel karakter)."
    )
    sifre_tekrar = forms.CharField(widget=forms.PasswordInput(), required=False, label="Şifre Tekrar")
    
    class Meta:
        model = Veteriner
        fields = '__all__'
    
    def clean_sifre(self):
        """Şifre gücü kontrolü"""
        sifre = self.cleaned_data.get('sifre')
        if sifre:
            try:
                # Django'nun password validators'ını kullan
                validate_password(sifre)
            except DjangoValidationError as e:
                raise forms.ValidationError(
                    f"Şifre güvenlik gereksinimlerini karşılamıyor: {', '.join(e.messages)}"
                )
        return sifre
    
    def clean(self):
        from anahtarlik.models import Sahip
        from petshop.models import PetShop
        from accaunt.models import MisafirProfil
        
        cleaned_data = super().clean()
        kullanici_adi = cleaned_data.get('kullanici_adi')
        sifre = cleaned_data.get('sifre')
        sifre_tekrar = cleaned_data.get('sifre_tekrar')
        email = cleaned_data.get('email')
        telefon = cleaned_data.get('telefon')
        
        # Şifre boşsa save_model'de otomatik oluşturulacak, burada sadece validasyon yap
        
        if sifre and sifre != sifre_tekrar:
            raise forms.ValidationError("Şifreler eşleşmiyor.")
        
        if kullanici_adi and User.objects.filter(username=kullanici_adi).exists():
            existing_user = User.objects.get(username=kullanici_adi)
            # Admin kullanıcısına profil oluşturmayı engelle
            if existing_user.is_superuser:
                raise forms.ValidationError(
                    "Admin kullanıcısına veteriner profili oluşturulamaz! "
                    "Admin kullanıcıları sistem yöneticisidir, veteriner olamaz."
                )
            # Mevcut kullanıcının başka profili var mı kontrol et
            if hasattr(existing_user, 'veteriner_profili'):
                raise forms.ValidationError(
                    f"Bu kullanıcının ({kullanici_adi}) zaten veteriner profili var."
                )
            if hasattr(existing_user, 'petshop_profili'):
                raise forms.ValidationError(
                    f"Bu kullanıcının ({kullanici_adi}) zaten petshop profili var. "
                    "Bir kullanıcı sadece bir tür profil olabilir."
                )
        
        # E-posta benzersizlik kontrolü (yeni kullanıcı oluşturuluyorsa)
        if kullanici_adi and email:
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError(
                    f"Bu e-posta adresi ({email}) zaten kayıtlı. "
                    "Aynı e-posta ile birden fazla hesap oluşturulamaz."
                )
        
        # Telefon benzersizlik kontrolü
        if telefon:
            telefon_clean = ''.join(filter(str.isdigit, telefon))
            if telefon_clean.startswith('0'):
                telefon_clean = telefon_clean[1:]
            
            # Tüm profil tiplerinde kontrol et
            if Sahip.objects.filter(telefon=telefon_clean).exists():
                raise forms.ValidationError(f"Bu telefon numarası ({telefon}) zaten kayıtlı (Sahip).")
            if self.instance.pk:
                # Edit modunda kendi kaydını hariç tut
                if self.Meta.model.objects.filter(telefon=telefon_clean).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError(f"Bu telefon numarası ({telefon}) zaten kayıtlı (Veteriner).")
            else:
                if self.Meta.model.objects.filter(telefon=telefon_clean).exists():
                    raise forms.ValidationError(f"Bu telefon numarası ({telefon}) zaten kayıtlı (Veteriner).")
            if PetShop.objects.filter(telefon=telefon_clean).exists():
                raise forms.ValidationError(f"Bu telefon numarası ({telefon}) zaten kayıtlı (PetShop).")
            if MisafirProfil.objects.filter(telefon=telefon_clean).exists():
                raise forms.ValidationError(f"Bu telefon numarası ({telefon}) zaten kayıtlı (Misafir).")
        
        return cleaned_data

@admin.register(Veteriner)
class VeterinerAdmin(admin.ModelAdmin):
    form = VeterinerAdminForm
    list_display = (
        "ad", "il_display", "ilce_display", "telefon",
        "odeme_modeli", "tahsis_sayisi", "satis_sayisi",
        "kalan_envanter_goster", "danisman_sahip_sayisi_goster", 
        "dinamik_kapasite_goster", "kapasite_durumu_goster", "aktif",
    )
    list_filter = ("aktif", "odeme_modeli", "il", "ilce")
    search_fields = ("ad", "telefon", "email", "il__ad", "ilce__ad")
    ordering = ("-olusturulma",)
    
    class Media:
        js = ('admin/js/veteriner_admin.js',)
    
    def generate_strong_password(self):
        """Güçlü şifre oluştur"""
        # En az 12 karakter, büyük/küçük harf, rakam ve özel karakter
        alphabet = string.ascii_letters + string.digits + "!@#$%&*"
        password = ''.join(secrets.choice(alphabet) for i in range(16))
        return password
    
    fieldsets = (
        ("Genel Bilgiler", {
            "fields": ("ad", "telefon", "email", "il", "ilce", "adres_detay", "konum_koordinat")
        }),
        ("Veteriner Bilgileri", {
            "fields": ("uzmanlik_alanlari", "calisma_saatleri", "acil_hizmet", "evde_hizmet")
        }),
        ("Sistem Bilgileri", {
            "fields": ("kullanici", "odeme_modeli", "aktif")
        }),
        ("Kullanıcı Hesabı", {
            "fields": ("kullanici_adi", "sifre", "sifre_tekrar"),
            "description": "Yeni kullanıcı hesabı oluşturmak için doldurun. Güçlü şifre kullanın (en az 8 karakter, büyük/küçük harf, rakam ve özel karakter içermeli)."
        }),
    )
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        İlçe alanını seçilen ile göre filtrele.
        Form ilk yüklendiğinde veya JavaScript çalışmazsa kullanılır.
        """
        if db_field.name == "ilce":
            # URL'den veya POST'tan il_id'yi almaya çalış
            il_id = None
            
            # Edit modunda: mevcut nesnenin il'ini kullan
            if request.resolver_match.kwargs.get('object_id'):
                try:
                    obj_id = request.resolver_match.kwargs['object_id']
                    obj = Veteriner.objects.get(pk=obj_id)
                    if obj.il:
                        il_id = obj.il.id
                except (Veteriner.DoesNotExist, ValueError, KeyError):
                    pass
            
            # POST data'dan il_id al (form submit edildiğinde)
            if not il_id and request.method == 'POST':
                il_id = request.POST.get('il')
            
            # İlçeleri filtrele
            if il_id:
                from anahtarlik.dictionaries import Ilce
                kwargs["queryset"] = Ilce.objects.filter(il_id=il_id).order_by('ad')
            else:
                # İl seçilmemişse boş queryset
                from anahtarlik.dictionaries import Ilce
                kwargs["queryset"] = Ilce.objects.none()
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def kalan_envanter_goster(self, obj):
        return obj.kalan_envanter
    kalan_envanter_goster.short_description = "Kalan Envanter"
    
    def il_display(self, obj):
        return obj.il.ad if obj.il else "-"
    il_display.short_description = "İl"
    il_display.admin_order_field = "il__ad"
    
    def ilce_display(self, obj):
        return obj.ilce.ad if obj.ilce else "-"
    ilce_display.short_description = "İlçe"
    ilce_display.admin_order_field = "ilce__ad"
    
    def danisman_sahip_sayisi_goster(self, obj):
        return obj.danisman_sahip_sayisi
    danisman_sahip_sayisi_goster.short_description = "Danışman Sahip Sayısı"
    danisman_sahip_sayisi_goster.admin_order_field = None
    
    def dinamik_kapasite_goster(self, obj):
        kapasite = obj.dinamik_kapasite
        current = obj.danisman_sahip_sayisi
        yuzde = obj.kapasite_yuzdesi
        
        if yuzde >= 100:
            color = "🔴"
        elif yuzde >= 80:
            color = "🟡"
        elif yuzde >= 50:
            color = "🟢"
        else:
            color = "⚪"
            
        return f"{color} {current}/{kapasite} (%{yuzde:.1f})"
    dinamik_kapasite_goster.short_description = "Dinamik Kapasite"
    dinamik_kapasite_goster.admin_order_field = None
    
    def kapasite_durumu_goster(self, obj):
        durum = obj.kapasite_durumu
        if durum == "Dolu":
            return "🔴 Dolu"
        elif durum == "Doluya Yakın":
            return "🟡 Doluya Yakın"
        elif durum == "Orta":
            return "🟢 Orta"
        else:
            return "⚪ Boş"
    kapasite_durumu_goster.short_description = "Kapasite Durumu"
    kapasite_durumu_goster.admin_order_field = None
    
    def save_model(self, request, obj, form, change):
        # Yeni kullanıcı hesabı oluşturma
        kullanici_adi = form.cleaned_data.get('kullanici_adi')
        sifre = form.cleaned_data.get('sifre')
        
        # Eğer şifre yoksa otomatik oluştur
        auto_generated = False
        if kullanici_adi and not sifre:
            sifre = self.generate_strong_password()
            auto_generated = True
        
        if kullanici_adi and sifre and not obj.kullanici:
            # Yeni kullanıcı oluştur
            user = User.objects.create_user(
                username=kullanici_adi,
                password=sifre,
                email=obj.email or '',
                first_name=obj.ad.split()[0] if obj.ad else '',
                last_name=' '.join(obj.ad.split()[1:]) if len(obj.ad.split()) > 1 else ''
            )
            obj.kullanici = user
            
            # Bayiye vermek için kullanıcı bilgilerini mesaj olarak göster
            from django.utils.html import format_html
            # Otomatik oluşturulmuş şifre uyarısı
            auto_note = ''
            if auto_generated:
                auto_note = format_html(
                    '<p style="background: #fff3cd; padding: 8px; border-radius: 3px; margin-bottom: 10px; color: #856404;">'
                    '🔐 <strong>Otomatik Güçlü Şifre Oluşturuldu:</strong> Şifre alanı boş bırakıldığı için sistem tarafından güvenli bir şifre oluşturuldu.'
                    '</p>'
                )
            
            success_msg = format_html(
                '<div style="background: #d4edda; padding: 15px; border-radius: 5px; margin: 10px 0;">'
                '<h4 style="margin-top: 0;">✅ Veteriner Kullanıcı Hesabı Oluşturuldu</h4>'
                '{}'
                '<p><strong>Bayiye vereceğiniz bilgiler:</strong></p>'
                '<table style="border-collapse: collapse; width: 100%;">'
                '<tr><td style="padding: 5px; border: 1px solid #ddd; background: #f8f9fa;"><strong>Veteriner Adı:</strong></td>'
                '<td style="padding: 5px; border: 1px solid #ddd;">{}</td></tr>'
                '<tr><td style="padding: 5px; border: 1px solid #ddd; background: #f8f9fa;"><strong>Kullanıcı Adı:</strong></td>'
                '<td style="padding: 5px; border: 1px solid #ddd;">{}</td></tr>'
                '<tr><td style="padding: 5px; border: 1px solid #ddd; background: #f8f9fa;"><strong>Şifre:</strong></td>'
                '<td style="padding: 5px; border: 1px solid #ddd;"><code style="background: #fff3cd; padding: 3px 8px; border-radius: 3px; font-size: 14px;">{}</code></td></tr>'
                '</table>'
                '<p style="color: #856404; margin-top: 10px; font-size: 12px;">'
                '⚠️ Bu bilgileri güvenli bir şekilde bayinize iletin. Şifre bir daha gösterilmeyecektir.</p>'
                '<p style="background: #d1ecf1; padding: 10px; border-radius: 3px; margin-top: 10px; color: #0c5460; font-size: 13px;">'
                '🔒 <strong>İlk Giriş Şifre Değiştirme:</strong> Veteriner ilk giriş yaptığında şifresini değiştirmesi ZORUNLUDUR. '
                'Giriş yaptıktan sonra otomatik olarak hesap ayarları sayfasına yönlendirilecektir.</p>'
                '</div>',
                auto_note,
                obj.ad,
                kullanici_adi,
                sifre
            )
            messages.success(request, success_msg)
            
            # E-posta gönderimi (eğer e-posta adresi varsa)
            if obj.email:
                try:
                    from django.core.mail import send_mail
                    from django.conf import settings
                    
                    subject = f"PetSafe Hub - Veteriner Hesabınız Oluşturuldu"
                    message = f"""Merhaba {obj.ad},

Veteriner hesabınız başarıyla oluşturulmuştur.

Giriş Bilgileriniz:
- Kullanıcı Adı: {kullanici_adi}
- Şifre: {sifre}

Bu bilgilerle https://{request.get_host()}/accaunt/login/ adresinden giriş yapabilirsiniz.

⚠️ ÖNEMLİ GÜVENLİK UYARISI:
Güvenliğiniz için İLK GİRİŞİNİZDE şifrenizi değiştirmeniz ZORUNLUDUR.
Giriş yaptıktan sonra otomatik olarak hesap ayarları sayfasına yönlendirileceksiniz.
Şifrenizi değiştirmeden panel'e erişemezsiniz.

İyi çalışmalar,
PetSafe Hub Ekibi"""
                    
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [obj.email],
                        fail_silently=True
                    )
                    messages.info(request, f"Giriş bilgileri {obj.email} adresine e-posta ile gönderildi.")
                except Exception as e:
                    messages.warning(request, f"E-posta gönderilemedi: {str(e)}")
        
        super().save_model(request, obj, form, change)


# =========================
# VETERİNER YÜZDE ADMIN
# =========================

@admin.register(VeterinerYuzde)
class VeterinerYuzdeAdmin(admin.ModelAdmin):
    list_display = (
        "veteriner", "ilce", "yuzde", "son_guncelleme"
    )
    list_filter = ("ilce", "son_guncelleme")
    search_fields = ("veteriner__ad", "ilce__ad")
    ordering = ("-yuzde", "veteriner__ad")
    readonly_fields = ("son_guncelleme",)
    
    fieldsets = (
        ("Veteriner Bilgileri", {
            "fields": ("veteriner", "ilce")
        }),
        ("Yüzde Dağılımı", {
            "fields": ("yuzde", "son_guncelleme")
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('veteriner', 'ilce')


# =========================
# SİPARİŞ İSTEMİ ADMIN
# =========================

@admin.register(SiparisIstemi)
class SiparisIstemiAdmin(admin.ModelAdmin):
    # Liste görünümü
    list_display = (
        "veteriner", "talep_edilen_adet", "talep_tarihi",
        "numune_mi", "odeme_durumu", "odeme_alindi_mi_goster",
        "olusturulan_etiket_sayisi", "kargolandimi", "kargo_sirketi", "kargo_takip_no",
    )
    list_filter = (
        "onaylandi", "numune_mi", "odeme_durumu",
        "kargolandimi", "kargo_sirketi", "talep_tarihi",
    )
    search_fields = (
        "veteriner__ad", "veteriner__il__ad", "veteriner__ilce__ad",
        "kargo_takip_no", "il__ad", "ilce__ad", "adres_detay",
    )
    date_hierarchy = "talep_tarihi"
    ordering = ("-talep_tarihi",)
    
    class Media:
        js = ('admin/js/veteriner_admin.js',)

    # Form düzeni
    fieldsets = (
        ("Sipariş", {
            "fields": ("veteriner", "talep_edilen_adet", "talep_tarihi", "onaylandi", "onay_tarihi")
        }),
        ("Gönderim Adresi", {
            "fields": ("farkli_adres_kullan", "il", "ilce", "adres_detay")
        }),
        ("Numune / Ödeme", {
            "fields": ("numune_mi", "odeme_durumu", "odeme_tutari", "odeme_para_birimi", "odeme_yontemi", "odeme_alinma_tarihi")
        }),
        ("Kargo", {
            "fields": ("kargolandimi", "kargo_tarihi", "kargo_sirketi", "kargo_takip_no")
        }),
    )
    readonly_fields = ("talep_tarihi", "onay_tarihi", "kargo_tarihi", "odeme_alinma_tarihi")
    
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
                    obj = SiparisIstemi.objects.get(pk=obj_id)
                    if obj.il:
                        il_id = obj.il.id
                except (SiparisIstemi.DoesNotExist, ValueError, KeyError):
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
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # Aksiyonlar
    actions = [
        "isaretle_onayla",
        "isaretle_odeme_alindi",
        "isaretle_odeme_iade",
        "isaretle_odeme_muaf",
        "isaretle_kargolandi",
    ]

    # ---- Yardımcı sütunlar ----
    def odeme_alindi_mi_goster(self, obj):
        return obj.odeme_alindi_mi
    odeme_alindi_mi_goster.boolean = True
    odeme_alindi_mi_goster.short_description = "Ödeme Alındı mı?"
    
    def olusturulan_etiket_sayisi(self, obj):
        """Oluşturulan etiket sayısını göster"""
        if not obj.onaylandi:
            return "❌ Onaylanmamış"
        
        etiket_sayisi = len(obj.olusturulan_etiketler)
        return f"✅ {etiket_sayisi}/{obj.talep_edilen_adet} etiket"
    olusturulan_etiket_sayisi.short_description = "Etiket Durumu"

    # ---- Kayıt kuralları (manuel kayıt/editleme) ----
    def save_model(self, request, obj, form, change):
        """
        Admin formundan kayıt/editleme yapılırken de iş kuralları uygulansın:
        - Ödeme alınmadan (ve numune değilken) kargo işaretlenemesin.
        - Ödeme ALINDI ise odeme_alinma_tarihi otomatik dolsun.
        """
        # Ödeme alındı ise tarih set et
        if obj.odeme_durumu == OD_ALIN and not obj.odeme_alinma_tarihi:
            obj.odeme_alinma_tarihi = timezone.now()

        # Numune değil ve ödeme ALINMADI ise kargo işaretlenemez
        if obj.kargolandimi and not obj.numune_mi and obj.odeme_durumu != OD_ALIN:
            self.message_user(
                request,
                "Ödeme alınmadan (ve numune değilken) kargo işaretlenemez.",
                level=messages.ERROR,
            )
            # Kargo alanlarını geri al
            obj.kargolandimi = False
            obj.kargo_tarihi = None

        super().save_model(request, obj, form, change)

    # ---- Aksiyonlar ----

    @admin.action(description="SİPARİŞ: Onayla")
    def isaretle_onayla(self, request, queryset):
        toplam_etiket = 0
        updated = 0
        
        for siparis in queryset:
            if not siparis.onaylandi:  # Sadece onaylanmamış siparişleri işle
                siparis.onaylandi = True
                siparis.save()  # Bu otomatik etiket oluşturacak
                toplam_etiket += siparis.talep_edilen_adet
                updated += 1
        
        if updated > 0:
            self.message_user(
                request, 
                f"{updated} sipariş ONAYLANDI ve {toplam_etiket} etiket otomatik oluşturuldu.", 
                level=messages.SUCCESS
            )
        else:
            self.message_user(request, "Onaylanacak yeni sipariş bulunamadı.", level=messages.WARNING)

    @admin.action(description="ÖDEME: Alındı (tarih otomatik)")
    def isaretle_odeme_alindi(self, request, queryset):
        updated = 0
        for s in queryset:
            s.odeme_durumu = OD_ALIN
            if not s.odeme_alinma_tarihi:
                s.odeme_alinma_tarihi = timezone.now()
            s.save()
            updated += 1
        self.message_user(request, f"{updated} siparişte ÖDEME ALINDI.", level=messages.SUCCESS)

    @admin.action(description="ÖDEME: İade edildi")
    def isaretle_odeme_iade(self, request, queryset):
        updated = queryset.update(odeme_durumu=OD_IADE)
        self.message_user(request, f"{updated} siparişte ÖDEME İADE edildi.", level=messages.SUCCESS)

    @admin.action(description="ÖDEME: Muaf (Numune)")
    def isaretle_odeme_muaf(self, request, queryset):
        updated = 0
        for s in queryset:
            s.numune_mi = True
            s.odeme_durumu = OD_MUAF
            s.odeme_tutari = None
            s.odeme_yontemi = ""
            s.odeme_alinma_tarihi = None
            s.save()
            updated += 1
        self.message_user(request, f"{updated} sipariş ÖDEME MUAF (Numune) oldu.", level=messages.SUCCESS)

    @admin.action(description="KARGO: Kargolandı olarak işaretle (ödeme şart)")
    def isaretle_kargolandi(self, request, queryset):
        """
        Kargolama şu şartlarla izinli:
          - sipariş numune ise (odeme_durumu=MUAF) → OK
          - ya da ödeme ALINDI ise → OK
        Aksi halde atlanır ve uyarı verilir.
        """
        ok = 0
        skipped = 0
        for s in queryset:
            if s.numune_mi or s.odeme_durumu == OD_ALIN:
                s.kargolandimi = True
                if not s.kargo_tarihi:
                    s.kargo_tarihi = timezone.now()
                s.save()
                ok += 1
            else:
                skipped += 1

        if ok:
            self.message_user(
                request,
                f"{ok} sipariş KARGOLANDI olarak işaretlendi.",
                level=messages.SUCCESS
            )
        if skipped:
            self.message_user(
                request,
                f"{skipped} sipariş atlandı: ödeme alınmadı (ve numune değil).",
                level=messages.WARNING
            )
