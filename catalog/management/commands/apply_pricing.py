"""
Management command: apply prices from Excel pricing table to existing Product records.

Expected file: Excel (.xlsx) with the structure:
  Row 1 : title (skipped)
  Row 2 : group headers (skipped)
  Row 3 : sub-headers (skipped)
  Row 4 : column headers (skipped)
  Row 5+ : data rows

Column mapping (0-based):
  A (0) : sign codes, space-separated, may contain noise words ("B à mention :")
  B (1) : size  — int (500), "o450" (round Ø), "350x350" (rectangular)
  C (2) : prix vente H-1, Dos Alu Brut, Classe 1  → Product.price (Cl.1)
  D (3) : prix vente H-1, Dos Alu Brut, Classe 2  → Product.price (Cl.2)
  F (5) : poids (kg)                               → Product.weight_kg
  L (11): délai fabrication                         → Product.lead_time
  M (12): prix vente, Dos Alu RAL, Classe 1        → Product.price_ral (Cl.1)
  N (13): prix vente, Dos Alu RAL, Classe 2        → Product.price_ral (Cl.2)
  J (9) : coût d'achat, Dos Alu Brut, Classe 1    → Product.cost_price (Cl.1)
  K (10): coût d'achat, Dos Alu Brut, Classe 2    → Product.cost_price (Cl.2)
  O (14): coût d'achat, Dos Alu RAL, Classe 1     → Product.cost_price_ral (Cl.1)
  P (15): coût d'achat, Dos Alu RAL, Classe 2     → Product.cost_price_ral (Cl.2)

Sign codes from column A are grouped (one cell covers several rows with None).
The size column drives the per-row product match.

Options:
  --file PATH   path to the .xlsx file (required)
  --dry-run     report matches without updating the database
"""

import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

import openpyxl
from django.core.management.base import BaseCommand, CommandError

from catalog.models import Product


HEADER_ROWS = 4
DATA_START = HEADER_ROWS + 1  # row 5 (1-based)

# Columns (0-based)
COL_CODES = 0
COL_SIZE = 1
COL_PRICE_CL1 = 2
COL_PRICE_CL2 = 3
COL_WEIGHT = 5
COL_COST_CL1 = 9
COL_COST_CL2 = 10
COL_LEAD_TIME = 11
COL_RAL_CL1 = 12
COL_RAL_CL2 = 13
COL_COST_RAL_CL1 = 14
COL_COST_RAL_CL2 = 15

# Only tokens matching this pattern are treated as sign codes
_CODE_PATTERN = re.compile(r"^[A-Z]{1,3}\d", re.IGNORECASE)


def _parse_codes(raw: str) -> list[str]:
    return [t.upper() for t in raw.split() if _CODE_PATTERN.match(t)]


def _normalize_size(raw) -> str:
    """Convert Excel size to the format stored in Product.dimensions."""
    if raw is None:
        return ""
    s = str(raw).strip().lower()
    if s.startswith("o"):
        s = s[1:]  # strip diameter prefix  → "o450" → "450"
    if "x" in s:
        w, h = s.split("x", 1)
        return f"{w.strip()}×{h.strip()} mm"
    try:
        return f"{int(float(s))} mm"
    except ValueError:
        return f"{s} mm"


def _to_decimal(val) -> Decimal | None:
    if val is None:
        return None
    try:
        return Decimal(str(val)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError):
        return None


def _to_str(val) -> str:
    if val is None:
        return ""
    return str(val).strip()


class Command(BaseCommand):
    help = "Apply prices from Excel pricing table to existing Product records"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            required=True,
            help="Path to the .xlsx pricing file",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report matches without writing to the database",
        )

    def handle(self, *args, **options):
        source = Path(options["file"])
        if not source.exists():
            raise CommandError(f"File not found: {source}")

        dry_run = options["dry_run"]
        tag = "[DRY RUN] " if dry_run else ""

        wb = openpyxl.load_workbook(source, data_only=True)
        ws = wb.active

        # --- parse Excel into groups ---
        groups: list[dict] = []
        current_codes: list[str] = []
        current_weight: Decimal | None = None
        current_lead_time: str = ""

        for row in ws.iter_rows(min_row=DATA_START, values_only=True):
            if all(v is None for v in row):
                continue

            raw_codes = row[COL_CODES]
            if raw_codes:
                current_codes = _parse_codes(str(raw_codes))
                current_weight = _to_decimal(row[COL_WEIGHT])
                current_lead_time = _to_str(row[COL_LEAD_TIME])

            if not current_codes:
                continue

            size_str = _normalize_size(row[COL_SIZE])
            if not size_str:
                continue

            groups.append({
                "codes": current_codes,
                "size": size_str,
                "weight": current_weight,
                "lead_time": current_lead_time,
                "price_cl1": _to_decimal(row[COL_PRICE_CL1]),
                "price_cl2": _to_decimal(row[COL_PRICE_CL2]),
                "cost_cl1": _to_decimal(row[COL_COST_CL1]),
                "cost_cl2": _to_decimal(row[COL_COST_CL2]),
                "ral_cl1": _to_decimal(row[COL_RAL_CL1]),
                "ral_cl2": _to_decimal(row[COL_RAL_CL2]),
                "cost_ral_cl1": _to_decimal(row[COL_COST_RAL_CL1]),
                "cost_ral_cl2": _to_decimal(row[COL_COST_RAL_CL2]),
            })

        self.stdout.write(f"{tag}Parsed {len(groups)} price rows from {source.name}")

        # --- apply to Products ---
        updated = 0
        not_found_codes: set[str] = set()

        for g in groups:
            for cls_label, price, cost, ral, cost_ral in [
                ("Classe 1", g["price_cl1"], g["cost_cl1"], g["ral_cl1"], g["cost_ral_cl1"]),
                ("Classe 2", g["price_cl2"], g["cost_cl2"], g["ral_cl2"], g["cost_ral_cl2"]),
            ]:
                qs = Product.objects.filter(
                    sign_code__in=g["codes"],
                    dimensions=g["size"],
                    material=cls_label,
                )

                if not qs.exists():
                    # track unmatched codes silently; report at the end
                    for c in g["codes"]:
                        not_found_codes.add(f"{c} / {g['size']} / {cls_label}")
                    continue

                if not dry_run:
                    fields: dict = {}
                    if price is not None:
                        fields["price"] = price
                        fields["is_active"] = True
                    if cost is not None:
                        fields["cost_price"] = cost
                    if ral is not None:
                        fields["price_ral"] = ral
                    if cost_ral is not None:
                        fields["cost_price_ral"] = cost_ral
                    if g["weight"] is not None:
                        fields["weight_kg"] = g["weight"]
                    if g["lead_time"]:
                        fields["lead_time"] = g["lead_time"]

                    if fields:
                        qs.update(**fields)
                        updated += qs.count()

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"\n{tag}Would update products (run without --dry-run to apply)."))
        else:
            self.stdout.write(self.style.SUCCESS(f"\nDone — {updated} product records updated."))

        if not_found_codes:
            self.stdout.write(
                self.style.WARNING(
                    f"\n{len(not_found_codes)} code/size/class combos had no matching product "
                    f"(Excel references signs not in Produits.txt)."
                )
            )
