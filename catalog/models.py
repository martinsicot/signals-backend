from django.db import models


class Classe(models.TextChoices):
    CL1 = "CL1", "Classe 1"
    CL2 = "CL2", "Classe 2"


class Backing(models.TextChoices):
    """RAL backing option — a purchasable choice affecting price."""
    ALU_BRUT = "alu_brut", "Dos alu brut"
    RAL = "ral", "Alu RAL au choix"


class Shape(models.TextChoices):
    TRIANGLE = "triangle", "Triangle"
    ROUND = "round", "Rond"
    SQUARE = "square", "Carré"
    OCTAGON = "octagon", "Octogone"
    DIAMOND = "diamond", "Losange"
    RECT = "rect", "Rectangle"
    DIRECTIONAL = "directional", "Directionnel"
    UNKNOWN = "unknown", "—"


class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Price grid — the source of truth for pricing.
# A price is keyed by (schedule, size, classe, backing), shared across every
# sign that maps to the schedule. Variants resolve their price from here.
# ---------------------------------------------------------------------------


class PriceSchedule(models.Model):
    """A distinct price matrix shared by many regulatory sign references."""

    SIZE_KIND_SINGLE = "single"
    SIZE_KIND_DIAMETER = "diameter"
    SIZE_KIND_RECT = "rect"
    SIZE_KIND_CHOICES = [
        (SIZE_KIND_SINGLE, "Single dimension"),
        (SIZE_KIND_DIAMETER, "Diameter"),
        (SIZE_KIND_RECT, "Width × Height"),
    ]

    code = models.CharField(max_length=50, unique=True, db_index=True)
    size_kind = models.CharField(max_length=20, choices=SIZE_KIND_CHOICES)
    label = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code


class PriceScheduleSize(models.Model):
    """One size line of a schedule, with the specs shared across its cells."""

    schedule = models.ForeignKey(PriceSchedule, on_delete=models.CASCADE, related_name="sizes")
    size_label = models.CharField(max_length=30)  # "500", "Ø450", "350x350"

    # Parsed dimensions (whichever apply to the schedule's size_kind).
    side_mm = models.PositiveIntegerField(null=True, blank=True)
    diameter_mm = models.PositiveIntegerField(null=True, blank=True)
    width_mm = models.PositiveIntegerField(null=True, blank=True)
    height_mm = models.PositiveIntegerField(null=True, blank=True)

    # Per-size specs (shared across CL1/CL2 and both backings).
    epaisseur_mm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    poids_kg = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    poids_note = models.CharField(max_length=50, blank=True)  # e.g. "Au sol"
    rails_mm = models.CharField(max_length=50, blank=True)  # e.g. "150/300"
    transport_dpd = models.CharField(max_length=100, blank=True)
    transport_palette = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = [("schedule", "size_label")]
        ordering = ["schedule", "id"]

    def __str__(self):
        return f"{self.schedule.code} · {self.size_label}"


class PriceCell(models.Model):
    """A single price point: (schedule size, classe, backing) → sale/cost."""

    schedule_size = models.ForeignKey(PriceScheduleSize, on_delete=models.CASCADE, related_name="cells")
    classe = models.CharField(max_length=3, choices=Classe.choices)
    backing = models.CharField(max_length=10, choices=Backing.choices)

    prix_vente_ht = models.DecimalField(max_digits=8, decimal_places=2)
    cout_achat_ht = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    delai = models.CharField(max_length=50, blank=True)  # fabrication lead time

    class Meta:
        unique_together = [("schedule_size", "classe", "backing")]
        ordering = ["schedule_size", "classe", "backing"]

    def __str__(self):
        return f"{self.schedule_size} · {self.classe} · {self.backing}"

    @property
    def marge_ht(self):
        if self.cout_achat_ht is None:
            return None
        return self.prix_vente_ht - self.cout_achat_ht


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------


class Product(models.Model):
    """One regulatory sign (e.g. A1a). Its variants are size × classe × backing."""

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    base_code = models.CharField(max_length=100, unique=True, db_index=True)  # regulatory ref
    name = models.CharField(max_length=300)
    slug = models.SlugField(max_length=120, unique=True)
    type = models.CharField(max_length=50, blank=True)
    shape = models.CharField(max_length=20, choices=Shape.choices, default=Shape.UNKNOWN)
    price_schedule = models.ForeignKey(
        PriceSchedule, on_delete=models.PROTECT, related_name="products", null=True, blank=True
    )
    is_quote = models.BooleanField(default=False)  # no online price → G* directional
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="products/", blank=True)
    is_active = models.BooleanField(default=True)
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Attribute(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = "Attribute"
        verbose_name_plural = "Attributes"
        ordering = ["name"]

    def __str__(self):
        return self.name


class AttributeValue(models.Model):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="values")
    value = models.CharField(max_length=100)
    display = models.CharField(max_length=200)
    slug = models.SlugField(max_length=120)

    class Meta:
        verbose_name = "Attribute Value"
        verbose_name_plural = "Attribute Values"
        unique_together = [("attribute", "value")]
        ordering = ["attribute", "value"]

    def __str__(self):
        return f"{self.attribute.name}: {self.display}"


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField(max_length=100, unique=True, db_index=True)

    # Structured pricing axes (source of truth for resolution).
    classe = models.CharField(max_length=3, choices=Classe.choices, blank=True)
    backing = models.CharField(max_length=10, choices=Backing.choices, blank=True)
    schedule_size = models.ForeignKey(
        PriceScheduleSize, on_delete=models.PROTECT, related_name="variants", null=True, blank=True
    )
    price_cell = models.ForeignKey(
        PriceCell, on_delete=models.SET_NULL, related_name="variants", null=True, blank=True
    )

    # Denormalized read cache (kept in sync with price_cell by the importer).
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)

    is_active = models.BooleanField(default=False)
    attributes = models.ManyToManyField(AttributeValue, through="ProductVariantAttribute")

    class Meta:
        verbose_name = "Product Variant"
        verbose_name_plural = "Product Variants"
        ordering = ["sku"]

    def __str__(self):
        return self.sku

    @property
    def display_name(self) -> str:
        parts = [self.product.name]
        for pva in (self.productvariantattribute_set
                    .select_related("attribute_value__attribute")
                    .order_by("attribute_value__attribute__name")):
            parts.append(pva.attribute_value.display)
        return " — ".join(parts)


class ProductVariantAttribute(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    attribute_value = models.ForeignKey(AttributeValue, on_delete=models.CASCADE)

    class Meta:
        unique_together = [("variant", "attribute_value")]
        db_table = "catalog_product_variant_attribute"
