"""
Management command: import product catalog from data/produits.json.

Each JSON entry is a product family (base_code). Its `declinaisons` are the
purchasable variants and map to ProductVariant rows. Attributes (Taille, Classe,
Finition, Fixations) are extracted from each déclinaison and linked via
ProductVariantAttribute.

Options:
  --file PATH   override JSON source (default: data/produits.json)
  --clear       delete all existing data before importing
  --dry-run     parse and report counts without writing to DB
"""

import json
import re
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from catalog.models import (
    Attribute,
    AttributeValue,
    Category,
    Product,
    ProductVariant,
    ProductVariantAttribute,
)

FINITION_DISPLAY = {
    "ACIER": "Acier",
    "ALU": "Aluminium",
    "BRUT": "Brut",
    "FEZN": "FeZn",
    "GALVA": "Galvanisé",
    "GALVANF": "Galvanisé NF",
    "INOX": "Inox",
    "LAQUE": "Laqué",
    "LED": "LED",
    "PEINTURE": "Peinture",
    "SENDZIMIR": "Sendzimir",
    "SOLAR": "Solaire",
}

CLASSE_DISPLAY = {
    "CL1": "Classe 1",
    "CL2": "Classe 2",
    "CL3": "Classe 3",
}

MAX_SLUG = 120
BATCH_SIZE = 500


def _slug(raw: str, seen: set, max_len: int = MAX_SLUG) -> str:
    base = slugify(re.sub(r"['\"/]", "-", raw))[:max_len]
    if not base:
        base = "item"
    candidate = base
    counter = 2
    while candidate in seen:
        suffix = f"-{counter}"
        candidate = base[: max_len - len(suffix)] + suffix
        counter += 1
    seen.add(candidate)
    return candidate


def _taille(decl: dict) -> tuple[str, str, str] | None:
    """Returns (value, display, slug) for the Taille attribute, or None."""
    h = decl.get("hauteur_mm")
    w = decl.get("largeur_mm")
    d = decl.get("diametre_mm")
    dim = decl.get("dimension_mm")

    if h and w:
        val = f"{w}x{h}"
        return val, f"{w}×{h} mm", slugify(val)
    if d:
        return f"o{d}", f"Ø{d} mm", f"diam-{d}"
    if dim:
        return str(dim), f"{dim} mm", slugify(str(dim))
    return None


