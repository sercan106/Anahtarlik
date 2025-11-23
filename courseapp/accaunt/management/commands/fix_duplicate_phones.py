"""
Management command to fix duplicate phone numbers across profile types.
"""
from django.core.management.base import BaseCommand
from anahtarlik.models import Sahip
from veteriner.models import Veteriner
from petshop.models import PetShop
from accaunt.models import MisafirProfil


class Command(BaseCommand):
    help = 'Duplicate telefon numaralarini duzelt'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Sadece rapor ver, degisiklik yapma',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.WARNING('Duplicate telefonlar kontrol ediliyor...'))
        
        phone_map = {}
        
        # Tum telefonlari topla
        for sahip in Sahip.objects.exclude(telefon='').exclude(telefon__isnull=True):
            phone = sahip.telefon.strip()
            if phone not in phone_map:
                phone_map[phone] = []
            phone_map[phone].append(('Sahip', sahip.id, sahip))
        
        for vet in Veteriner.objects.exclude(telefon='').exclude(telefon__isnull=True):
            phone = vet.telefon.strip()
            if phone not in phone_map:
                phone_map[phone] = []
            phone_map[phone].append(('Veteriner', vet.id, vet))
        
        for petshop in PetShop.objects.exclude(telefon='').exclude(telefon__isnull=True):
            phone = petshop.telefon.strip()
            if phone not in phone_map:
                phone_map[phone] = []
            phone_map[phone].append(('PetShop', petshop.id, petshop))
        
        for misafir in MisafirProfil.objects.exclude(telefon='').exclude(telefon__isnull=True):
            phone = misafir.telefon.strip()
            if phone not in phone_map:
                phone_map[phone] = []
            phone_map[phone].append(('Misafir', misafir.id, misafir))
        
        # Cakismalari bul
        conflicts = {phone: users for phone, users in phone_map.items() if len(users) > 1}
        
        if not conflicts:
            self.stdout.write(self.style.SUCCESS('[OK] Duplicate telefon bulunamadi!'))
            return
        
        self.stdout.write(self.style.ERROR(f'[HATA] {len(conflicts)} duplicate telefon bulundu:'))
        
        total_fixed = 0
        
        for phone, users in conflicts.items():
            self.stdout.write(f'\n[TELEFON] {phone} ({len(users)} profil)')
            
            for i, (profile_type, profile_id, obj) in enumerate(users):
                if i == 0:
                    self.stdout.write(f'  [OK] {profile_type} #{profile_id} (KORUNDU)')
                else:
                    old_phone = phone
                    new_phone = f"{phone}_dup{i}"
                    
                    if not dry_run:
                        obj.telefon = new_phone
                        obj.save(update_fields=['telefon'])
                        self.stdout.write(f'  [FIX] {profile_type} #{profile_id} - {old_phone} -> {new_phone}')
                    else:
                        self.stdout.write(f'  [DRY] {profile_type} #{profile_id} - {old_phone} -> {new_phone} (DRY RUN)')
                    
                    total_fixed += 1
        
        if dry_run:
            self.stdout.write(f'\n{self.style.WARNING(f"DRY RUN: {total_fixed} telefon duzeltilecek")}')
            self.stdout.write('Degisiklikleri uygulamak icin --dry-run olmadan calistirin.')
        else:
            self.stdout.write(f'\n{self.style.SUCCESS(f"[OK] {total_fixed} duplicate telefon duzeltildi!")}')
            self.stdout.write('\n[ONEMLI]: Kullanicilara telefon numaralarinin degistigini bildirin.')
















