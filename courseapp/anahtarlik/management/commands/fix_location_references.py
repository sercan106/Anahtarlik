from django.core.management.base import BaseCommand
from django.db import connection
from anahtarlik.dictionaries import Il, Ilce, Mahalle
import random


class Command(BaseCommand):
    help = 'Il/ilce/mahalle referanslarini yeni yuklenmiş verilerden rastgele atar'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Il/ilce/mahalle referanslari duzeltiliyor...'))

        # Tum il/ilce/mahalle verilerini once yukle (performans icin)
        tum_iller = list(Il.objects.all())
        tum_ilceler = list(Ilce.objects.select_related('il').all())
        tum_mahalleler = list(Mahalle.objects.select_related('ilce__il').all())

        self.stdout.write(f'Yuklenen veriler: {len(tum_iller)} il, {len(tum_ilceler)} ilce, {len(tum_mahalleler)} mahalle')

        # 1. Veteriner modelini duzelt
        self.stdout.write('\n1. Veteriner kayitlari duzeltiliyor...')
        self._fix_veteriner(tum_iller, tum_ilceler)

        # 2. PetShop modelini duzelt
        self.stdout.write('\n2. PetShop kayitlari duzeltiliyor...')
        self._fix_petshop(tum_iller, tum_ilceler)

        # 3. Sahip modelini duzelt
        self.stdout.write('\n3. Sahip kayitlari duzeltiliyor...')
        self._fix_sahip(tum_iller, tum_ilceler, tum_mahalleler)

        # 4. KullaniciAdresi modelini duzelt
        self.stdout.write('\n4. KullaniciAdresi kayitlari duzeltiliyor...')
        self._fix_kullanici_adresi(tum_iller, tum_ilceler, tum_mahalleler)

        # 5. Shop Adres modelini duzelt
        self.stdout.write('\n5. Shop Adres kayitlari duzeltiliyor...')
        self._fix_shop_adres(tum_iller, tum_ilceler, tum_mahalleler)

        # 6. HayvanProfili modelini duzelt
        self.stdout.write('\n6. HayvanProfili kayitlari duzeltiliyor...')
        self._fix_hayvan_profili(tum_iller, tum_ilceler)

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('TUM IL/ILCE/MAHALLE REFERANSLARI DUZELTILDI!'))
        self.stdout.write('='*60)

    def _fix_veteriner(self, tum_iller, tum_ilceler):
        """Veteriner modelindeki il/ilce referanslarini duzelt"""
        from veteriner.models import Veteriner

        veterinerler = Veteriner.objects.all()
        guncellenen = 0

        for vet in veterinerler:
            rastgele_il = random.choice(tum_iller)
            # Bu ile bagli ilcelerden birini sec
            il_ilceleri = [ilce for ilce in tum_ilceler if ilce.il_id == rastgele_il.id]
            rastgele_ilce = random.choice(il_ilceleri)

            vet.il = rastgele_il
            vet.ilce = rastgele_ilce
            vet.save(update_fields=['il', 'ilce'])
            guncellenen += 1

        self.stdout.write(self.style.SUCCESS(f'   {guncellenen} Veteriner kaydı guncellendi'))

    def _fix_petshop(self, tum_iller, tum_ilceler):
        """PetShop modelindeki il/ilce referanslarini duzelt"""
        from petshop.models import PetShop

        petshoplar = PetShop.objects.all()
        guncellenen = 0

        for shop in petshoplar:
            rastgele_il = random.choice(tum_iller)
            # Bu ile bagli ilcelerden birini sec
            il_ilceleri = [ilce for ilce in tum_ilceler if ilce.il_id == rastgele_il.id]
            rastgele_ilce = random.choice(il_ilceleri)

            shop.il = rastgele_il
            shop.ilce = rastgele_ilce
            shop.save(update_fields=['il', 'ilce'])
            guncellenen += 1

        self.stdout.write(self.style.SUCCESS(f'   {guncellenen} PetShop kaydı guncellendi'))

    def _fix_sahip(self, tum_iller, tum_ilceler, tum_mahalleler):
        """Sahip modelindeki il/ilce/mahalle referanslarini duzelt"""
        from anahtarlik.models import Sahip

        sahipler = Sahip.objects.all()
        guncellenen = 0

        for sahip in sahipler:
            rastgele_il = random.choice(tum_iller)
            # Bu ile bagli ilcelerden birini sec
            il_ilceleri = [ilce for ilce in tum_ilceler if ilce.il_id == rastgele_il.id]
            rastgele_ilce = random.choice(il_ilceleri)
            # Bu ilceye bagli mahallelerden birini sec
            ilce_mahalleleri = [mahalle for mahalle in tum_mahalleler if mahalle.ilce_id == rastgele_ilce.id]
            rastgele_mahalle = random.choice(ilce_mahalleleri) if ilce_mahalleleri else None

            sahip.il = rastgele_il
            sahip.ilce = rastgele_ilce
            sahip.mahalle = rastgele_mahalle
            sahip.save(update_fields=['il', 'ilce', 'mahalle'])
            guncellenen += 1

        self.stdout.write(self.style.SUCCESS(f'   {guncellenen} Sahip kaydı guncellendi'))

    def _fix_kullanici_adresi(self, tum_iller, tum_ilceler, tum_mahalleler):
        """KullaniciAdresi modelindeki il/ilce/mahalle referanslarini duzelt"""
        from anahtarlik.models import KullaniciAdresi

        adresler = KullaniciAdresi.objects.all()
        guncellenen = 0

        for adres in adresler:
            rastgele_il = random.choice(tum_iller)
            # Bu ile bagli ilcelerden birini sec
            il_ilceleri = [ilce for ilce in tum_ilceler if ilce.il_id == rastgele_il.id]
            rastgele_ilce = random.choice(il_ilceleri)
            # Bu ilceye bagli mahallelerden birini sec
            ilce_mahalleleri = [mahalle for mahalle in tum_mahalleler if mahalle.ilce_id == rastgele_ilce.id]
            rastgele_mahalle = random.choice(ilce_mahalleleri) if ilce_mahalleleri else None

            adres.il = rastgele_il
            adres.ilce = rastgele_ilce
            adres.mahalle = rastgele_mahalle
            adres.save(update_fields=['il', 'ilce', 'mahalle'])
            guncellenen += 1

        self.stdout.write(self.style.SUCCESS(f'   {guncellenen} KullaniciAdresi kaydı guncellendi'))

    def _fix_shop_adres(self, tum_iller, tum_ilceler, tum_mahalleler):
        """Shop Adres modelindeki il/ilce/mahalle referanslarini duzelt"""
        from shop.models import Adres

        adresler = Adres.objects.all()
        guncellenen = 0

        for adres in adresler:
            rastgele_il = random.choice(tum_iller)
            # Bu ile bagli ilcelerden birini sec
            il_ilceleri = [ilce for ilce in tum_ilceler if ilce.il_id == rastgele_il.id]
            rastgele_ilce = random.choice(il_ilceleri)
            # Bu ilceye bagli mahallelerden birini sec
            ilce_mahalleleri = [mahalle for mahalle in tum_mahalleler if mahalle.ilce_id == rastgele_ilce.id]
            rastgele_mahalle = random.choice(ilce_mahalleleri) if ilce_mahalleleri else None

            adres.il = rastgele_il
            adres.ilce = rastgele_ilce
            adres.mahalle = rastgele_mahalle
            adres.save(update_fields=['il', 'ilce', 'mahalle'])
            guncellenen += 1

        self.stdout.write(self.style.SUCCESS(f'   {guncellenen} Shop Adres kaydı guncellendi'))

    def _fix_hayvan_profili(self, tum_iller, tum_ilceler):
        """HayvanProfili modelindeki il/ilce referanslarini duzelt"""
        from ilan.models import HayvanProfili

        profiller = HayvanProfili.objects.all()
        guncellenen = 0

        for profil in profiller:
            rastgele_il = random.choice(tum_iller)
            # Bu ile bagli ilcelerden birini sec
            il_ilceleri = [ilce for ilce in tum_ilceler if ilce.il_id == rastgele_il.id]
            rastgele_ilce = random.choice(il_ilceleri)

            profil.il = rastgele_il
            profil.ilce = rastgele_ilce
            profil.save(update_fields=['il', 'ilce'])
            guncellenen += 1

        self.stdout.write(self.style.SUCCESS(f'   {guncellenen} HayvanProfili kaydı guncellendi'))
