# shop/email_utils.py - Email bildirim sistemi
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)

def send_order_confirmation_email(siparis):
    """
    Sipariş onay email'i gönder
    """
    try:
        # Email alıcısını belirle
        if siparis.kullanici:
            recipient_email = siparis.kullanici.email
            recipient_name = siparis.kullanici.get_full_name() or siparis.kullanici.username
        else:
            recipient_email = siparis.misafir_email
            recipient_name = siparis.misafir_ad_soyad or "Değerli Müşterimiz"
        
        if not recipient_email:
            logger.warning(f"Sipariş {siparis.id} için email adresi bulunamadı")
            return False

        # Context hazırla
        context = {
            'siparis': siparis,
            'recipient_name': recipient_name,
            'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
            'contact_email': getattr(settings, 'CONTACT_EMAIL', 'info@petsafehub.com'),
        }

        # HTML template'i render et
        html_content = render_to_string('shop/emails/siparis_onay.html', context)
        
        # Email oluştur
        subject = f"✅ Sipariş Onayı - #{siparis.id} - PetSafe Hub"
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=f"Siparişiniz onaylandı. Sipariş numaranız: #{siparis.id}",
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@petsafehub.com'),
            to=[recipient_email]
        )
        
        email.attach_alternative(html_content, "text/html")
        
        # Email gönder
        result = email.send()
        
        if result:
            logger.info(f"Sipariş onay email'i gönderildi: {recipient_email} - Sipariş #{siparis.id}")
            return True
        else:
            logger.error(f"Sipariş onay email'i gönderilemedi: {recipient_email} - Sipariş #{siparis.id}")
            return False
            
    except Exception as e:
        logger.error(f"Sipariş onay email hatası: {str(e)} - Sipariş #{siparis.id}")
        return False

def send_shipping_notification_email(siparis, kargo_tarihi=None):
    """
    Kargo gönderildi email'i gönder
    """
    try:
        # Email alıcısını belirle
        if siparis.kullanici:
            recipient_email = siparis.kullanici.email
            recipient_name = siparis.kullanici.get_full_name() or siparis.kullanici.username
        else:
            recipient_email = siparis.misafir_email
            recipient_name = siparis.misafir_ad_soyad or "Değerli Müşterimiz"
        
        if not recipient_email:
            logger.warning(f"Sipariş {siparis.id} için email adresi bulunamadı")
            return False

        # Kargo tarihi belirle
        if not kargo_tarihi:
            kargo_tarihi = timezone.now()

        # Context hazırla
        context = {
            'siparis': siparis,
            'recipient_name': recipient_name,
            'kargo_tarihi': kargo_tarihi,
            'tahmini_teslimat': "2-3 iş günü",  # Bu değer kargo firmasına göre değişebilir
            'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
            'contact_email': getattr(settings, 'CONTACT_EMAIL', 'info@petsafehub.com'),
        }

        # HTML template'i render et
        html_content = render_to_string('shop/emails/kargo_gonderildi.html', context)
        
        # Email oluştur
        subject = f"📦 Siparişiniz Kargoya Verildi - #{siparis.id} - PetSafe Hub"
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=f"Siparişiniz kargoya verildi. Takip numaranız: {siparis.kargo_takip_no or 'Henüz atanmadı'}",
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@petsafehub.com'),
            to=[recipient_email]
        )
        
        email.attach_alternative(html_content, "text/html")
        
        # Email gönder
        result = email.send()
        
        if result:
            logger.info(f"Kargo bildirim email'i gönderildi: {recipient_email} - Sipariş #{siparis.id}")
            return True
        else:
            logger.error(f"Kargo bildirim email'i gönderilemedi: {recipient_email} - Sipariş #{siparis.id}")
            return False
            
    except Exception as e:
        logger.error(f"Kargo bildirim email hatası: {str(e)} - Sipariş #{siparis.id}")
        return False

def send_order_cancellation_email(siparis, iptal_nedeni=None, iade_yontemi=None, iade_takip_no=None):
    """
    Sipariş iptal email'i gönder
    """
    try:
        # Email alıcısını belirle
        if siparis.kullanici:
            recipient_email = siparis.kullanici.email
            recipient_name = siparis.kullanici.get_full_name() or siparis.kullanici.username
        else:
            recipient_email = siparis.misafir_email
            recipient_name = siparis.misafir_ad_soyad or "Değerli Müşterimiz"
        
        if not recipient_email:
            logger.warning(f"Sipariş {siparis.id} için email adresi bulunamadı")
            return False

        # Context hazırla
        context = {
            'siparis': siparis,
            'recipient_name': recipient_name,
            'iptal_tarihi': timezone.now(),
            'iptal_nedeni': iptal_nedeni or "Stok yetersizliği",
            'iade_yontemi': iade_yontemi or "Orijinal ödeme yöntemine",
            'iade_suresi': "3-5 iş günü",
            'iade_takip_no': iade_takip_no,
            'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
            'contact_email': getattr(settings, 'CONTACT_EMAIL', 'info@petsafehub.com'),
        }

        # HTML template'i render et
        html_content = render_to_string('shop/emails/siparis_iptal.html', context)
        
        # Email oluştur
        subject = f"❌ Sipariş İptal Edildi - #{siparis.id} - PetSafe Hub"
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=f"Siparişiniz iptal edildi. Sipariş numaranız: #{siparis.id}",
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@petsafehub.com'),
            to=[recipient_email]
        )
        
        email.attach_alternative(html_content, "text/html")
        
        # Email gönder
        result = email.send()
        
        if result:
            logger.info(f"Sipariş iptal email'i gönderildi: {recipient_email} - Sipariş #{siparis.id}")
            return True
        else:
            logger.error(f"Sipariş iptal email'i gönderilemedi: {recipient_email} - Sipariş #{siparis.id}")
            return False
            
    except Exception as e:
        logger.error(f"Sipariş iptal email hatası: {str(e)} - Sipariş #{siparis.id}")
        return False

