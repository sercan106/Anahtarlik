from django.core.management.base import BaseCommand
from shop.models import KargoFirma

class Command(BaseCommand):
    help = 'Kargo firmaları oluştur'

    def handle(self, *args, **options):
        # Mevcut kargo firmalarını temizle
        KargoFirma.objects.all().delete()
        
        # Yeni kargo firmaları oluştur
        cargo_companies = [
            {
                'ad': 'Aras Kargo',
                'sabit_ucret': 15.00,
                'ucretsiz_kargo_limiti': 200.00,
                'tahmini_sure_gun': 2,
                'sira': 1,
                'aktif': True
            },
            {
                'ad': 'Yurtiçi Kargo',
                'sabit_ucret': 12.00,
                'ucretsiz_kargo_limiti': 150.00,
                'tahmini_sure_gun': 3,
                'sira': 2,
                'aktif': True
            },
            {
                'ad': 'MNG Kargo',
                'sabit_ucret': 18.00,
                'ucretsiz_kargo_limiti': 250.00,
                'tahmini_sure_gun': 2,
                'sira': 3,
                'aktif': True
            },
            {
                'ad': 'PTT Kargo',
                'sabit_ucret': 10.00,
                'ucretsiz_kargo_limiti': 100.00,
                'tahmini_sure_gun': 4,
                'sira': 4,
                'aktif': True
            },
            {
                'ad': 'Sürat Kargo',
                'sabit_ucret': 20.00,
                'ucretsiz_kargo_limiti': 300.00,
                'tahmini_sure_gun': 1,
                'sira': 5,
                'aktif': True
            }
        ]
        
        for company_data in cargo_companies:
            KargoFirma.objects.create(**company_data)
            self.stdout.write(
                self.style.SUCCESS(f'Kargo firması oluşturuldu: {company_data["ad"]}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Toplam {len(cargo_companies)} kargo firması oluşturuldu!')
        )
