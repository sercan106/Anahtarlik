from django.core.management.base import BaseCommand
from etiket.models import Etiket


class Command(BaseCommand):
    help = 'Son kullanma tarihi geçen etiketleri pasif yapar'

    def handle(self, *args, **options):
        pasiflestirilen_sayisi = Etiket.pasiflestir_suresi_dolanlar()
        
        if pasiflestirilen_sayisi > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'{pasiflestirilen_sayisi} adet etiket son kullanma tarihi geçtiği için pasif yapıldı.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Son kullanma tarihi geçen etiket bulunamadı.')
            )










