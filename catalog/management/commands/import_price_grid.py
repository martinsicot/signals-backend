"""
Management command: import the permanent-signage catalog from the price grid.

Source: data/price_grid_permanent.json (built by scripts/build_price_grid.py).

The grid is the source of truth for pricing. This command:
  1. upserts PriceSchedule / PriceScheduleSize / PriceCell,
  2. creates one Product per priced sign reference (quote-only refs become
     is_quote products with no variants),
  3. expands each product into variants = sizes × classe × backing,
  4. syncs each variant's cached `price` from its PriceCell.prix_vente_ht.

NOTE: cout_achat_ht (buying price) lives only on PriceCell and must never be
exposed through a public serializer.

Options:
  --file PATH   override JSON source (default: data/price_grid_permanent.json)
  --clear       delete all existing catalog + price-grid data before importing
  --dry-run     parse and report counts without writing to the DB
"""

import json
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from catalog.models import (
    Attribute,
    AttributeValue,
    Backing,
    Category,
    Classe,
    PriceCell,
    PriceSchedule,
    PriceScheduleSize,
    Product,
    ProductVariant,
    ProductVariantAttribute,
)

PREFIX_CATEGORIES = {
    "A": ("Danger", "danger"),
    "B": ("Prescription", "prescription"),
    "C": ("Obligation", "obligation"),
    "D": ("Direction", "direction"),
    "E": ("Localisation", "localisation"),
    "F": ("Divers", "divers"),
    "G": ("Grands axes", "grands-axes"),
}
BATCH_SIZE = 1000


def _dec(v):
    return None if v is None else Decimal(str(v))


def _sku_size(label: str) -> str:
    return label.replace("Ø", "D").replace("×", "x").replace(" ", "")


