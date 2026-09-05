"""
Management command: link committed product images to their Product.

Convention: an image lives at MEDIA_ROOT/products/<base_code>.png and is
matched to the Product whose base_code equals the filename stem. This keeps
the catalog images as build-time assets (Render has no persistent disk) while
still populating Product.image so templates/serializers work unchanged.

Idempotent: run on every deploy. Sets image when the file exists, clears it
when the file is gone.

Options:
  --dry-run   report what would change without writing to the DB
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from catalog.models import Product

IMAGE_SUBDIR = "products"


class Command(BaseCommand):
    help = "Link media/products/<base_code>.png files to their Product by base_code."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report changes without writing to the database.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        media_root = Path(settings.MEDIA_ROOT)

        linked = cleared = already = missing = 0

        for product in Product.objects.all().only("id", "base_code", "image"):
            rel_path = f"{IMAGE_SUBDIR}/{product.base_code}.png"
            abs_path = media_root / rel_path

            if abs_path.exists():
                if product.image.name == rel_path:
                    already += 1
                else:
                    if not dry_run:
                        product.image = rel_path
                        product.save(update_fields=["image"])
                    linked += 1
            else:
                missing += 1
                if product.image:
                    if not dry_run:
                        product.image = ""
                        product.save(update_fields=["image"])
                    cleared += 1

        prefix = "[dry-run] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}linked={linked} already_linked={already} "
                f"cleared={cleared} missing_png={missing}"
            )
        )
