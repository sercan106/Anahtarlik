"""
Eski tarama kayıtlarını otomatik temizleme komutu
Kullanım: python manage.py cleanup_scans
Cron: 0 3 * * * cd /path/to/project && python manage.py cleanup_scans
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from etiket.models import EtiketTarama


class Command(BaseCommand):
    help = 'Eski tarama kayıtlarını temizler (30 gün öncesi)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Kaç gün önceki kayıtlar silinsin (varsayılan: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Silmeden önce kaç kayıt silineceğini göster',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        # Cutoff tarihi hesapla
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Silinecek kayıtları bul
        old_scans = EtiketTarama.objects.filter(tarama_zamani__lt=cutoff_date)
        count = old_scans.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS(f'[OK] Silinecek kayit yok ({days} gun oncesi)')
            )
            return
        
        # Dry run modu
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'[DRY RUN] {count} kayit silinecek ({cutoff_date.strftime("%d.%m.%Y")} oncesi)'
                )
            )
            
            # İlk 5 kaydı göster
            sample = old_scans[:5]
            for scan in sample:
                self.stdout.write(
                    f'  - {scan.etiket.seri_numarasi}: {scan.tarama_zamani.strftime("%d.%m.%Y %H:%M")} ({scan.get_lokasyon_kisa()})'
                )
            
            if count > 5:
                self.stdout.write(f'  ... ve {count - 5} kayit daha')
            
            return
        
        # Gerçek silme
        deleted_count = old_scans.delete()[0]
        
        self.stdout.write(
            self.style.SUCCESS(
                f'[OK] {deleted_count} eski tarama kaydi silindi ({days} gun oncesi)'
            )
        )
        
        # İstatistik
        remaining = EtiketTarama.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'[ISTATISTIK] Kalan toplam tarama: {remaining}'
            )
        )

