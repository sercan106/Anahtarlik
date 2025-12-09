# veteriner/admin.py
from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.html import format_html
from django import forms
import secrets
import string

# İl/İlçe dictionary modellerini en baştan import et (hata buradan kalkacak)
from anahtarlik.dictionaries import Ilce

from .models import Veteriner, SiparisIstemi, VeterinerYuzde, OD_ALIN, OD_IADE, OD_MUAF


# ==============================================================
# VETERİNER ADMIN – %100 HATASIZ
# ==============================================================
class VeterinerAdminForm(forms.ModelForm):
    kullanici_adi = forms.CharField(
        max_length=150, required=False, label="Kullanıcı Adı",
        help_text="Boş bırakılırsa veteriner adına göre otomatik oluşturulur."
    )
    sifre = forms.CharField(
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        required=False, label="Şifre",
        help_text="Boş bırakılırsa 16 karakter güçlü otomatik şifre üretilir."
    )
    sifre_tekrar = forms.CharField(
        widget=forms.PasswordInput(), required=False, label="Şifre Tekrar"
    )

    class Meta:
        model = Veteriner
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        kullanici_adi = cleaned_data.get('kullanici_adi')
        sifre = cleaned_data.get('sifre')
        sifre_tekrar = cleaned_data.get('sifre_tekrar')
        email = cleaned_data.get('email')

        if sifre and sifre != sifre_tekrar:
            raise forms.ValidationError("Şifreler eşleşmiyor.")

        if kullanici_adi:
            if User.objects.filter(username=kullanici_adi).exists():
                # Mevcut veterinerin kendi kullanıcı adı mı kontrol et
                if (self.instance.pk and 
                    hasattr(self.instance, 'kullanici') and 
                    self.instance.kullanici and  # None kontrolü
                    self.instance.kullanici.username == kullanici_adi):
                    pass  # Kendi kullanıcı adı, hata yok
                else:
                    raise forms.ValidationError("Bu kullanıcı adı zaten alınmış.")

        if email and User.objects.filter(email=email).exists():
            # Mevcut veterinerin kendi email'i mi kontrol et
            if (self.instance.pk and 
                hasattr(self.instance, 'kullanici') and 
                self.instance.kullanici and  # None kontrolü
                self.instance.kullanici.email == email):
                pass  # Kendi email'i, hata yok
            else:
                raise forms.ValidationError("Bu e-posta adresi zaten kullanılıyor.")

        return cleaned_data


@admin.register(Veteriner)
class VeterinerAdmin(admin.ModelAdmin):
    form = VeterinerAdminForm

    list_display = (
        "ad", "il_display", "ilce_display", "telefon",
        "danisman_sahip_sayisi_goster",
        "kalan_envanter_goster",
        "tahsis_sayisi_goster",
        "satis_sayisi_goster",
        "aktif"
    )
    list_filter = ("aktif", "odeme_modeli", "il", "ilce")
    search_fields = ("ad", "telefon", "email", "il__ad", "ilce__ad")
    ordering = ("-olusturulma",)

    # Sadece modelde gerçekten olan alanlar
    readonly_fields = ("olusturulma",)

    fieldsets = (
        ("Temel Bilgiler", {
            "fields": ("ad", "telefon", "email", "il", "ilce", "adres_detay", "konum_koordinat")
        }),
        ("Veteriner Özellikleri", {
            "fields": ("uzmanlik_alanlari", "calisma_saatleri", "acil_hizmet", "evde_hizmet")
        }),
        ("Sistem Bilgileri", {
            "fields": ("kullanici", "odeme_modeli", "aktif", "olusturulma")
        }),
        ("Yeni Kullanıcı Hesabı Oluştur", {
            "description": "Yeni veteriner için kullanıcı hesabı oluşturun.",
            "fields": ("kullanici_adi", "sifre", "sifre_tekrar")
        }),
    )

    class Media:
        js = ('admin/js/veteriner_admin.js',)

    # ---------- Yardımcı metodlar ----------
    def il_display(self, obj):
        return obj.il.ad if obj.il else "-"
    il_display.short_description = "İl"
    il_display.admin_order_field = "il__ad"

    def ilce_display(self, obj):
        return obj.ilce.ad if obj.ilce else "-"
    ilce_display.short_description = "İlçe"
    ilce_display.admin_order_field = "ilce__ad"

    def danisman_sahip_sayisi_goster(self, obj):
        return obj.danisman_sahip_sayisi if obj.pk else "-"
    danisman_sahip_sayisi_goster.short_description = "Danışman Sahip"

    def kalan_envanter_goster(self, obj):
        return obj.kalan_envanter if obj.pk else "-"
    kalan_envanter_goster.short_description = "Kalan Envanter"

    def tahsis_sayisi_goster(self, obj):
        return obj.tahsis_sayisi if obj.pk else "-"
    tahsis_sayisi_goster.short_description = "Tahsis Sayısı"

    def satis_sayisi_goster(self, obj):
        return obj.satis_sayisi if obj.pk else "-"
    satis_sayisi_goster.short_description = "Satış Sayısı"

    def kapasite_durumu_goster(self, obj):
        durum = obj.kapasite_durumu
        renk = {"Dolu": "red", "Doluya Yakın": "orange", "Orta": "green", "Boş": "gray"}.get(durum, "gray")
        return format_html('<span style="color:{};font-weight:bold;">{} {}</span>', renk, "Circle", durum)
    kapasite_durumu_goster.short_description = "Kapasite"

    # ---------- İl → İlçe dinamik ----------
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "ilce":
            il_id = None
            # Düzenleme ekranı
            obj_id = request.resolver_match.kwargs.get('object_id')
            if obj_id:
                try:
                    obj = Veteriner.objects.get(pk=obj_id)
                    il_id = obj.il_id
                except Veteriner.DoesNotExist:
                    pass
            # Form submit sırasında
            if not il_id and request.method == "POST":
                il_id = request.POST.get("il")

            if il_id:
                kwargs["queryset"] = Ilce.objects.filter(il_id=il_id).order_by("ad")
            else:
                kwargs["queryset"] = Ilce.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # ---------- Güçlü şifre ----------
    def _generate_password(self):
        alphabet = string.ascii_letters + string.digits + "!@#$%&*"
        return ''.join(secrets.choice(alphabet) for _ in range(16))

    # ---------- save_model ----------
    def save_model(self, request, obj, form, change):
        if not change:  # yeni kayıt
            kullanici_adi = form.cleaned_data.get("kullanici_adi") or ""
            sifre = form.cleaned_data.get("sifre")

            # Kullanıcı adı yoksa otomatik üret
            if not kullanici_adi.strip():
                base = obj.ad.lower().replace(" ", "_")
                kullanici_adi = base
                i = 1
                while User.objects.filter(username=kullanici_adi).exists():
                    kullanici_adi = f"{base}_{i}"
                    i += 1

            # Şifre yoksa otomatik üret
            if not sifre:
                sifre = self._generate_password()
                auto_gen = True
            else:
                auto_gen = False

            user = User.objects.create_user(
                username=kullanici_adi,
                password=sifre,
                email=obj.email or "",
                first_name=obj.ad.split()[0] if obj.ad else "",
                last_name=" ".join(obj.ad.split()[1:]) if len(obj.ad.split()) > 1 else ""
            )
            obj.kullanici = user

            auto_msg = format_html(
                '<div style="background:#fff3cd;padding:10px;border-radius:5px;margin:10px 0;">'
                '<strong>Otomatik güçlü şifre oluşturuldu!</strong></div>'
            ) if auto_gen else ""

            messages.success(request, format_html(
                '{}'
                '<div style="background:#d4edda;padding:15px;border-radius:8px;margin:15px 0;">'
                '<h4>Veteriner Hesabı Oluşturuldu</h4>'
                '<p><strong>Veteriner:</strong> {}</p>'
                '<p><strong>Kullanıcı adı:</strong> <code>{}</code></p>'
                '<p><strong>Şifre:</strong> <code style="background:#fff3cd;padding:6px 12px;border-radius:4px;font-size:1.1em;">{}</code></p>'
                '<p style="color:#856404;margin-top:12px;"><strong>Bu şifre bir daha gösterilmeyecek!</strong></p>'
                '</div>',
                auto_msg, obj.ad, kullanici_adi, sifre
            ))

        super().save_model(request, obj, form, change)


