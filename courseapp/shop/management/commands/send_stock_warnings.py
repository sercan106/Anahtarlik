# shop/management/commands/send_stock_warnings.py
from django.core.management.base import BaseCommand
from shop.email_utils import check_and_send_stock_warnings

class Command(BaseCommand):
    help = 'Stok seviyelerini kontrol eder ve düşük stoklu ürünler için admin\'lere email gönderir'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-stok',
            type=int,
            default=5,
            help='Minimum stok seviyesi (varsayılan: 5)'
        )
        parser.add_argument(
            '--uyari-stok',
            type=int,
            default=10,
            help='Uyarı stok seviyesi (varsayılan: 10)'
        )

    def handle(self, *args, **options):
        min_stok = options['min_stok']
        uyari_stok = options['uyari_stok']
        
        self.stdout.write(
            self.style.SUCCESS(f'Stok kontrolü başlatılıyor...')
        )
        self.stdout.write(f'Minimum stok seviyesi: {min_stok}')
        self.stdout.write(f'Uyarı stok seviyesi: {uyari_stok}')
        
        try:
            success = check_and_send_stock_warnings()
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS('Stok kontrolü başarıyla tamamlandı!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('Stok kontrolü sırasında hata oluştu!')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Stok kontrolü hatası: {str(e)}')
            )

