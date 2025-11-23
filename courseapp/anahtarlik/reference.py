import csv
from pathlib import Path
from typing import Tuple

from django.db import transaction

from anahtarlik.models import Il, Ilce
from anahtarlik.dictionaries import Tur, Irk








def _open_csv_with_fallback(path: Path):
    """Return a text handle for the CSV, trying several encodings."""
    last_error = None
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        handle = path.open("r", encoding=encoding)
        try:
            handle.read(1)
            handle.seek(0)
            return handle
        except UnicodeDecodeError as exc:
            handle.close()
            last_error = exc
    raise ReferenceImportError(f"CSV dosyası {path} desteklenen bir karakter kodlaması ile açılamadı.")

class ReferenceImportError(Exception):
    """Raised when reference data cannot be imported from the provided CSV."""


def load_il_ilce_from_csv(csv_path: Path) -> Tuple[int, int]:
    """Import provinces and districts from the given CSV path.

    The CSV must contain `il` and `ilce` columns. Returns a tuple of
    `(created_il_count, created_ilce_count)` for reporting purposes.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(path)

    created_il = 0
    created_ilce = 0

    with _open_csv_with_fallback(path) as handle:
        reader = csv.DictReader(handle)
        if 'il' not in reader.fieldnames or 'ilce' not in reader.fieldnames:
            raise ReferenceImportError('CSV must include "il" and "ilce" headers.')

        with transaction.atomic():
            for row in reader:
                il_ad = (row.get('il') or '').strip()
                ilce_ad = (row.get('ilce') or '').strip()
                if not il_ad or not ilce_ad:
                    continue

                il, created = Il.objects.get_or_create(ad=il_ad)
                if created:
                    created_il += 1

                _, created = Ilce.objects.get_or_create(il=il, ad=ilce_ad)
                if created:
                    created_ilce += 1

    return created_il, created_ilce


def load_tur_irk_from_csv(csv_path: Path) -> Tuple[int, int]:
    """Import species and breeds from the given CSV path."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(path)

    created_tur = 0
    created_irk = 0

    with _open_csv_with_fallback(path) as handle:
        reader = csv.DictReader(handle)
        if 'tur' not in reader.fieldnames or 'irk' not in reader.fieldnames:
            raise ReferenceImportError('CSV must include "tur" and "irk" headers.')

        with transaction.atomic():
            for row in reader:
                tur_ad = (row.get('tur') or '').strip()
                irk_ad = (row.get('irk') or '').strip()
                if not tur_ad or not irk_ad:
                    continue

                tur, created = Tur.objects.get_or_create(ad=tur_ad)
                if created:
                    created_tur += 1

                _, created = Irk.objects.get_or_create(tur=tur, ad=irk_ad)
                if created:
                    created_irk += 1

    return created_tur, created_irk


def build_breed_options():
    """Return mapping of species choice keys to breed name lists."""
    from anahtarlik.models import EvcilHayvan

    mapping = {}
    choice_map = dict(EvcilHayvan.TUR_SECENEKLERI)
    for key, display in choice_map.items():
        tur_obj = Tur.objects.filter(ad__iexact=display).first()
        if not tur_obj:
            mapping[key] = []
            continue
        mapping[key] = list(tur_obj.irkler.order_by('ad').values_list('ad', flat=True))
    return mapping


def resolve_species_and_breed(tur_key: str | None, irk_name: str | None):
    """Resolve species/breed references for given form values."""
    from anahtarlik.models import EvcilHayvan

    tur_ref = None
    irk_ref = None

    tur_key = (tur_key or '').strip()
    irk_name = (irk_name or '').strip()

    if tur_key:
        choice_map = dict(EvcilHayvan.TUR_SECENEKLERI)
        tur_label = choice_map.get(tur_key, tur_key)
        tur_ref = Tur.objects.filter(ad__iexact=tur_label).first()

    if irk_name:
        queryset = Irk.objects.filter(ad__iexact=irk_name)
        if tur_ref:
            queryset = queryset.filter(tur=tur_ref)
        irk_ref = queryset.first()

    return tur_ref, irk_ref


