#!/usr/bin/env python
"""
Pet Ürünleri mağaza kartını oluşturur
"""
import os
import sys
import django

# Django setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'courseapp.settings')
django.setup()

from shop.models import MagazaKarti, Urun

def create_pet_urunleri_kart():
    """Pet Ürünleri mağaza kartını oluştur veya güncelle"""
    
    # Mevcut kartı kontrol et
    existing_pet = MagazaKarti.objects.filter(
        baslik__icontains='Pet Ürünleri'
    ).first()
    
    if not existing_pet:
        # Yeni kart oluştur
        pet_kart = MagazaKarti.objects.create(
            baslik='Pet Ürünleri',
            alt_baslik='Evcil dostlarınız için yüksek kaliteli pet ürünleri',
            aciklama='Kedi, köpek ve diğer evcil hayvanlarınız için geniş ürün yelpazesi. Oyuncaklardan mama kaplarına, bakım ürünlerinden aksesuarlara kadar her şey burada.',
            icon='🐾',
            renk='#ff8533',
            link_url='/shop/petshop/',
            buton_metni='Pet Ürünleri',
            sira=1,
            aktif=True,
            urun_sayisi=Urun.objects.filter(urun_tipi='normal', aktif=True).count()
        )
        print(f'✅ Pet Ürünleri kartı oluşturuldu: {pet_kart.baslik}')
    else:
        # Mevcut kartı güncelle
        existing_pet.baslik = 'Pet Ürünleri'
        existing_pet.alt_baslik = 'Evcil dostlarınız için yüksek kaliteli pet ürünleri'
        existing_pet.aciklama = 'Kedi, köpek ve diğer evcil hayvanlarınız için geniş ürün yelpazesi. Oyuncaklardan mama kaplarına, bakım ürünlerinden aksesuarlara kadar her şey burada.'
        existing_pet.icon = '🐾'
        existing_pet.renk = '#ff8533'
        existing_pet.link_url = '/shop/petshop/'
        existing_pet.buton_metni = 'Pet Ürünleri'
        existing_pet.sira = 1
        existing_pet.aktif = True
        existing_pet.urun_sayisi = Urun.objects.filter(urun_tipi='normal', aktif=True).count()
        existing_pet.save()
        print(f'✅ Pet Ürünleri kartı güncellendi ve aktif yapıldı: {existing_pet.baslik}')
    
    print(f'\n📊 Toplam aktif pet ürünü sayısı: {Urun.objects.filter(urun_tipi="normal", aktif=True).count()}')

if __name__ == '__main__':
    create_pet_urunleri_kart()

