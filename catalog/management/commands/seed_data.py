from django.core.management.base import BaseCommand
from catalog.models import Category, Product


class Command(BaseCommand):
    help = "Seed the database with sample products for development"

    def handle(self, *args, **options):
        self.stdout.write("Seeding catalog data...")

        road, _ = Category.objects.get_or_create(
            slug="road-signs",
            defaults={"name": "Road Signs", "description": "Standard road signs for public roads"},
        )
        worksite, _ = Category.objects.get_or_create(
            slug="worksite-signs",
            defaults={"name": "Worksite Signs", "description": "Temporary signs for construction sites"},
        )
        info, _ = Category.objects.get_or_create(
            slug="information-signs",
            defaults={"name": "Information Signs", "description": "Informational and directional signs"},
        )

        products = [
            {
                "category": road, "name": "Stop Sign — B2a", "slug": "stop-sign-b2a",
                "price": "49.90", "dimensions": "Ø 900mm", "material": "Aluminium 1.5mm",
                "meta_title": "Stop Sign B2a — Buy Online",
                "meta_description": "Standard aluminium stop sign B2a, Ø 900mm. Ships in 3 working days.",
            },
            {
                "category": road, "name": "Give Way — AB3a", "slug": "give-way-ab3a",
                "price": "44.90", "dimensions": "Ø 700mm", "material": "Aluminium 1.5mm",
            },
            {
                "category": road, "name": "Speed Limit 30 — B14", "slug": "speed-limit-30-b14",
                "price": "39.90", "dimensions": "Ø 700mm", "material": "Aluminium 1.5mm",
            },
            {
                "category": road, "name": "Speed Limit 50 — B14", "slug": "speed-limit-50-b14",
                "price": "39.90", "dimensions": "Ø 700mm", "material": "Aluminium 1.5mm",
            },
            {
                "category": road, "name": "No Entry — B1", "slug": "no-entry-b1",
                "price": "54.90", "dimensions": "Ø 700mm", "material": "Aluminium 1.5mm",
            },
            {
                "category": worksite, "name": "Road Works Ahead — AK5", "slug": "road-works-ak5",
                "price": "59.90", "dimensions": "700x700mm", "material": "Aluminium 1.5mm",
            },
            {
                "category": worksite, "name": "Lane Closed — KC1", "slug": "lane-closed-kc1",
                "price": "64.90", "dimensions": "700x700mm", "material": "Aluminium 1.5mm",
            },
            {
                "category": info, "name": "Parking Sign — CE12", "slug": "parking-ce12",
                "price": "34.90", "dimensions": "500x700mm", "material": "Aluminium 1.5mm",
            },
        ]

        created = 0
        for data in products:
            _, was_created = Product.objects.get_or_create(slug=data["slug"], defaults=data)
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. {created} products created, {len(products) - created} already existed."
        ))