class Command(BaseCommand):
    help = "Import the permanent-signage catalog from data/price_grid_permanent.json"

    def add_arguments(self, parser):
        parser.add_argument("--file", default="data/price_grid_permanent.json")
        parser.add_argument("--clear", action="store_true")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        source = Path(options["file"])
        if not source.exists():
            raise CommandError(f"File not found: {source}")

        with open(source, encoding="utf-8") as fh:
            data = json.load(fh)

        schedules = data["price_schedules"]
        refs = data["sign_references"]
        priced_refs = [r for r in refs if r.get("schedule")]
        quote_refs = [r for r in refs if not r.get("schedule")]

        # Projected variant count = for each priced ref, its schedule's cell count.
        cells_per_schedule = {
            s["code"]: sum(
                1
                for row in s["rows"]
                for b in row["prices"].values()
                for c in b.values()
                if c["vente"] is not None
            )
            for s in schedules
        }
        projected_variants = sum(cells_per_schedule[r["schedule"]] for r in priced_refs)

        if options["dry_run"]:
            self.stdout.write(self.style.SUCCESS(
                f"[DRY RUN] Would create:\n"
                f"  {len(schedules)} price schedules\n"
                f"  {len(priced_refs)} priced products + {len(quote_refs)} quote products\n"
                f"  ~{projected_variants} variants"
            ))
            return

        with transaction.atomic():
            if options["clear"]:
                ProductVariantAttribute.objects.all().delete()
                ProductVariant.objects.all().delete()
                Product.objects.all().delete()
                PriceCell.objects.all().delete()
                PriceScheduleSize.objects.all().delete()
                PriceSchedule.objects.all().delete()
                AttributeValue.objects.all().delete()
                Attribute.objects.all().delete()
                Category.objects.all().delete()
                self.stdout.write(self.style.WARNING("Cleared catalog + price-grid data."))

            category_objs: dict[str, Category] = {}
            for prefix, (name, slug) in PREFIX_CATEGORIES.items():
                cat, _ = Category.objects.get_or_create(slug=slug, defaults={"name": name})
                category_objs[prefix] = cat

            # --- 1. price grid ---
            schedule_objs: dict[str, PriceSchedule] = {}
            # (schedule_code, size_label) -> PriceScheduleSize
            size_objs: dict[tuple[str, str], PriceScheduleSize] = {}
            # (schedule_code, size_label, classe, backing) -> PriceCell
            cell_objs: dict[tuple, PriceCell] = {}

            for s in schedules:
                ps, _ = PriceSchedule.objects.update_or_create(
                    code=s["code"],
                    defaults={"size_kind": s["size_kind"], "label": s.get("label", "")},
                )
                schedule_objs[s["code"]] = ps

                for row in s["rows"]:
                    dims = row["dimensions"]
                    poids = row["specs"].get("poids_kg")
                    poids_kg = _dec(poids) if isinstance(poids, (int, float)) else None
                    poids_note = poids if isinstance(poids, str) else ""
                    pss, _ = PriceScheduleSize.objects.update_or_create(
                        schedule=ps,
                        size_label=row["size"],
                        defaults={
                            "side_mm": dims.get("value_mm"),
                            "diameter_mm": dims.get("diameter_mm"),
                            "width_mm": dims.get("width_mm"),
                            "height_mm": dims.get("height_mm"),
                            "epaisseur_mm": _dec(row["specs"].get("epaisseur_mm")),
                            "poids_kg": poids_kg,
                            "poids_note": poids_note,
                            "rails_mm": row["specs"].get("rails_mm") or "",
                            "transport_dpd": row["specs"].get("transport_dpd") or "",
                            "transport_palette": row["specs"].get("transport_palette") or "",
                        },
                    )
                    size_objs[(s["code"], row["size"])] = pss

                    for backing, by_class in row["prices"].items():
                        delai = row["specs"].get(f"delai_{backing}") or ""
                        for classe, cell in by_class.items():
                            if cell["vente"] is None:
                                continue
                            pc, _ = PriceCell.objects.update_or_create(
                                schedule_size=pss,
                                classe=classe,
                                backing=backing,
                                defaults={
                                    "prix_vente_ht": _dec(cell["vente"]),
                                    "cout_achat_ht": _dec(cell.get("achat")),
                                    "delai": delai,
                                },
                            )
                            cell_objs[(s["code"], row["size"], classe, backing)] = pc

            # --- 2. attributes (display layer) ---
            attr_taille, _ = Attribute.objects.get_or_create(slug="taille", defaults={"name": "Taille"})
            attr_classe, _ = Attribute.objects.get_or_create(slug="classe", defaults={"name": "Classe"})
            attr_backing, _ = Attribute.objects.get_or_create(slug="backing", defaults={"name": "Dos / RAL"})
            av_cache: dict[tuple, AttributeValue] = {}

            def get_av(attr, value, display, slug):
                key = (attr.id, value)
                if key not in av_cache:
                    av, _ = AttributeValue.objects.get_or_create(
                        attribute=attr, value=value,
                        defaults={"display": display, "slug": slug},
                    )
                    av_cache[key] = av
                return av_cache[key]

            classe_labels = dict(Classe.choices)
            backing_labels = dict(Backing.choices)

            # --- 3. products + variants ---
            seen_slugs: set[str] = set()
            created_products = created_variants = 0
            pva_batch: list[ProductVariantAttribute] = []

            def flush_pva():
                if pva_batch:
                    ProductVariantAttribute.objects.bulk_create(pva_batch, ignore_conflicts=True)
                    pva_batch.clear()

            def uniq_slug(base):
                base = slugify(base)[:120] or "panneau"
                slug, n = base, 2
                while slug in seen_slugs:
                    slug = f"{base[:116]}-{n}"
                    n += 1
                seen_slugs.add(slug)
                return slug

            for r in refs:
                ref = r["ref"]
                is_quote = not r.get("schedule")
                prefix = ref[0].upper()
                product, p_created = Product.objects.update_or_create(
                    base_code=ref,
                    defaults={
                        "name": f"Panneau {ref}",
                        "slug": uniq_slug(f"panneau-{ref}"),
                        "shape": r.get("shape", "unknown"),
                        "price_schedule": None if is_quote else schedule_objs[r["schedule"]],
                        "is_quote": is_quote,
                        "type": "quote" if is_quote else "fixed",
                        "is_active": True,
                    },
                )
                if prefix in category_objs:
                    product.categories.set([category_objs[prefix]])
                created_products += int(p_created)
                if is_quote:
                    continue

                for row in [row for s in schedules if s["code"] == r["schedule"] for row in s["rows"]]:
                    size_label = row["size"]
                    pss = size_objs[(r["schedule"], size_label)]
                    for backing in row["prices"]:
                        for classe in row["prices"][backing]:
                            pc = cell_objs.get((r["schedule"], size_label, classe, backing))
                            if pc is None:
                                continue
                            sku = f"{ref}-{_sku_size(size_label)}-{classe}-{backing}"
                            variant, v_created = ProductVariant.objects.update_or_create(
                                sku=sku,
                                defaults={
                                    "product": product,
                                    "classe": classe,
                                    "backing": backing,
                                    "schedule_size": pss,
                                    "price_cell": pc,
                                    "price": pc.prix_vente_ht,
                                    "weight_kg": pss.poids_kg,
                                    "is_active": True,
                                },
                            )
                            created_variants += int(v_created)

                            for av in (
                                get_av(attr_taille, size_label, size_label, slugify(_sku_size(size_label))),
                                get_av(attr_classe, classe, classe_labels[classe], slugify(classe)),
                                get_av(attr_backing, backing, backing_labels[backing], slugify(backing)),
                            ):
                                pva_batch.append(ProductVariantAttribute(variant=variant, attribute_value=av))
                                if len(pva_batch) >= BATCH_SIZE:
                                    flush_pva()

            flush_pva()

        self.stdout.write(self.style.SUCCESS(
            f"\nDone.\n"
            f"  {PriceSchedule.objects.count()} price schedules, "
            f"{PriceCell.objects.count()} price cells\n"
            f"  {Product.objects.count()} products ({Product.objects.filter(is_quote=True).count()} quote)\n"
            f"  {ProductVariant.objects.count()} variants"
        ))
