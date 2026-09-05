"""
Management command: generate WebP thumbnails for product images.

Reads the committed source PNGs at MEDIA_ROOT/products/<base_code>.png and
writes resized WebP derivatives to MEDIA_ROOT/products/thumbs/:

    <base_code>_240.webp   → catalog grids / home
    <base_code>_480.webp   → product detail (retina for ~320px display)

This command is DB-free: it works purely from files on disk, so it can run at
Docker build time (before any database exists). It is idempotent — existing,
up-to-date thumbnails are skipped unless --force is given.

Options:
  --force   regenerate even if the thumbnail already exists
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from PIL import Image

WIDTHS = (240, 480)
WEBP_QUALITY = 82
# method 0 (fast) .. 6 (best/slowest). 4 balances build time vs. file size.
WEBP_METHOD = 4
SOURCE_SUBDIR = "products"
THUMB_SUBDIR = "products/thumbs"


class Command(BaseCommand):
    help = "Generate WebP thumbnails for product images in MEDIA_ROOT/products/."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Regenerate thumbnails even if they already exist.",
        )

    def handle(self, *args, **options):
        force = options["force"]
        media_root = Path(settings.MEDIA_ROOT)
        source_dir = media_root / SOURCE_SUBDIR
        thumb_dir = media_root / THUMB_SUBDIR
        thumb_dir.mkdir(parents=True, exist_ok=True)

        sources = sorted(source_dir.glob("*.png"))
        if not sources:
            self.stdout.write(self.style.WARNING(f"No source PNGs in {source_dir}"))
            return

        generated = skipped = failed = 0

        for src in sources:
            try:
                src_mtime = src.stat().st_mtime
                with Image.open(src) as img:
                    img = img.convert("RGBA")
                    for width in WIDTHS:
                        out = thumb_dir / f"{src.stem}_{width}.webp"
                        if (
                            not force
                            and out.exists()
                            and out.stat().st_mtime >= src_mtime
                        ):
                            skipped += 1
                            continue
                        thumb = img.copy()
                        thumb.thumbnail((width, width), Image.LANCZOS)
                        thumb.save(out, "WEBP", quality=WEBP_QUALITY, method=WEBP_METHOD)
                        generated += 1
            except Exception as exc:  # noqa: BLE001 — report and continue
                failed += 1
                self.stderr.write(self.style.ERROR(f"{src.name}: {exc}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"thumbnails generated={generated} skipped={skipped} "
                f"failed={failed} (sources={len(sources)}, widths={list(WIDTHS)})"
            )
        )
