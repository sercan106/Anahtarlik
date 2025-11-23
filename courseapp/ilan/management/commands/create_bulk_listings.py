import random
from pathlib import Path
from datetime import date, timedelta

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction

from anahtarlik.models import Sahip, EvcilHayvan
from anahtarlik.dictionaries import Tur, Irk, Il, Ilce
from ilan.models import HayvanProfili, Ilan


IMAGE_DIR = Path(
    r"C:\Users\user\Desktop\YAZILIM\Anahtarlık2\courseapp\static\images\hayvan fotoları"
)


class Command(BaseCommand):
    help = "Belirtilen sayıda örnek ilan üretir."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=100, help="Oluşturulacak ilan sayısı")
        parser.add_argument("--featured", type=int, default=40, help="Öne çıkan ilan sayısı")
        parser.add_argument(
            "--username",
            type=str,
            default="bulk_owner",
            help="İlanların ait olacağı kullanıcı adı (yoksa oluşturulur)",
        )

    def handle(self, *args, **options):
        count = options["count"]
        featured_count = options["featured"]
        username = options["username"]

        images = [
            path
            for path in IMAGE_DIR.glob("*")
            if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        ]
        if not images:
            raise CommandError(f"Görsel bulunamadı: {IMAGE_DIR}")

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": f"{username}@example.com",
                "first_name": "Demo",
                "last_name": "Owner",
            },
        )
        if created:
            user.set_password("demo1234")
            user.save()
            self.stdout.write(self.style.WARNING(f"Yeni kullanıcı oluşturuldu: {username}/demo1234"))

        sahip, _ = Sahip.objects.get_or_create(
            kullanici=user,
            defaults={
                "ad": "Demo",
                "soyad": "Owner",
                "telefon": "5550000000",
                "il": Il.objects.first(),
                "ilce": Ilce.objects.first(),
            },
        )
        if sahip.il is None or sahip.ilce is None:
            raise CommandError("Sahip için il/ilçe tanımlı değil. Önce sözlük verilerini yükleyin.")

        turler = list(Tur.objects.all())
        if not turler:
            raise CommandError("Tür sözlüğü boş.")

        iller = list(Il.objects.all())
        if not iller:
            raise CommandError("İl sözlüğü boş.")

        cinsiyetler = ["erkek", "disi"]

        created_listings = 0
        featured_assigned = 0

        for index in range(count):
            tur = random.choice(turler)
            irklar = list(Irk.objects.filter(tur=tur))
            if not irklar:
                continue
            irk = random.choice(irklar)

            il = random.choice(iller)
            ilceler = list(Ilce.objects.filter(il=il))
            if not ilceler:
                continue
            ilce = random.choice(ilceler)

            hayvan_ad = random.choice(
                [
                    "Mia",
                    "Luna",
                    "Max",
                    "Milo",
                    "Daisy",
                    "Leo",
                    "Bella",
                    "Choco",
                    "Lucky",
                    "Pati",
                ]
            ) + f" #{index+1}"

            dogum_tarihi = date.today() - timedelta(days=random.randint(60, 720))
            evcil = EvcilHayvan.objects.create(
                ad=hayvan_ad,
                tur=tur,
                irk=irk,
                cinsiyet=random.choice(cinsiyetler),
                dogum_tarihi=dogum_tarihi,
                sahip=sahip,
                saglik_notu="Sağlıklı ve sevecen.",
                genel_not="Oyun oynamayı çok seviyor.",
            )

            image_path = random.choice(images)
            with image_path.open("rb") as img_file:
                profil = HayvanProfili.objects.create(
                    kullanici=user,
                    evcil_hayvan=evcil,
                    hayvan_adi=hayvan_ad,
                    tur=tur,
                    irk=irk,
                    yas=f"{random.randint(1, 5)} Yaş",
                    cinsiyet="ERKEK" if random.choice(cinsiyetler) == "erkek" else "DISI",
                    il=il,
                    ilce=ilce,
                    aciklama=f"{hayvan_ad} için sevgi dolu bir yuva arıyoruz.",
                    profil_fotografi=File(img_file, name=f"profile_{index}_{image_path.name}"),
                )

            onemli = featured_assigned < featured_count
            if onemli:
                featured_assigned += 1

            Ilan.objects.create(
                hayvan_profili=profil,
                baslik=f"{hayvan_ad} Sahiplendirme İlanı",
                ilan_turu="SAHIPLENDIRME",
                aciklama=f"{hayvan_ad} sevecen ve oyunbaz bir dost. Sorumlu bir aile arıyoruz.",
                onemli_mi=onemli,
                onaylandi=True,
                aktif=True,
                fiyat=None,
            )

            created_listings += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{created_listings} ilan oluşturuldu. Öne çıkan ilan sayısı: {featured_assigned}."
            )
        )

