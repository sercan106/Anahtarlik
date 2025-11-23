import time
from datetime import timedelta

from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from anahtarlik.dictionaries import Il, Ilce, Mahalle, Tur, Irk
from ilan.models import (
    HayvanProfili,
    Ilan,
    ILAN_SAHIPLENDIRME,
    CINSIYET_ERKEK,
)


class IlanListPerformanceTests(TestCase):
    """Lightweight performance regression checks for ilan listesi view."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="perf_owner",
            email="perf@example.com",
            password="secret123",
        )

        cls.tur = Tur.objects.create(ad="Köpek")
        cls.irk = Irk.objects.create(tur=cls.tur, ad="Golden Retriever")
        cls.il = Il.objects.create(ad="İstanbul")
        cls.ilce = Ilce.objects.create(il=cls.il, ad="Kadıköy")
        cls.mahalle = Mahalle.objects.create(ilce=cls.ilce, ad="Moda")

        ilan_sayisi = 60
        onemli_araligi = 4

        profiller = []
        for index in range(ilan_sayisi):
            profil = HayvanProfili.objects.create(
                kullanici=cls.user,
                hayvan_adi=f"Test Hayvanı {index}",
                tur=cls.tur,
                irk=cls.irk,
                yas="2",
                cinsiyet=CINSIYET_ERKEK,
                asi_durumu=True,
                ic_parazit=True,
                dis_parazit=True,
                sehir_disi_gonderim=False,
                il=cls.il,
                ilce=cls.ilce,
                mahalle=cls.mahalle,
                mahalle_diger="",
                aciklama="Performans testi verisi",
            )
            profiller.append(profil)

        ilanlar = []
        for index, profil in enumerate(profiller):
            ilanlar.append(
                Ilan(
                    hayvan_profili=profil,
                    baslik=f"Performans İlanı {index}",
                    ilan_turu=ILAN_SAHIPLENDIRME,
                    aciklama="Performans testi açıklaması",
                    fiyat=None,
                    onemli_mi=index % onemli_araligi == 0,
                    aktif=True,
                    onaylandi=True,
                    bitis_tarihi=timezone.now() + timedelta(days=30),
                )
            )

        Ilan.objects.bulk_create(ilanlar, batch_size=32)

    def _assert_performance(self, url: str, max_queries: int = 120, max_seconds: float = 1.0):
        with CaptureQueriesContext(connection) as ctx:
            start = time.perf_counter()
            response = self.client.get(url, follow=True)
            elapsed = time.perf_counter() - start

        self.assertEqual(
            response.status_code,
            200,
            f"{url} yanıtı beklenenden farklı ({response.status_code})",
        )
        self.assertLessEqual(
            len(ctx),
            max_queries,
            f"{url} için sorgu sayısı yüksek: {len(ctx)} > {max_queries}",
        )
        self.assertLess(
            elapsed,
            max_seconds,
            f"{url} yanıt süresi beklenenden yüksek: {elapsed:.3f}s > {max_seconds}s",
        )

    def test_normal_list_view_performance(self):
        url = reverse("ilan:ilan_listesi")
        self._assert_performance(url)

    def test_featured_filter_performance(self):
        url = reverse("ilan:ilan_listesi") + "?onemli_ilanlar=1"
        # Filtre sadece vitrin sorgusunu çalıştırdığı için sorgu sayısı daha düşük olmalı
        self._assert_performance(url, max_queries=100, max_seconds=0.8)

