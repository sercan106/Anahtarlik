from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from anahtarlik.reference import load_tur_irk_from_csv, ReferenceImportError


class Command(BaseCommand):
    help = "Load species and breeds from a CSV file with columns: tur, irk"

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str, help='Path to CSV file (utf-8)')

    def handle(self, *args, **options):
        path = Path(options['csv_path'])
        try:
            created_tur, created_irk = load_tur_irk_from_csv(path)
        except FileNotFoundError:
            raise CommandError(f'File not found: {path}')
        except ReferenceImportError as exc:
            raise CommandError(str(exc))

        self.stdout.write(
            self.style.SUCCESS(
                f'Import completed. New species: {created_tur}, new breeds: {created_irk}'
            )
        )