# ==============================================================
# DİĞER ADMINLER (hata yok)
# ==============================================================
@admin.register(VeterinerYuzde)
class VeterinerYuzdeAdmin(admin.ModelAdmin):
    list_display = ("veteriner", "ilce", "yuzde", "son_guncelleme")
    list_filter = ("ilce", "son_guncelleme")
    search_fields = ("veteriner__ad", "ilce__ad")
    readonly_fields = ("son_guncelleme",)


@admin.register(SiparisIstemi)
class SiparisIstemiAdmin(admin.ModelAdmin):
    list_display = ("veteriner", "talep_edilen_adet", "talep_tarihi", "onaylandi",
                    "numune_mi", "odeme_durumu", "kargolandimi", "kargo_takip_no")
    list_filter = ("onaylandi", "numune_mi", "odeme_durumu", "kargolandimi", "talep_tarihi")
    search_fields = ("veteriner__ad", "kargo_takip_no")
    readonly_fields = ("talep_tarihi", "onay_tarihi", "kargo_tarihi", "odeme_alinma_tarihi")
    actions = ["onayla", "odeme_alindi", "odeme_iade", "odeme_muaf", "kargolandi"]

    def onayla(self, request, queryset):
        updated = 0
        for s in queryset.filter(onaylandi=False):
            s.onaylandi = True
            s.save()
            updated += 1
        self.message_user(request, f"{updated} sipariş onaylandı.", messages.SUCCESS)
    onayla.short_description = "Onayla & Etiket Oluştur"

    def odeme_alindi(self, request, queryset):
        updated = queryset.update(odeme_durumu=OD_ALIN, odeme_alinma_tarihi=timezone.now())
        self.message_user(request, f"{updated} siparişte ödeme alındı.", messages.SUCCESS)

    def odeme_iade(self, request, queryset):
        updated = queryset.update(odeme_durumu=OD_IADE)
        self.message_user(request, f"{updated} siparişte ödeme iade edildi.", messages.SUCCESS)

    def odeme_muaf(self, request, queryset):
        updated = 0
        for s in queryset:
            s.numune_mi = True
            s.odeme_durumu = OD_MUAF
            s.odeme_tutari = None
            s.save()
            updated += 1
        self.message_user(request, f"{updated} sipariş numune yapıldı.", messages.SUCCESS)

    def kargolandi(self, request, queryset):
        ok = skipped = 0
        for s in queryset:
            if s.numune_mi or s.odeme_durumu == OD_ALIN:
                s.kargolandimi = True
                s.kargo_tarihi = timezone.now()
                s.save()
                ok += 1
            else:
                skipped += 1
        if ok: self.message_user(request, f"{ok} sipariş kargolandı.", messages.SUCCESS)
        if skipped: self.message_user(request, f"{skipped} atlandı (ödeme eksik).", messages.WARNING)