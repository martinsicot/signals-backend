"""
Management command: import traffic sign panels from Produits.txt.

Source file format: TSV (Latin-1), columns: Code / Libellé / Prix
Only rows with prefix AP, ADP, PV or RP are imported (assembled panels).
Films (AF, RF, ADF), tôles (AT, RT, ADT) and accessories are skipped.

Code anatomy:  {LINE}-{SIGN_CODE} {SIZE}[-{CLASS}]
  LINE      AP = Allegro, ADP = Adagio, PV = Panneau Volet, RP = Rondo
  SIGN_CODE French sign identity: B4, A13A, AB3A, CE15A …  (stored in sign_code)
  SIZE      single mm value (700) or W×H (400X1000)
  CLASS     CL1 or CL2 (reflectivity class)

Categories are derived from the sign series (A, AB, AK, B, BK, C, CE, CK …).

Options:
  --file PATH   override source (default: Produits.txt, next to manage.py)
  --clear       delete all existing Category + Product rows before importing
  --dry-run     parse and count without writing to DB
"""

import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from catalog.models import Category, Product


PANEL_PREFIXES = {"AP", "ADP", "PV", "RP"}

LINE_LABELS = {
    "AP": "Allegro",
    "ADP": "Adagio",
    "PV": "Panneau Volet",
    "RP": "Rondo",
}

# Ordered longest-first so AB/AK/BK/CE/CK/EB are matched before A/B/C/E
SERIES_PREFIXES = ["AK", "AB", "BK", "CE", "CK", "EB"]

SERIES_NAMES = {
    "A": "Panneaux de danger",
    "AB": "Panneaux de priorité",
    "AK": "Signalisation temporaire — Danger",
    "B": "Panneaux d'interdiction et d'obligation",
    "BK": "Signalisation temporaire — Réglementation",
    "C": "Panneaux de direction",
    "CE": "Panneaux de direction spéciaux",
    "CK": "Signalisation temporaire — Direction",
    "D": "Panneaux de service",
    "E": "Panneaux de localisation",
    "EB": "Balises et bornes",
    "J": "Panneaux J",
    "K": "Panneaux K",
    "M": "Panneaux M",
    "S": "Panneaux S",
}

# Handles three separator styles found in the file:
#   AP-B4 700-CL2          (hyphen before CL)
#   ADP-D21 1000X250 CL2   (space before CL)
#   RP-AK14 TRIFLASH 1000-CL1  (variant word between sign and size)
#   AP-C 500X300-CL1 ASSEMBLY POINT  (trailing text after CL, ignored)
# No $ anchor so trailing text is silently ignored.
_CODE_RE = re.compile(
    r"^(?P<line>[A-Z]+)-(?P<sign>[^\s]+)\s+(?:[A-Z]+\s+)?(?P<size>[\dX]+)(?:[\s-](?P<cls>CL\d+))?",
    re.IGNORECASE,
)

MAX_SLUG = 80


def _parse_price(raw: str) -> Decimal | None:
    cleaned = raw.strip().replace(",", ".")
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _get_series(sign_code: str) -> str:
    upper = sign_code.upper()
    for prefix in SERIES_PREFIXES:
        if upper.startswith(prefix):
            return prefix
    return upper[0]


def _build_dimensions(size_str: str) -> str:
    upper = size_str.upper()
    if "X" in upper:
        w, h = upper.split("X", 1)
        return f"{w}×{h} mm"
    return f"{size_str} mm"


def _build_name(sign_code: str, size_str: str, cls: str | None) -> str:
    parts = [f"Panneau {sign_code.upper()}", _build_dimensions(size_str)]
    if cls:
        num = cls.upper().lstrip("CL")
        parts.append(f"Classe {num}")
    return " — ".join(parts)


def _build_slug(line: str, sign_code: str, size_str: str, cls: str | None, seen: set) -> str:
    raw = f"{line}-{sign_code}-{size_str}"
    if cls:
        raw += f"-{cls}"
    base = slugify(raw)[:MAX_SLUG]
    candidate = base
    counter = 2
    while candidate in seen:
        suffix = f"-{counter}"
        candidate = base[: MAX_SLUG - len(suffix)] + suffix
        counter += 1
    seen.add(candidate)
    return candidate


