"""
Import quote-only products from the Excel catalog for sign codes that have no
price in the price grid (and therefore no entry in the DB yet).

Usage:
    python manage.py import_catalog_supplements data/Fiches_produits.xlsx [--dry-run]

Each row in the spreadsheet that has a code not already in the DB becomes a
Product with is_quote=True / type="quote". Descriptions and SEO meta are
populated later by import_product_content.
"""

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from catalog.models import Category, Product

# Longest prefix matched first (sort by length desc at runtime).
FAMILY_CATEGORIES = {
    "ID":  ("Identification", "identification"),
    "SC":  ("Chantier", "chantier"),
    "SI":  ("Chantier", "chantier"),
    "SR":  ("Chantier", "chantier"),
    "SU":  ("Chantier", "chantier"),
    "SE":  ("Chantier", "chantier"),
    "AB":  ("Danger", "danger"),
    "AK":  ("Danger", "danger"),
    "CE":  ("Obligation", "obligation"),
    "Da":  ("Direction", "direction"),
    "Db":  ("Direction", "direction"),
    "Dc":  ("Direction", "direction"),
    "Dd":  ("Direction", "direction"),
    "De":  ("Direction", "direction"),
    "Df":  ("Direction", "direction"),
    "Dv":  ("Direction", "direction"),
    "Dp":  ("Direction", "direction"),
    "Ea":  ("Localisation", "localisation"),
    "Eb":  ("Localisation", "localisation"),
    "Ec":  ("Localisation", "localisation"),
    "EB":  ("Localisation", "localisation"),
    "KC":  ("Équipement", "equipement"),
    "KD":  ("Équipement", "equipement"),
    "KM":  ("Équipement", "equipement"),
    "KR":  ("Équipement", "equipement"),
    "KS":  ("Équipement", "equipement"),
    "KX":  ("Équipement", "equipement"),
    "XB":  ("Prescription", "prescription"),
    "PM":  ("Localisation", "localisation"),
    "A":   ("Danger", "danger"),
    "B":   ("Prescription", "prescription"),
    "C":   ("Obligation", "obligation"),
    "D":   ("Direction", "direction"),
    "E":   ("Localisation", "localisation"),
    "G":   ("Grands axes", "grands-axes"),
    "H":   ("Gabarit", "gabarit"),
    "J":   ("Localisation", "localisation"),
    "K":   ("Équipement", "equipement"),
    "M":   ("Jalonnement", "jalonnement"),
    "R":   ("Prescription", "prescription"),
}

SHAPE_BY_PREFIX = {
    "triangle": {"A", "AB", "AK"},
    "round":    {"B", "R", "XB"},
}


def _category_for(code: str) -> tuple[str, str]:
    """Return (name, slug) for the best-matching prefix, or a fallback."""
    prefixes = sorted(FAMILY_CATEGORIES, key=len, reverse=True)
    for prefix in prefixes:
        if code.upper().startswith(prefix.upper()):
            return FAMILY_CATEGORIES[prefix]
    return ("Divers", "divers")


def _shape_for(code: str) -> str:
    upper = code.upper()
    for shape, prefixes in SHAPE_BY_PREFIX.items():
        if any(upper.startswith(p.upper()) for p in prefixes):
            return shape
    return "square"


class Command(BaseCommand):
    help = "Create quote-only products from the Excel for codes not yet in the catalog."

    def add_arguments(self, parser):
        parser.add_argument("xlsx", type=str, help="Path to the Excel file")
        parser.add_argument("--dry-run", action="store_true")

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
        wb.close()

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

        # Collect unique codes from Excel (first occurrence wins).
        excel_rows: dict[str, dict] = {}
        for row in rows[1:]:
            code = col(row, "Code panneau")
            if code and code not in excel_rows:
                excel_rows[code] = {
                    "code": code,
                    "nom": col(row, "Nom panneau"),
                }

        # Codes already in DB (case-insensitive).
        existing = {p.base_code.upper() for p in Product.objects.only("base_code")}

        to_create = [
            r for r in excel_rows.values()
            if r["code"].upper() not in existing
        ]

        self.stdout.write(
            f"Excel: {len(excel_rows)} codes — "
            f"{len(existing)} already in DB — "
            f"{len(to_create)} to create"
        )

        if options["dry_run"]:
            for r in to_create[:10]:
                cat_name, _ = _category_for(r["code"])
                self.stdout.write(f"  [DRY RUN] {r['code']} → {cat_name}")
            if len(to_create) > 10:
                self.stdout.write(f"  … and {len(to_create) - 10} more")
            self.stdout.write(self.style.WARNING("Dry run — no changes written."))
            return

        # Ensure categories exist.
        cat_cache: dict[str, Category] = {}
        for name, slug in set(FAMILY_CATEGORIES.values()) | {("Divers", "divers"), ("Gabarit", "gabarit"), ("Jalonnement", "jalonnement"), ("Équipement", "equipement"), ("Chantier", "chantier"), ("Identification", "identification")}:
            cat, _ = Category.objects.get_or_create(slug=slug, defaults={"name": name})
            cat_cache[slug] = cat

        # Existing slugs to avoid collisions.
        seen_slugs = set(Product.objects.values_list("slug", flat=True))

        def uniq_slug(base):
            base = slugify(base)[:120] or "panneau"
            slug, n = base, 2
            while slug in seen_slugs:
                slug = f"{base[:116]}-{n}"
                n += 1
            seen_slugs.add(slug)
            return slug

        created = 0
        with transaction.atomic():
            for r in to_create:
                code = r["code"]
                nom = r["nom"]
                full_name = f"Panneau {code} — {nom}" if nom else f"Panneau {code}"
                new_name = full_name[:297] + "…" if len(full_name) > 300 else full_name

                cat_name, cat_slug = _category_for(code)
                cat = cat_cache.get(cat_slug)

                product = Product.objects.create(
                    base_code=code,
                    name=new_name,
                    slug=uniq_slug(f"panneau-{code}"),
                    shape=_shape_for(code),
                    is_quote=True,
                    type="quote",
                    is_active=True,
                )
                if cat:
                    product.categories.set([cat])
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done — {created} products created."
        ))
