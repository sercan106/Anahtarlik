# anahtarlik/management/commands/load_basic_data.py
from django.core.management.base import BaseCommand
from anahtarlik.dictionaries import Tur, Irk, Il, Ilce, Mahalle

class Command(BaseCommand):
    help = 'Temel verileri yükler (tür, ırk, il, ilçe)'

    def handle(self, *args, **options):
        # İlleri oluştur
        iller = [
            'İstanbul', 'Ankara', 'İzmir', 'Bursa', 'Antalya', 'Adana', 'Konya', 'Gaziantep',
            'Mersin', 'Diyarbakır', 'Kayseri', 'Eskişehir', 'Urfa', 'Malatya', 'Erzurum',
            'Van', 'Batman', 'Elazığ', 'Isparta', 'Trabzon'
        ]
        
        for il_adi in iller:
            il, created = Il.objects.get_or_create(ad=il_adi)
            if created:
                self.stdout.write(f'İl oluşturuldu: {il_adi}')
        
        # İlçeleri oluştur
        il_ilce_data = {
            'İstanbul': ['Kadıköy', 'Beşiktaş', 'Şişli', 'Beyoğlu', 'Fatih', 'Üsküdar', 'Bakırköy', 'Zeytinburnu'],
            'Ankara': ['Çankaya', 'Keçiören', 'Yenimahalle', 'Mamak', 'Sincan', 'Etimesgut', 'Altındağ', 'Gölbaşı'],
            'İzmir': ['Konak', 'Karşıyaka', 'Bornova', 'Çiğli', 'Buca', 'Bayraklı', 'Gaziemir', 'Balçova'],
            'Bursa': ['Osmangazi', 'Nilüfer', 'Yıldırım', 'İnegöl', 'Gemlik', 'Mudanya', 'Orhangazi', 'İznik'],
            'Antalya': ['Muratpaşa', 'Kepez', 'Konyaaltı', 'Döşemealtı', 'Aksu', 'Serik', 'Manavgat', 'Alanya']
        }
        
        for il_adi, ilce_listesi in il_ilce_data.items():
            try:
                il = Il.objects.get(ad=il_adi)
                for ilce_adi in ilce_listesi:
                    ilce, created = Ilce.objects.get_or_create(il=il, ad=ilce_adi)
                    if created:
                        self.stdout.write(f'İlçe oluşturuldu: {ilce_adi} ({il_adi})')
            except Il.DoesNotExist:
                self.stdout.write(f'İl bulunamadı: {il_adi}')
        
        # Mahalleleri oluştur
        for il_adi, ilce_listesi in il_ilce_data.items():
            try:
                il = Il.objects.get(ad=il_adi)
                for ilce_adi in ilce_listesi[:3]:  # İlk 3 ilçe için mahalle oluştur
                    try:
                        ilce = Ilce.objects.get(il=il, ad=ilce_adi)
                        mahalle_listesi = [
                            f'{ilce_adi} Merkez', f'{ilce_adi} Mahallesi', f'{ilce_adi} Yeni Mahalle'
                        ]
                        for mahalle_adi in mahalle_listesi:
                            mahalle, created = Mahalle.objects.get_or_create(ilce=ilce, ad=mahalle_adi)
                            if created:
                                self.stdout.write(f'Mahalle oluşturuldu: {mahalle_adi} ({ilce_adi})')
                    except Ilce.DoesNotExist:
                        continue
            except Il.DoesNotExist:
                continue
        
        # Türleri oluştur
        turler = [
            'Kedi', 'Köpek', 'Tavşan', 'Kuş', 'Balık', 'Hamster', 'Guinea Pig', 'Kaplumbağa'
        ]
        
        for tur_adi in turler:
            tur, created = Tur.objects.get_or_create(ad=tur_adi)
            if created:
                self.stdout.write(f'Tür oluşturuldu: {tur_adi}')
        
        # Irkları oluştur
        irk_data = {
            'Kedi': [
                'British Shorthair', 'Van Kedisi', 'Tekir', 'Persian', 'Maine Coon', 
                'Siam Kedisi', 'Scottish Fold', 'Ragdoll', 'Bombay', 'Himalayan'
            ],
            'Köpek': [
                'Golden Retriever', 'Labrador', 'Alman Kurdu', 'Chihuahua', 'Beagle',
                'Husky', 'Poodle', 'Bulldog', 'Rottweiler', 'Doberman'
            ],
            'Tavşan': [
                'Hollanda Cüce Tavşanı', 'Angora Tavşanı', 'Rex Tavşanı', 'Lop Tavşanı',
                'Lionhead Tavşanı', 'Mini Rex', 'Havana Tavşanı', 'Himalayan Tavşanı'
            ],
            'Kuş': [
                'Sultan Papağanı', 'Muhabbet Kuşu', 'Kanarya', 'Finch', 'Cockatiel',
                'Lovebird', 'Conure', 'African Grey', 'Cockatoo', 'Budgie'
            ],
            'Balık': [
                'Japon Balığı', 'Beta Balığı', 'Tetra', 'Guppy', 'Molly', 'Platy',
                'Cichlid', 'Discus', 'Angelfish', 'Neon Tetra'
            ],
            'Hamster': [
                'Suriye Hamsteri', 'Cüce Hamster', 'Roborovski', 'Campbell', 'Winter White'
            ],
            'Guinea Pig': [
                'American', 'Peruvian', 'Abyssinian', 'Teddy', 'Silkie', 'Texel'
            ],
            'Kaplumbağa': [
                'Kırmızı Yanaklı Su Kaplumbağası', 'Rus Kaplumbağası', 'Hermann Kaplumbağası',
                'Yunan Kaplumbağası', 'Marginated Kaplumbağası'
            ]
        }
        
        for tur_adi, irk_listesi in irk_data.items():
            try:
                tur = Tur.objects.get(ad=tur_adi)
                for irk_adi in irk_listesi:
                    irk, created = Irk.objects.get_or_create(tur=tur, ad=irk_adi)
                    if created:
                        self.stdout.write(f'Irk oluşturuldu: {irk_adi} ({tur_adi})')
            except Tur.DoesNotExist:
                self.stdout.write(f'Tür bulunamadı: {tur_adi}')
        
        self.stdout.write(
            self.style.SUCCESS('\n[BASARILI] Temel veriler başarıyla yüklendi!')
        )