class Command(BaseCommand):
    help = "Import traffic sign panels from Produits.txt"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            default="Produits.txt",
            help="Path to the TSV source file (default: Produits.txt next to manage.py)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing Category and Product rows before importing",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and count without writing to the database",
        )

    def handle(self, *args, **options):
        source = Path(options["file"])
        if not source.is_absolute():
            source = Path.cwd() / source
        if not source.exists():
            raise CommandError(f"File not found: {source}")

        dry_run = options["dry_run"]
        prefix = "[DRY RUN] " if dry_run else ""

        rows = []
        skipped_unparseable = 0
        with open(source, encoding="latin-1") as fh:
            for i, line in enumerate(fh):
                if i == 0:
                    continue  # header
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 2:
                    continue
                code = parts[0].strip()
                price_raw = parts[2].strip() if len(parts) > 2 else ""

                line_prefix = code.split("-")[0].upper()
                if line_prefix not in PANEL_PREFIXES:
                    continue

                m = _CODE_RE.match(code)
                if not m:
                    skipped_unparseable += 1
                    continue

                rows.append({
                    "code": code,
                    "price_raw": price_raw,
                    "line": m.group("line").upper(),
                    "sign_code": m.group("sign").upper(),
                    "size_str": m.group("size").upper(),
                    "cls": m.group("cls").upper() if m.group("cls") else None,
                })

        self.stdout.write(
            f"{prefix}Parsed {len(rows)} panel rows from {source.name}"
            + (f" ({skipped_unparseable} skipped — unparseable code)" if skipped_unparseable else "")
        )

        if options["clear"] and not dry_run:
            deleted_p = Product.objects.all().delete()[0]
            deleted_c = Category.objects.all().delete()[0]
            self.stdout.write(
                self.style.WARNING(f"Cleared {deleted_p} products and {deleted_c} categories.")
            )

        # --- categories: one per sign series ---
        series_set = {_get_series(r["sign_code"]) for r in rows}
        category_map: dict[str, Category] = {}

        for series in sorted(series_set):
            cat_name = SERIES_NAMES.get(series, f"Panneaux {series}")
            cat_slug = slugify(f"panneaux-{series.lower()}")
            if not dry_run:
                cat, created = Category.objects.update_or_create(
                    slug=cat_slug,
                    defaults={"name": cat_name},
                )
                category_map[series] = cat
                if created:
                    self.stdout.write(f"  Created category: {cat_name}")
            else:
                self.stdout.write(f"  {prefix}Category: {cat_name}")

        # --- products ---
        seen_slugs: set[str] = set()
        if not dry_run:
            seen_slugs = set(Product.objects.values_list("slug", flat=True))

        created_count = 0
        updated_count = 0
        no_price_count = 0

        for row in rows:
            price = _parse_price(row["price_raw"])
            if price is None:
                no_price_count += 1
                price = Decimal("0.00")

            series = _get_series(row["sign_code"])
            slug = _build_slug(
                row["line"], row["sign_code"], row["size_str"], row["cls"], seen_slugs
            )
            name = _build_name(row["sign_code"], row["size_str"], row["cls"])
            dimensions = _build_dimensions(row["size_str"])
            material = f"Classe {row['cls'].lstrip('CL')}" if row["cls"] else ""

            defaults = {
                "name": name,
                "sign_code": row["sign_code"],
                "price": price,
                "is_active": price > 0,
                "dimensions": dimensions,
                "material": material,
                "description": LINE_LABELS.get(row["line"], row["line"]),
            }

            if not dry_run:
                _, was_created = Product.objects.update_or_create(
                    slug=slug,
                    defaults={"category": category_map[series], **defaults},
                )
                if was_created:
                    created_count += 1
                else:
                    updated_count += 1

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n{prefix}Would import {len(rows)} panels across "
                    f"{len(series_set)} categories. "
                    f"{no_price_count} without price (would be inactive)."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nDone — {created_count} created, {updated_count} updated, "
                    f"{no_price_count} inactive (no price)."
                )
            )