def send_stock_warning_email(urun, min_stok_seviyesi=5, uyari_seviyesi=10):
    """
    Stok uyarı email'i gönder (admin'lere)
    """
    try:
        # Admin email'lerini al
        admin_emails = getattr(settings, 'ADMIN_EMAILS', [])
        if not admin_emails:
            # Django admin kullanıcılarından email al
            from django.contrib.auth.models import User
            admin_emails = list(User.objects.filter(is_superuser=True).values_list('email', flat=True))
            admin_emails = [email for email in admin_emails if email]
        
        if not admin_emails:
            logger.warning("Admin email adresi bulunamadı")
            return False

        # Context hazırla
        context = {
            'urun': urun,
            'min_stok_seviyesi': min_stok_seviyesi,
            'uyari_seviyesi': uyari_seviyesi,
            'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
            'contact_email': getattr(settings, 'CONTACT_EMAIL', 'info@petsafehub.com'),
        }

        # HTML template'i render et
        html_content = render_to_string('shop/emails/stok_uyari.html', context)
        
        # Email oluştur
        subject = f"⚠️ Stok Uyarısı - {urun.ad} - PetSafe Hub"
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=f"Ürün stokları azaldı: {urun.ad} - Kalan stok: {urun.stok}",
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@petsafehub.com'),
            to=admin_emails
        )
        
        email.attach_alternative(html_content, "text/html")
        
        # Email gönder
        result = email.send()
        
        if result:
            logger.info(f"Stok uyarı email'i gönderildi: {urun.ad} - Kalan stok: {urun.stok}")
            return True
        else:
            logger.error(f"Stok uyarı email'i gönderilemedi: {urun.ad}")
            return False
            
    except Exception as e:
        logger.error(f"Stok uyarı email hatası: {str(e)} - Ürün: {urun.ad}")
        return False

def send_bulk_email(recipients, subject, template_name, context=None):
    """
    Toplu email gönder
    """
    try:
        if context is None:
            context = {}
        
        # Site bilgilerini context'e ekle
        context.update({
            'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
            'contact_email': getattr(settings, 'CONTACT_EMAIL', 'info@petsafehub.com'),
        })

        # HTML template'i render et
        html_content = render_to_string(template_name, context)
        
        # Her alıcı için ayrı email gönder
        success_count = 0
        for recipient_email in recipients:
            if not recipient_email:
                continue
                
            email = EmailMultiAlternatives(
                subject=subject,
                body=subject,  # Basit text versiyonu
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@petsafehub.com'),
                to=[recipient_email]
            )
            
            email.attach_alternative(html_content, "text/html")
            
            if email.send():
                success_count += 1
        
        logger.info(f"Toplu email gönderildi: {success_count}/{len(recipients)} başarılı")
        return success_count
        
    except Exception as e:
        logger.error(f"Toplu email hatası: {str(e)}")
        return 0

def check_and_send_stock_warnings():
    """
    Stok seviyelerini kontrol et ve uyarı gönder
    """
    from .models import Urun
    
    try:
        # Düşük stoklu ürünleri bul
        min_stok = 5
        uyari_stok = 10
        
        dusuk_stok_urunler = Urun.objects.filter(
            aktif=True,
            stok__lte=uyari_stok,
            stok__gt=0  # Stok tükenmiş olanları hariç tut
        )
        
        tükenen_urunler = Urun.objects.filter(
            aktif=True,
            stok=0
        )
        
        # Uyarı gönder
        for urun in dusuk_stok_urunler:
            send_stock_warning_email(urun, min_stok, uyari_stok)
        
        for urun in tükenen_urunler:
            send_stock_warning_email(urun, min_stok, uyari_stok)
        
        logger.info(f"Stok kontrolü tamamlandı: {dusuk_stok_urunler.count()} düşük stok, {tükenen_urunler.count()} tükenen")
        return True
        
    except Exception as e:
        logger.error(f"Stok kontrolü hatası: {str(e)}")
        return False

