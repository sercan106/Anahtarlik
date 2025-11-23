from django.core.management.base import BaseCommand
from django.db import connection
from anahtarlik.dictionaries import Il, Ilce
import random


class Command(BaseCommand):
    help = 'HayvanProfili il/ilce referanslarini duzelt (migration oncesi)'

    def handle(self, *args, **options):
        iller = list(Il.objects.all())
        ilceler = list(Ilce.objects.all())

        if not iller or not ilceler:
            self.stdout.write(self.style.ERROR('Il veya ilce verisi bulunamadi!'))
            return

        rastgele_il = random.choice(iller)
        il_ilceleri = [i for i in ilceler if i.il_id == rastgele_il.id]
        rastgele_ilce = random.choice(il_ilceleri)

        with connection.cursor() as cursor:
            cursor.execute(
                f'UPDATE ilan_hayvanprofili SET il_id = {rastgele_il.id}, ilce_id = {rastgele_ilce.id}'
            )

        self.stdout.write(self.style.SUCCESS(
            f'HayvanProfili guncellendi: {rastgele_il.ad} - {rastgele_ilce.ad}'
        ))