class Command(BaseCommand):
    help = "Import product catalog from data/produits.json"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            default="data/produits.json",
            help="Path to the JSON source file (default: data/produits.json)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing catalog data before importing",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and count without writing to the database",
        )

    def handle(self, *args, **options):
        source = Path(options["file"])
        if not source.exists():
            raise CommandError(f"File not found: {source}")

        dry_run = options["dry_run"]
        prefix = "[DRY RUN] " if dry_run else ""

        with open(source, encoding="utf-8") as fh:
            data = json.load(fh)

        self.stdout.write(f"{prefix}Loaded {len(data)} product families from {source}")

        if options["clear"] and not dry_run:
            ProductVariantAttribute.objects.all().delete()
            ProductVariant.objects.all().delete()
            Product.objects.all().delete()
            Category.objects.all().delete()
            AttributeValue.objects.all().delete()
            Attribute.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared all catalog data."))

        if dry_run:
            total_decl = sum(len(f.get("declinaisons", [])) for f in data)
            no_price = sum(
                1 for f in data
                for d in f.get("declinaisons", [])
                if d.get("prix") is None
            )
            gammes = {f["gamme"] for f in data}
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n{prefix}Would create:\n"
                    f"  {len(gammes)} categories\n"
                    f"  {len(data)} products\n"
                    f"  {total_decl} variants ({no_price} inactive — no price)\n"
                    f"  4 attributes"
                )
            )
            return

        # --- seed attributes ---
        attr_taille, _ = Attribute.objects.get_or_create(slug="taille", defaults={"name": "Taille"})
        attr_classe, _ = Attribute.objects.get_or_create(slug="classe", defaults={"name": "Classe"})
        attr_finition, _ = Attribute.objects.get_or_create(slug="finition", defaults={"name": "Finition"})
        attr_fixations, _ = Attribute.objects.get_or_create(slug="fixations", defaults={"name": "Fixations"})

        # cache for AttributeValue: (attribute_id, value) → AttributeValue
        av_cache: dict[tuple, AttributeValue] = {}

        def get_or_create_av(attr: Attribute, value: str, display: str, slug: str) -> AttributeValue:
            key = (attr.id, value)
            if key not in av_cache:
                av, _ = AttributeValue.objects.get_or_create(
                    attribute=attr,
                    value=value,
                    defaults={"display": display, "slug": slug},
                )
                av_cache[key] = av
            return av_cache[key]

        # --- import ---
        seen_product_slugs: set[str] = set(Product.objects.values_list("slug", flat=True))
        created_products = 0
        created_variants = 0
        skipped_variants = 0
        no_price_count = 0

        pva_batch: list[ProductVariantAttribute] = []

        def flush_pva():
            if pva_batch:
                ProductVariantAttribute.objects.bulk_create(pva_batch, ignore_conflicts=True)
                pva_batch.clear()

        for family in data:
            with transaction.atomic():
                gamme = family["gamme"]
                base_code = family["base_code"]
                declinaisons = family.get("declinaisons", [])

                cat_slug = slugify(gamme)
                category, _ = Category.objects.get_or_create(
                    slug=cat_slug,
                    defaults={"name": gamme},
                )

                has_any_price = any(d.get("prix") is not None for d in declinaisons)
                product_slug = _slug(base_code, seen_product_slugs)

                product, p_created = Product.objects.update_or_create(
                    base_code=base_code,
                    defaults={
                        "name": family["libelle"],
                        "slug": product_slug,
                        "type": family.get("type", ""),
                        "category": category,
                        "is_active": has_any_price,
                    },
                )
                if p_created:
                    created_products += 1

                for decl in declinaisons:
                    sku = decl["code"]
                    prix = decl.get("prix")
                    has_price = prix is not None
                    if not has_price:
                        no_price_count += 1

                    variant, v_created = ProductVariant.objects.update_or_create(
                        sku=sku,
                        defaults={
                            "product": product,
                            "price": Decimal(str(prix)) if has_price else None,
                            "weight_kg": decl.get("poids_kg"),
                            "is_active": has_price,
                        },
                    )
                    if v_created:
                        created_variants += 1
                    else:
                        skipped_variants += 1

                    av_list: list[AttributeValue] = []

                    taille = _taille(decl)
                    if taille:
                        av_list.append(get_or_create_av(attr_taille, *taille))

                    classe = decl.get("classe")
                    if classe:
                        av_list.append(get_or_create_av(
                            attr_classe,
                            classe,
                            CLASSE_DISPLAY.get(classe.upper(), classe),
                            slugify(classe),
                        ))

                    for fin in decl.get("finitions") or []:
                        av_list.append(get_or_create_av(
                            attr_finition,
                            fin,
                            FINITION_DISPLAY.get(fin, fin.title()),
                            fin.lower(),
                        ))

                    if "fixations" in decl:
                        val = "true" if decl["fixations"] else "false"
                        display = "Avec fixations" if decl["fixations"] else "Sans fixation"
                        slug = "avec-fixations" if decl["fixations"] else "sans-fixation"
                        av_list.append(get_or_create_av(attr_fixations, val, display, slug))

                    for av in av_list:
                        pva_batch.append(ProductVariantAttribute(variant=variant, attribute_value=av))
                        if len(pva_batch) >= BATCH_SIZE:
                            flush_pva()

        flush_pva()

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone.\n"
                f"  {created_products} products created, "
                f"{len(data) - created_products} updated\n"
                f"  {created_variants} variants created, "
                f"{skipped_variants} updated\n"
                f"  {no_price_count} variants inactive (no price)\n"
                f"  {AttributeValue.objects.count()} attribute values"
            )
        )
