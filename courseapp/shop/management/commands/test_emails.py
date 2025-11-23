# shop/management/commands/test_emails.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from shop.models import Urun, Siparis, SiparisKalemi
from shop.email_utils import (
    send_order_confirmation_email,
    send_shipping_notification_email,
    send_order_cancellation_email,
    send_stock_warning_email
)

class Command(BaseCommand):
    help = 'Email sistemini test eder'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Test email adresi (varsayılan: ilk superuser email)'
        )
        parser.add_argument(
            '--test-type',
            type=str,
            choices=['all', 'order', 'shipping', 'cancel', 'stock'],
            default='all',
            help='Test edilecek email tipi'
        )

    def handle(self, *args, **options):
        test_email = options['email']
        test_type = options['test_type']
        
        # Test email adresini belirle
        if not test_email:
            try:
                superuser = User.objects.filter(is_superuser=True).first()
                if superuser and superuser.email:
                    test_email = superuser.email
                else:
                    self.stdout.write(
                        self.style.ERROR('Test email adresi bulunamadı! --email parametresi ile belirtin.')
                    )
                    return
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Email adresi alınırken hata: {str(e)}')
                )
                return
        
        self.stdout.write(f'Test email adresi: {test_email}')
        self.stdout.write(f'Test tipi: {test_type}')
        
        try:
            if test_type in ['all', 'order']:
                self.test_order_confirmation(test_email)
            
            if test_type in ['all', 'shipping']:
                self.test_shipping_notification(test_email)
            
            if test_type in ['all', 'cancel']:
                self.test_order_cancellation(test_email)
            
            if test_type in ['all', 'stock']:
                self.test_stock_warning()
            
            self.stdout.write(
                self.style.SUCCESS('Email testleri tamamlandı!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Test hatası: {str(e)}')
            )

    def test_order_confirmation(self, email):
        """Sipariş onay email'ini test et"""
        self.stdout.write('📧 Sipariş onay email\'i test ediliyor...')
        
        # Test siparişi oluştur
        test_user = User.objects.filter(email=email).first()
        if not test_user:
            # Test kullanıcısı oluştur
            test_user = User.objects.create_user(
                username='test_user',
                email=email,
                password='test123'
            )
        
        # Test ürünü oluştur
        test_urun, created = Urun.objects.get_or_create(
            ad='Test Ürünü',
            defaults={
                'aciklama': 'Test ürünü açıklaması',
                'fiyat': 100.00,
                'stok': 10,
                'urun_tipi': 'normal',
                'aktif': True
            }
        )
        
        # Test siparişi oluştur
        test_siparis = Siparis.objects.create(
            kullanici=test_user,
            toplam_fiyat=100.00,
            adres='Test Adresi\nİstanbul, Türkiye'
        )
        
        # Test sipariş kalemi oluştur
        SiparisKalemi.objects.create(
            siparis=test_siparis,
            urun=test_urun,
            miktar=1,
            fiyat=100.00
        )
        
        # Email gönder
        success = send_order_confirmation_email(test_siparis)
        
        if success:
            self.stdout.write(self.style.SUCCESS('✅ Sipariş onay email\'i başarıyla gönderildi!'))
        else:
            self.stdout.write(self.style.ERROR('❌ Sipariş onay email\'i gönderilemedi!'))
        
        # Test verilerini temizle
        test_siparis.delete()
        if created:
            test_urun.delete()

    def test_shipping_notification(self, email):
        """Kargo bildirim email'ini test et"""
        self.stdout.write('📦 Kargo bildirim email\'i test ediliyor...')
        
        # Test siparişi oluştur
        test_user = User.objects.filter(email=email).first()
        if not test_user:
            test_user = User.objects.create_user(
                username='test_user2',
                email=email,
                password='test123'
            )
        
        test_siparis = Siparis.objects.create(
            kullanici=test_user,
            toplam_fiyat=150.00,
            adres='Test Adresi\nİstanbul, Türkiye',
            kargo_takip_no='TEST123456789'
        )
        
        # Email gönder
        success = send_shipping_notification_email(test_siparis)
        
        if success:
            self.stdout.write(self.style.SUCCESS('✅ Kargo bildirim email\'i başarıyla gönderildi!'))
        else:
            self.stdout.write(self.style.ERROR('❌ Kargo bildirim email\'i gönderilemedi!'))
        
        # Test verilerini temizle
        test_siparis.delete()

    def test_order_cancellation(self, email):
        """Sipariş iptal email'ini test et"""
        self.stdout.write('❌ Sipariş iptal email\'i test ediliyor...')
        
        # Test siparişi oluştur
        test_user = User.objects.filter(email=email).first()
        if not test_user:
            test_user = User.objects.create_user(
                username='test_user3',
                email=email,
                password='test123'
            )
        
        test_siparis = Siparis.objects.create(
            kullanici=test_user,
            toplam_fiyat=200.00,
            adres='Test Adresi\nİstanbul, Türkiye'
        )
        
        # Email gönder
        success = send_order_cancellation_email(
            test_siparis, 
            'Test iptal nedeni',
            'Test iade yöntemi'
        )
        
        if success:
            self.stdout.write(self.style.SUCCESS('✅ Sipariş iptal email\'i başarıyla gönderildi!'))
        else:
            self.stdout.write(self.style.ERROR('❌ Sipariş iptal email\'i gönderilemedi!'))
        
        # Test verilerini temizle
        test_siparis.delete()

    def test_stock_warning(self):
        """Stok uyarı email'ini test et"""
        self.stdout.write('⚠️ Stok uyarı email\'i test ediliyor...')
        
        # Test ürünü oluştur
        test_urun, created = Urun.objects.get_or_create(
            ad='Test Stok Ürünü',
            defaults={
                'aciklama': 'Test stok ürünü açıklaması',
                'fiyat': 50.00,
                'stok': 3,  # Düşük stok
                'urun_tipi': 'normal',
                'aktif': True
            }
        )
        
        # Email gönder
        success = send_stock_warning_email(test_urun, min_stok_seviyesi=5, uyari_seviyesi=10)
        
        if success:
            self.stdout.write(self.style.SUCCESS('✅ Stok uyarı email\'i başarıyla gönderildi!'))
        else:
            self.stdout.write(self.style.ERROR('❌ Stok uyarı email\'i gönderilemedi!'))
        
        # Test verilerini temizle
        if created:
            test_urun.delete()

