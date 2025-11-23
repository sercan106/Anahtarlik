from decimal import Decimal

from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from shop.models import Kategori, Urun, Siparis


class PetshopListViewTests(TestCase):
    def setUp(self):
        self.parent = Kategori.objects.create(ad='Kedi Ürünleri', slug='kedi-urunleri')
        self.child1 = Kategori.objects.create(ad='Mama', slug='kedi-mama', parent=self.parent)
        self.child2 = Kategori.objects.create(ad='Oyuncak', slug='kedi-oyuncak', parent=self.parent)

        urun_parent = Urun.objects.create(
            ad='Kedi Tırmalama Tahtası',
            aciklama='Dayanıklı tırmalama tahtası',
            fiyat=Decimal('150'),
            stok=10,
            urun_tipi='normal',
        )
        urun_parent.kategoriler.add(self.parent)

        urun_child1 = Urun.objects.create(
            ad='Premium Kedi Maması',
            aciklama='Tam besleyici mama',
            fiyat=Decimal('90'),
            stok=25,
            urun_tipi='normal',
        )
        urun_child1.kategoriler.add(self.child1)

        urun_child2 = Urun.objects.create(
            ad='Zilli Kedi Topu',
            aciklama='Eğlenceli kedi oyuncağı',
            fiyat=Decimal('20'),
            stok=40,
            urun_tipi='normal',
        )
        urun_child2.kategoriler.add(self.child2)

    def test_category_counts_and_query_efficiency(self):
        url = reverse('shop:petshop_list')
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Sorgu sayısının makul seviyede kaldığını doğrula
        self.assertLess(len(queries), 25, msg=f"Sorgu sayısı yüksek: {len(queries)}")

        ana_kategoriler = response.context['ana_kategoriler']
        parent_category = next(cat for cat in ana_kategoriler if cat.id == self.parent.id)

        # Ana kategoride 3 ürün (kendisi + 2 alt kategorideki ürünler)
        self.assertEqual(parent_category.urun_sayisi, 3)

        child_counts = {child.id: child.urun_sayisi for child in parent_category.alt_kategoriler_liste}
        self.assertEqual(child_counts[self.child1.id], 1)
        self.assertEqual(child_counts[self.child2.id], 1)

        # Toplam ürün sayısı context'te doğru dönmeli
        self.assertEqual(response.context['toplam_urun'], 3)


class AdminOrderListTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username='admin', password='test123', is_staff=True)

        self.user1 = User.objects.create_user(username='alice', password='pass')
        self.user2 = User.objects.create_user(username='bob', password='pass')

        self.order1_user1 = Siparis.objects.create(
            kullanici=self.user1,
            toplam_fiyat=Decimal('100'),
            adres='Adres 1'
        )
        self.order2_user1 = Siparis.objects.create(
            kullanici=self.user1,
            toplam_fiyat=Decimal('150'),
            adres='Adres 2'
        )
        self.order_user2 = Siparis.objects.create(
            kullanici=self.user2,
            toplam_fiyat=Decimal('200'),
            adres='Adres 3'
        )
        self.guest_order = Siparis.objects.create(
            kullanici=None,
            toplam_fiyat=Decimal('80'),
            adres='Misafir Adres',
            misafir_ad_soyad='Misafir Kullanıcı',
            misafir_email='guest@example.com'
        )

        self.client.force_login(self.staff_user)

    def test_user_order_counts_are_annotated(self):
        url = reverse('shop:admin_siparis_yonet')
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertLess(len(queries), 40, msg=f"Admin sipariş listesi sorgu sayısı beklenenden fazla: {len(queries)}")

        orders = list(response.context['siparisler'])
        counts = {order.id: order.user_order_count for order in orders}

        self.assertEqual(counts[self.order1_user1.id], 2)
        self.assertEqual(counts[self.order2_user1.id], 2)
        self.assertEqual(counts[self.order_user2.id], 1)

        guest_order = next(order for order in orders if order.id == self.guest_order.id)
        self.assertEqual(guest_order.user_order_count, 1)
