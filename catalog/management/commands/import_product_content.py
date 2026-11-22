"""
Import product content (name, description, meta) from an Excel spreadsheet.

Usage:
    python manage.py import_product_content /path/to/file.xlsx [--dry-run]

Expected columns (row 1 is the header):
    Code panneau | Nom panneau | Description courte | ... | Meta title | Meta description | ...

The command matches rows to Product records via base_code (case-insensitive).
It updates: name, description, meta_title, meta_description.
The name becomes "Panneau {code} — {nom}" when nom differs from the bare code.
"""

import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from catalog.models import Product


class Command(BaseCommand):
    help = "Import product names, descriptions and SEO meta from an Excel file."

    def add_arguments(self, parser):
        parser.add_argument("xlsx", type=str, help="Path to the Excel file")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would change without writing to the database",
        )

    def handle(self, *args, **options):
        xlsx_path = Path(options["xlsx"])
        if not xlsx_path.exists():
            raise CommandError(f"File not found: {xlsx_path}")

        try:
            import openpyxl
        except ImportError:
            raise CommandError("openpyxl is required: pip install openpyxl")

        wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))

        if not rows:
            raise CommandError("The spreadsheet appears to be empty.")

        header = [str(c).strip() if c else "" for c in rows[0]]

        def col(row, name):
            try:
                idx = header.index(name)
                val = row[idx]
                return str(val).strip() if val is not None else ""
            except ValueError:
                return ""

        BRAND = "Le Panneau"
        SITE_TAG = "e-signalisation"

        updated = 0
        skipped = 0
        not_found = []

        dry_run = options["dry_run"]

        for row in rows[1:]:
            code = col(row, "Code panneau")
            if not code:
                continue

            nom = col(row, "Nom panneau")
            description = col(row, "Description courte")
            raw_meta_title = col(row, "Meta title")
            meta_description = col(row, "Meta description")

            # Build the display name: "Panneau A1a — Virage à droite"
            full_name = f"Panneau {code} — {nom}" if nom else f"Panneau {code}"
            new_name = full_name[:297] + "…" if len(full_name) > 300 else full_name

            # Adapt meta title: replace competitor brand tag with ours
            meta_title = raw_meta_title.replace(f"| {SITE_TAG}", f"| {BRAND}").strip()
            # Clamp to 60 chars
            if len(meta_title) > 60:
                meta_title = meta_title[:57] + "…"

            # Clamp meta description to 160 chars
            if len(meta_description) > 160:
                meta_description = meta_description[:157] + "…"

            try:
                product = Product.objects.get(base_code__iexact=code)
            except Product.DoesNotExist:
                not_found.append(code)
                continue

            changed = (
                product.name != new_name
                or product.description != description
                or product.meta_title != meta_title
                or product.meta_description != meta_description
            )

            if not changed:
                skipped += 1
                continue

            if dry_run:
                self.stdout.write(
                    f"[DRY RUN] {code}: name={new_name!r} | "
                    f"meta_title={meta_title!r}"
                )
            else:
                product.name = new_name
                product.description = description
                product.meta_title = meta_title
                product.meta_description = meta_description
                product.save(update_fields=["name", "description", "meta_title", "meta_description"])

            updated += 1

        wb.close()

        self.stdout.write(self.style.SUCCESS(
            f"{'[DRY RUN] ' if dry_run else ''}Done — "
            f"updated: {updated}, unchanged: {skipped}, not found: {len(not_found)}"
        ))
        if not_found:
            self.stdout.write(f"Not found in DB ({len(not_found)}): {', '.join(not_found[:20])}")
            if len(not_found) > 20:
                self.stdout.write(f"  … and {len(not_found) - 20} more")
        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — no changes written."))
        else:
            self.stdout.write("Run with --dry-run first to preview changes.")

        sys.exit(0 if not not_found else 1)
