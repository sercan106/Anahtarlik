"""
Management command to fix duplicate email addresses in User model.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models import Count


class Command(BaseCommand):
    help = 'Duplicate e-posta adreslerini düzelt'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Sadece rapor ver, değişiklik yapma',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.WARNING('Duplicate e-postalar kontrol ediliyor...'))
        
        # Duplicate e-postaları bul
        duplicates = User.objects.values('email').annotate(
            count=Count('email')
        ).filter(count__gt=1, email__isnull=False).exclude(email='')
        
        if not duplicates:
            self.stdout.write(self.style.SUCCESS('[OK] Duplicate e-posta bulunamadi!'))
            return
        
        self.stdout.write(self.style.ERROR(f'[HATA] {len(duplicates)} duplicate e-posta bulundu:'))
        
        total_fixed = 0
        
        for dup in duplicates:
            email = dup['email']
            count = dup['count']
            users = User.objects.filter(email=email).order_by('date_joined')
            
            self.stdout.write(f'\n[EMAIL] {email} ({count} kullanici)')
            
            for i, user in enumerate(users):
                if i == 0:
                    self.stdout.write(f'  [OK] #{user.id} - {user.username} - {user.date_joined} (KORUNDU)')
                else:
                    old_email = user.email
                    new_email = f"{email.split('@')[0]}_dup{i}@{email.split('@')[1]}"
                    
                    if not dry_run:
                        user.email = new_email
                        user.save(update_fields=['email'])
                        self.stdout.write(f'  [FIX] #{user.id} - {user.username} - {old_email} -> {new_email}')
                    else:
                        self.stdout.write(f'  [DRY] #{user.id} - {user.username} - {old_email} -> {new_email} (DRY RUN)')
                    
                    total_fixed += 1
        
        if dry_run:
            self.stdout.write(f'\n{self.style.WARNING(f"DRY RUN: {total_fixed} e-posta duzeltilecek")}')
            self.stdout.write('Degisiklikleri uygulamak icin --dry-run olmadan calistirin.')
        else:
            self.stdout.write(f'\n{self.style.SUCCESS(f"[OK] {total_fixed} duplicate e-posta duzeltildi!")}')
            
            # Artik unique constraint eklenebilir
            self.stdout.write('\n' + self.style.WARNING('[ONEMLI]:'))
            self.stdout.write('Artik User modelinde email unique yapabilirsiniz.')
            self.stdout.write('settings.py\'de AUTH_USER_MODEL ayarlamasi gerekebilir.')

