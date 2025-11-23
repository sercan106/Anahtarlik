from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
from anahtarlik.models import Bildirim

class Command(BaseCommand):
    help = 'Eski bildirimleri otomatik olarak siler.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Silme işlemini yapmadan sadece kaç bildirimin silineceğini gösterir.',
        )
        parser.add_argument(
            '--force-days',
            type=int,
            help='Belirli gün sayısından eski bildirimleri sil (varsayılan: tür bazlı)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force_days = options.get('force_days')

        self.stdout.write(f'[{timezone.now().strftime("%Y-%m-%d %H:%M:%S")}] Bildirim temizleme işlemi başlatılıyor...')

        total_deleted = 0
        
        if force_days:
            # Belirli gün sayısından eski tüm bildirimleri sil
            cutoff_date = timezone.now() - timedelta(days=force_days)
            old_notifications = Bildirim.objects.filter(olusturma_zamani__lt=cutoff_date)
            
            count = old_notifications.count()
            if count == 0:
                self.stdout.write(
                    self.style.SUCCESS(f'[OK] {force_days} günden eski bildirim bulunamadı')
                )
                return
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f'[DRY RUN] {count} bildirim silinecek ({force_days} günden eski)'
                    )
                )
                self._show_sample_notifications(old_notifications)
                return
            
            deleted_count = old_notifications.delete()[0]
            total_deleted += deleted_count
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'[OK] {deleted_count} bildirim silindi ({force_days} günden eski)'
                )
            )
        else:
            # Tür bazlı temizlik
            notification_types = [
                ('QR_TARAMA', 30),
                ('BULAN_BILGI', 30),
                ('KAYIP_HAYVAN', 30),
                ('GENEL', 7),
                ('SISTEM', 3),
                ('PROMOSYON', 3),
            ]
            
            for tur, days in notification_types:
                cutoff_date = timezone.now() - timedelta(days=days)
                old_notifications = Bildirim.objects.filter(
                    tur=tur,
                    olusturma_zamani__lt=cutoff_date
                )
                
                count = old_notifications.count()
                if count == 0:
                    continue
                
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f'[DRY RUN] {count} {tur} bildirimi silinecek ({days} günden eski)'
                        )
                    )
                    self._show_sample_notifications(old_notifications)
                else:
                    deleted_count = old_notifications.delete()[0]
                    total_deleted += deleted_count
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'[OK] {deleted_count} {tur} bildirimi silindi ({days} günden eski)'
                        )
                    )
        
        if not dry_run:
            remaining = Bildirim.objects.count()
            self.stdout.write(
                self.style.SUCCESS(
                    f'[ISTATISTIK] Toplam silinen: {total_deleted}'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'[ISTATISTIK] Kalan toplam bildirim: {remaining}'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'[DRY RUN] Toplam silinecek bildirim: {total_deleted}'
                )
            )

    def _show_sample_notifications(self, notifications):
        """Örnek bildirimleri göster"""
        sample = notifications[:5]
        for notification in sample:
            self.stdout.write(
                f'  - {notification.sahip.kullanici.username}: {notification.baslik} '
                f'({notification.olusturma_zamani.strftime("%d.%m.%Y %H:%M")})'
            )
        
        if notifications.count() > 5:
            self.stdout.write(f'  ... ve {notifications.count() - 5} bildirim daha')





